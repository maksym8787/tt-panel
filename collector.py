import json
import re
import subprocess
import time
import traceback
import urllib.error
import urllib.request

from config import (
    METRICS_URL, CLIENTS_URL, COLLECT_INTERVAL, LOG_FILE,
    _shutdown_event, logger,
)
from database import get_db, cleanup_old_data
from network import rdns_lookup
from auth import cleanup_stale_rate_limits, cleanup_expired_sessions

_prev_metrics = None


def parse_prometheus_metrics(text: str) -> dict:
    """Collapse a Prometheus exposition into {metric_name: total}.

    The endpoint splits several metrics by label, e.g.
        client_sessions{protocol_type="HTTP1"} 0
        client_sessions{protocol_type="HTTP2"} 2
    Assigning instead of accumulating kept only the last series, so sessions and
    traffic were undercounted whenever clients used more than one protocol.
    """
    data = {}
    for line in text.strip().splitlines():
        if line.startswith("#"):
            continue
        match = re.match(r'(\w+)(?:\{[^}]*\})?\s+([\d.eE+-]+)', line)
        if not match:
            continue
        key, val = match.group(1), match.group(2)
        try:
            num = float(val) if '.' in val or 'e' in val.lower() else int(val)
        except ValueError:
            continue
        data[key] = data.get(key, 0) + num
    return data


def fetch_live_metrics() -> dict:
    try:
        with urllib.request.urlopen(METRICS_URL, timeout=5) as resp:
            return parse_prometheus_metrics(resp.read().decode())
    except Exception:
        return {}


_prev_clients = {}
# None = not probed yet, True/False = whether the endpoint exposes /clients.
_clients_available = None


def fetch_client_stats():
    """GET /clients. Returns a list, or None when the feature is unavailable."""
    global _clients_available
    req = urllib.request.Request(CLIENTS_URL, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # per_client_metrics is off, or the endpoint predates 1.1.0.
            if _clients_available is not False:
                logger.info(
                    "Per-user metrics unavailable (%s returned 404). Enable "
                    "[metrics] per_client_metrics on endpoint 1.1.0+ to use them.",
                    CLIENTS_URL)
            _clients_available = False
        else:
            logger.warning("/clients returned HTTP %s", e.code)
        return None
    except Exception:
        return None

    if not isinstance(data, list):
        logger.warning("/clients did not return a JSON array")
        return None
    if _clients_available is not True:
        logger.info("Per-user metrics available: tracking %d client(s)", len(data))
    _clients_available = True
    return data


def clients_available():
    return _clients_available


def collect_client_usage():
    """Turn /clients lifetime counters into hourly per-user deltas."""
    global _prev_clients
    clients = fetch_client_stats()
    if clients is None:
        return

    now = int(time.time())
    hour_ts = now - (now % 3600)
    rows = []
    seen = {}
    for entry in clients:
        if not isinstance(entry, dict):
            continue
        username = entry.get("username")
        if not username:
            continue
        cur_in = int(entry.get("inbound") or 0)
        cur_out = int(entry.get("outbound") or 0)
        sessions = int(entry.get("sessions") or 0)
        ip = entry.get("ip") or None
        seen[username] = (cur_in, cur_out)

        prev = _prev_clients.get(username)
        if prev is None:
            # First sample establishes the baseline; no delta to record yet.
            d_in = d_out = 0
        else:
            # Counters reset when the endpoint restarts: treat the current
            # value as the delta rather than clamping a negative to zero.
            d_in = cur_in - prev[0] if cur_in >= prev[0] else cur_in
            d_out = cur_out - prev[1] if cur_out >= prev[1] else cur_out
        rows.append((hour_ts, username, d_in, d_out, sessions, ip, now if sessions else 0))

    _prev_clients = seen
    if not rows:
        return

    with get_db() as conn:
        conn.execute("PRAGMA busy_timeout=5000")
        c = conn.cursor()
        for hts, username, d_in, d_out, sessions, ip, last_seen in rows:
            c.execute("""
                INSERT INTO client_usage_hourly
                    (hour_ts, username, inbound_bytes, outbound_bytes, sessions_max, last_ip, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(hour_ts, username) DO UPDATE SET
                    inbound_bytes = inbound_bytes + excluded.inbound_bytes,
                    outbound_bytes = outbound_bytes + excluded.outbound_bytes,
                    sessions_max = MAX(sessions_max, excluded.sessions_max),
                    last_ip = COALESCE(excluded.last_ip, last_ip),
                    last_seen = MAX(last_seen, excluded.last_seen)
            """, (hts, username, d_in, d_out, sessions, ip, last_seen))
        conn.commit()


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


_CONNECT_RE = re.compile(
    r'client_address:\s*([\d.]+).*?destination:\s*Address\(([^)]+)\).*?user_agent:\s*Some\("([^"]+)"\)')
_CLIENT_ID_RE = re.compile(r'\[CLIENT=(\d+)')


def _parse_log_lines(lines: list):
    if not lines:
        return
    now = int(time.time())
    connects = []
    disconnects = []
    for line in lines:
        m = _CONNECT_RE.search(line)
        if m:
            connects.append((m.group(1), m.group(2), m.group(3)))
            continue
        low = line.lower()
        if "tunnel closed gracefully" in low or "tunnel stopped gracefully" in low:
            cid_m = _CLIENT_ID_RE.search(line)
            disconnects.append(cid_m.group(1) if cid_m else None)

    if not connects and not disconnects:
        return

    # Reverse DNS can block for up to a second per address; resolve before opening
    # the write transaction so the collector never holds the DB lock on the network.
    rows = [(now, ip, rdns_lookup(dst), ua, "connect") for ip, dst, ua in connects]

    with get_db() as conn:
        conn.execute("PRAGMA busy_timeout=5000")
        c = conn.cursor()
        if rows:
            c.executemany(
                "INSERT INTO connections (ts, client_ip, destination, user_agent, event) VALUES (?, ?, ?, ?, ?)",
                rows)
        if disconnects:
            c.executemany(
                "INSERT INTO connections (ts, client_id, event) VALUES (?, ?, ?)",
                [(now, cid, "disconnect") for cid in disconnects])
        conn.commit()


def _meta_get(key, default=None):
    try:
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            return row[0] if row else default
    except Exception:
        return default


def _meta_set(key, value):
    try:
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()
    except Exception:
        logger.warning("Failed to persist meta key %s", key)


def _read_journal_since_cursor():
    """Read journald entries exactly once.

    A `--since N seconds ago` window overlaps between cycles and double-counts
    connections; a saved cursor resumes precisely where the last read stopped.
    """
    cursor = _meta_get("journal_cursor")
    cmd = ["journalctl", "-u", "trusttunnel", "--no-pager", "-q", "--show-cursor", "-o", "short"]
    if cursor:
        cmd += ["--after-cursor", cursor]
    else:
        cmd += ["--since", "%d seconds ago" % COLLECT_INTERVAL]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except Exception:
        return []
    if r.returncode != 0 or not r.stdout.strip():
        return []
    lines = r.stdout.splitlines()
    out = []
    for line in lines:
        # journalctl prints the new cursor as a trailing "-- cursor: s=..." line
        if line.startswith("-- cursor:"):
            _meta_set("journal_cursor", line.split(":", 1)[1].strip())
            continue
        if line.startswith("-- "):
            continue
        out.append(line)
    return out


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
        new_lines = _read_journal_since_cursor()

    try:
        _parse_log_lines(new_lines)
    except Exception:
        logger.error("Log parse error:\n%s", traceback.format_exc())


_last_session_cleanup = 0.0


def collector_loop():
    global _last_log_pos, _last_session_cleanup
    from services import auto_renew_cert_if_needed, backfill_created_at

    _last_log_pos = _load_last_log_pos()
    try:
        backfill_created_at()
    except Exception:
        logger.error("created_at backfill failed:\n%s", traceback.format_exc())

    while not _shutdown_event.is_set():
        try:
            collect_metrics()
            collect_client_usage()
            parse_new_log_entries()
            if int(time.time()) % 3600 < COLLECT_INTERVAL:
                cleanup_old_data()
            cleanup_stale_rate_limits()
            # Session expiry is reaped here so request handlers stay read-only.
            if time.time() - _last_session_cleanup > 600:
                _last_session_cleanup = time.time()
                cleanup_expired_sessions()
            auto_renew_cert_if_needed()
        except Exception:
            logger.error("Collector error:\n%s", traceback.format_exc())
        _shutdown_event.wait(timeout=COLLECT_INTERVAL)
