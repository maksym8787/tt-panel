import subprocess
import threading
import time
from datetime import datetime

from config import TUN_IF, logger, _shutdown_event
from auth import load_panel_db, save_panel_db
from servers import get_active_server_id, get_next_failover_server, activate_server, _check_tun_up


_fail_count = 0
_last_latency = None
_last_check_ts = 0
_health_lock = threading.Lock()

_net_history = []
_NET_HISTORY_MAX = 20160
_prev_rx = 0
_prev_tx = 0
_prev_net_ts = 0


def get_health_status():
    with _health_lock:
        return {
            "tun_up": _check_tun_up(),
            "tun_ip": _get_tun_ip(),
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
    global _prev_rx, _prev_tx, _prev_net_ts
    rx, tx = _read_tun_bytes()
    now = time.time()
    if _prev_net_ts > 0 and (now - _prev_net_ts) > 0:
        dt = now - _prev_net_ts
        d_rx = max(0, rx - _prev_rx)
        d_tx = max(0, tx - _prev_tx)
        entry = {
            "ts": int(now),
            "rx_bps": int(d_rx / dt),
            "tx_bps": int(d_tx / dt),
            "rx_total": rx,
            "tx_total": tx,
        }
        with _health_lock:
            _net_history.append(entry)
            if len(_net_history) > _NET_HISTORY_MAX:
                del _net_history[:-_NET_HISTORY_MAX]
    _prev_rx = rx
    _prev_tx = tx
    _prev_net_ts = now


def get_net_history():
    with _health_lock:
        return list(_net_history)


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
    db = load_panel_db()
    flog = db.get("failover_log", [])
    flog.insert(0, log_entry)
    db["failover_log"] = flog[:200]
    save_panel_db(db)

    with _health_lock:
        _fail_count = 0

    activate_server(next_id)


def health_loop():
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
