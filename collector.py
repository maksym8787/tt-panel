import re
import subprocess
import time
import traceback
import urllib.request

from config import (
    METRICS_URL, COLLECT_INTERVAL, LOG_FILE,
    _shutdown_event, logger,
)
from database import get_db, cleanup_old_data
from network import rdns_lookup
from auth import cleanup_stale_rate_limits

_prev_metrics = None


def parse_prometheus_metrics(text: str) -> dict:
    data = {}
    for line in text.strip().splitlines():
        if line.startswith("#"):
            continue
        match = re.match(r'(\w+)(?:\{[^}]*\})?\s+([\d.eE+-]+)', line)
        if match:
            key, val = match.group(1), match.group(2)
            try:
                data[key] = float(val) if '.' in val or 'e' in val.lower() else int(val)
            except ValueError:
                pass
    return data


def fetch_live_metrics() -> dict:
    try:
        req = urllib.request.urlopen(METRICS_URL, timeout=5)
        text = req.read().decode()
        return parse_prometheus_metrics(text)
    except Exception:
        return {}


def collect_metrics():
    global _prev_metrics
    m = fetch_live_metrics()
    if not m:
        return
    now = int(time.time())
    cur_in = m.get("inbound_traffic_bytes", 0)
    cur_out = m.get("outbound_traffic_bytes", 0)
    if _prev_metrics is None:
        _prev_metrics = {"in": cur_in, "out": cur_out}
        delta_in = 0
        delta_out = 0
    else:
        delta_in = max(0, cur_in - _prev_metrics["in"]) if cur_in >= _prev_metrics["in"] else cur_in
        delta_out = max(0, cur_out - _prev_metrics["out"]) if cur_out >= _prev_metrics["out"] else cur_out
        _prev_metrics = {"in": cur_in, "out": cur_out}
    with get_db() as conn:
        conn.execute("PRAGMA busy_timeout=5000")
        c = conn.cursor()
        c.execute("""INSERT INTO metrics_snapshots
            (ts, sessions, inbound_bytes, outbound_bytes, tcp_sockets, udp_sockets, cpu_seconds, memory_bytes, open_fds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (now, m.get("client_sessions", 0), cur_in, cur_out,
             m.get("outbound_tcp_sockets", 0), m.get("outbound_udp_sockets", 0),
             m.get("process_cpu_seconds_total", 0),
             m.get("process_resident_memory_bytes", 0), m.get("process_open_fds", 0)))
        hour_ts = now - (now % 3600)
        c.execute("SELECT id, inbound_bytes, outbound_bytes, sessions_max, connections_count FROM traffic_hourly WHERE hour_ts = ?", (hour_ts,))
        row = c.fetchone()
        if row:
            new_max = max(row[3], m.get("client_sessions", 0))
            c.execute("UPDATE traffic_hourly SET inbound_bytes=inbound_bytes+?, outbound_bytes=outbound_bytes+?, sessions_max=?, connections_count=connections_count+1 WHERE id=?",
                (delta_in, delta_out, new_max, row[0]))
        else:
            c.execute("INSERT INTO traffic_hourly (hour_ts, inbound_bytes, outbound_bytes, sessions_max, connections_count) VALUES (?, ?, ?, ?, ?)",
                (hour_ts, delta_in, delta_out, m.get("client_sessions", 0), 1))
        conn.commit()


def _load_last_log_pos() -> int:
    try:
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            row = conn.execute("SELECT value FROM meta WHERE key='last_log_pos'").fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return 0


def _save_last_log_pos(pos: int):
    try:
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('last_log_pos', ?)", (str(pos),))
            conn.commit()
    except Exception:
        logger.warning("Failed to save last_log_pos")


_last_log_pos = 0


def _parse_log_lines(lines: list):
    if not lines:
        return
    with get_db() as conn:
        conn.execute("PRAGMA busy_timeout=5000")
        c = conn.cursor()
        now = int(time.time())
        for line in lines:
            m = re.search(r'client_address:\s*([\d.]+).*?destination:\s*Address\(([^)]+)\).*?user_agent:\s*Some\("([^"]+)"\)', line)
            if m:
                dst = rdns_lookup(m.group(2))
                c.execute("INSERT INTO connections (ts, client_ip, destination, user_agent, event) VALUES (?, ?, ?, ?, ?)",
                    (now, m.group(1), dst, m.group(3), "connect"))
                continue
            if "tunnel closed gracefully" in line.lower() or "tunnel stopped gracefully" in line.lower():
                cid_m = re.search(r'\[CLIENT=(\d+)', line)
                cid = cid_m.group(1) if cid_m else None
                c.execute("INSERT INTO connections (ts, protocol, event) VALUES (?, ?, ?)", (now, cid, "disconnect"))
                continue
        conn.commit()


def parse_new_log_entries():
    global _last_log_pos
    new_lines = []
    if LOG_FILE.exists():
        try:
            fsize = LOG_FILE.stat().st_size
            if fsize < _last_log_pos:
                _last_log_pos = 0
            if fsize > _last_log_pos:
                with open(LOG_FILE, 'r') as f:
                    f.seek(_last_log_pos)
                    new_lines = f.readlines()
                    _last_log_pos = f.tell()
                _save_last_log_pos(_last_log_pos)
        except Exception:
            logger.error("Log file read error:\n%s", traceback.format_exc())

    if not new_lines:
        try:
            since_sec = max(COLLECT_INTERVAL + 10, 120)
            r = subprocess.run(
                ["journalctl", "-u", "trusttunnel", "--no-pager", "-q",
                 "--since", f"{since_sec} seconds ago"],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0 and r.stdout.strip():
                new_lines = r.stdout.strip().splitlines()
        except Exception:
            pass

    try:
        _parse_log_lines(new_lines)
    except Exception:
        logger.error("Log parse error:\n%s", traceback.format_exc())


def collector_loop():
    global _last_log_pos
    from services import auto_renew_cert_if_needed

    _last_log_pos = _load_last_log_pos()
    while not _shutdown_event.is_set():
        try:
            collect_metrics()
            parse_new_log_entries()
            if int(time.time()) % 3600 < COLLECT_INTERVAL:
                cleanup_old_data()
            cleanup_stale_rate_limits()
            auto_renew_cert_if_needed()
        except Exception:
            logger.error("Collector error:\n%s", traceback.format_exc())
        _shutdown_event.wait(timeout=COLLECT_INTERVAL)
