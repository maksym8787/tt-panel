import json
import subprocess
import threading
import time
from datetime import datetime

from config import TUN_IF, NET_HISTORY_FILE, SERVICE_NAME, logger, _shutdown_event
from auth import load_panel_db, save_panel_db
from servers import get_active_server_id, get_next_failover_server, activate_server, _check_tun_up


_fail_count = 0
_last_latency = None
_last_check_ts = 0
_health_lock = threading.Lock()

_net_recent = []
_net_aggregated = []
_RECENT_MAX = 120
_AGGREGATED_MAX = 105120
_AGG_INTERVAL = 300
_prev_rx = 0
_prev_tx = 0
_prev_net_ts = 0
_save_counter = 0


def _load_net_history():
    global _net_recent, _net_aggregated
    try:
        if NET_HISTORY_FILE.exists():
            data = json.loads(NET_HISTORY_FILE.read_text())
            _net_aggregated = data.get("aggregated", [])[-_AGGREGATED_MAX:]
            cutoff = time.time() - 3600
            _net_recent = [p for p in data.get("recent", []) if p.get("ts", 0) > cutoff]
            logger.info("Loaded net history: %d recent, %d aggregated", len(_net_recent), len(_net_aggregated))
    except Exception as e:
        logger.warning("Failed to load net history: %s", e)


def _save_net_history():
    try:
        data = {"recent": _net_recent[-_RECENT_MAX:], "aggregated": _net_aggregated[-_AGGREGATED_MAX:]}
        tmp = NET_HISTORY_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data))
        tmp.replace(NET_HISTORY_FILE)
    except Exception as e:
        logger.warning("Failed to save net history: %s", e)


_external_ip = None
_external_ip_ts = 0

def _get_external_ip():
    global _external_ip, _external_ip_ts
    now = time.time()
    if _external_ip and (now - _external_ip_ts) < 300:
        return _external_ip
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "5", "--interface", TUN_IF, "https://api.ipify.org"],
            capture_output=True, text=True, timeout=8
        )
        if r.returncode == 0 and r.stdout.strip():
            _external_ip = r.stdout.strip()
            _external_ip_ts = now
            return _external_ip
    except Exception:
        pass
    return _external_ip


def _get_tt_service_uptime():
    try:
        r = subprocess.run(
            ["systemctl", "show", SERVICE_NAME, "-p", "ActiveState,ActiveEnterTimestampMonotonic"],
            capture_output=True, text=True, timeout=5
        )
        active = False
        enter_us = 0
        for line in r.stdout.splitlines():
            if line.startswith("ActiveState="):
                active = line.split("=", 1)[1].strip() == "active"
            elif line.startswith("ActiveEnterTimestampMonotonic="):
                v = line.split("=", 1)[1].strip()
                if v.isdigit():
                    enter_us = int(v)
        if not active or enter_us == 0:
            return 0
        with open("/proc/uptime") as f:
            now_us = int(float(f.read().split()[0]) * 1_000_000)
        return max(0, (now_us - enter_us) // 1_000_000)
    except Exception:
        pass
    return 0


def get_health_status():
    tun_up = _check_tun_up()
    tun_ip = _get_tun_ip()
    ext_ip = _get_external_ip() if tun_up else None
    tt_uptime = _get_tt_service_uptime()
    with _health_lock:
        connected = tun_up and _fail_count < 2 and _last_latency is not None
        return {
            "tun_up": tun_up,
            "connected": connected,
            "tun_ip": tun_ip if tun_up else None,
            "external_ip": ext_ip,
            "tt_uptime": tt_uptime,
            "latency_ms": _last_latency,
            "fail_count": _fail_count,
            "last_check": _last_check_ts,
        }


def _get_tun_ip():
    try:
        r = subprocess.run(
            ["ip", "-4", "addr", "show", TUN_IF],
            capture_output=True, text=True, timeout=5
        )
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                return line.split()[1].split("/")[0]
    except Exception:
        pass
    return None


def _read_tun_bytes():
    try:
        with open("/proc/net/dev") as f:
            for line in f:
                parts = line.strip().split()
                if parts and parts[0].rstrip(":") == TUN_IF:
                    rx = int(parts[1])
                    tx = int(parts[9])
                    return rx, tx
    except Exception:
        pass
    return 0, 0


def _collect_net_stats():
    global _prev_rx, _prev_tx, _prev_net_ts, _save_counter
    rx, tx = _read_tun_bytes()
    now = time.time()
    if _prev_net_ts > 0 and (now - _prev_net_ts) > 0:
        dt = now - _prev_net_ts
        d_rx = max(0, rx - _prev_rx)
        d_tx = max(0, tx - _prev_tx)
        entry = {"ts": int(now), "rx_bps": int(d_rx / dt), "tx_bps": int(d_tx / dt)}
        with _health_lock:
            _net_recent.append(entry)
            if len(_net_recent) > _RECENT_MAX:
                del _net_recent[:-_RECENT_MAX]
            _aggregate_old_points()
    _prev_rx = rx
    _prev_tx = tx
    _prev_net_ts = now
    _save_counter += 1
    if _save_counter >= 10:
        _save_counter = 0
        with _health_lock:
            _save_net_history()


def _aggregate_old_points():
    cutoff = time.time() - 3600
    old = [p for p in _net_recent if p["ts"] < cutoff]
    if len(old) < 5:
        return
    bucket_ts = (old[0]["ts"] // _AGG_INTERVAL) * _AGG_INTERVAL
    bucket = []
    for p in old:
        pt = (p["ts"] // _AGG_INTERVAL) * _AGG_INTERVAL
        if pt != bucket_ts:
            if bucket:
                _net_aggregated.append({
                    "ts": bucket_ts,
                    "rx_bps": sum(b["rx_bps"] for b in bucket) // len(bucket),
                    "tx_bps": sum(b["tx_bps"] for b in bucket) // len(bucket),
                })
            bucket = []
            bucket_ts = pt
        bucket.append(p)
    if bucket:
        _net_aggregated.append({
            "ts": bucket_ts,
            "rx_bps": sum(b["rx_bps"] for b in bucket) // len(bucket),
            "tx_bps": sum(b["tx_bps"] for b in bucket) // len(bucket),
        })
    if len(_net_aggregated) > _AGGREGATED_MAX:
        del _net_aggregated[:-_AGGREGATED_MAX]
    _net_recent[:] = [p for p in _net_recent if p["ts"] >= cutoff]


def get_net_history():
    with _health_lock:
        return _net_aggregated + _net_recent


def _ping_through_tun():
    try:
        r = subprocess.run(
            ["ping", "-c", "1", "-W", "3", "-I", TUN_IF, "1.1.1.1"],
            capture_output=True, text=True, timeout=6
        )
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                if "time=" in line:
                    ms = line.split("time=")[1].split()[0]
                    return float(ms)
            return 0.0
    except Exception:
        pass
    return None


def _do_health_check():
    global _fail_count, _last_latency, _last_check_ts

    tun_up = _check_tun_up()
    latency = None
    if tun_up:
        latency = _ping_through_tun()

    with _health_lock:
        _last_check_ts = time.time()
        _last_latency = latency

        if not tun_up or latency is None:
            _fail_count += 1
        else:
            _fail_count = 0

    return _fail_count


def _try_failover():
    global _fail_count
    db = load_panel_db()
    settings = db.get("settings", {})
    if not settings.get("auto_failover", True):
        return

    threshold = settings.get("failover_threshold", 3)
    if _fail_count < threshold:
        return

    current = get_active_server_id()
    next_id = get_next_failover_server(current)
    if not next_id:
        logger.warning("No failover server available")
        return

    logger.info("Failover: %s -> %s (after %d failures)", current, next_id, _fail_count)

    log_entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "from": current,
        "to": next_id,
        "reason": f"health_check_failed_{_fail_count}x",
    }
    flog = db.get("failover_log", [])
    flog.insert(0, log_entry)
    db["failover_log"] = flog[:200]
    db["on_backup"] = True
    save_panel_db(db)

    with _health_lock:
        _fail_count = 0

    activate_server(next_id)


def health_loop():
    _load_net_history()
    logger.info("Health check loop started")
    time.sleep(10)
    while not _shutdown_event.is_set():
        try:
            _collect_net_stats()
            db = load_panel_db()
            interval = db.get("settings", {}).get("health_check_interval", 30)
            active = get_active_server_id()
            if active:
                fails = _do_health_check()
                if fails > 0:
                    _try_failover()
        except Exception as e:
            logger.error("Health check error: %s", e)
        _shutdown_event.wait(max(10, interval))


def start_health_thread():
    t = threading.Thread(target=health_loop, daemon=True, name="health-check")
    t.start()
    return t
