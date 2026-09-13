import json
import subprocess
import threading
import time
from datetime import datetime

from config import TUN_IF, NET_HISTORY_FILE, SERVICE_NAME, logger, _shutdown_event
from auth import (
    load_panel_db, save_panel_db, update_panel_db,
    cleanup_stale_rate_limits, cleanup_expired_sessions,
)
from servers import get_active_server_id, get_next_failover_server, activate_server, _check_tun_up


_fail_count = 0
_last_latency = None
_last_check_ts = 0
_health_lock = threading.Lock()

_net_recent = []
_net_aggregated = []
# Recent points are kept by AGE, not by count. A fixed 120-entry cap used to
# evict points before they were old enough to be aggregated, so at a 10s health
# interval the aggregate was never written and anything older than ~20 minutes
# vanished. The count is now only a memory guard, sized well above the window.
_RECENT_WINDOW = 3600
_RECENT_MAX = 4000
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
            cutoff = time.time() - _RECENT_WINDOW
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

def reset_external_ip_cache():
    global _external_ip, _external_ip_ts
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


_uptime_cache = {"value": 0, "ts": 0.0}
_UPTIME_TTL = 10


def _get_tt_service_uptime():
    """Service uptime in seconds.

    Cached: /api/status is polled every 10s per open tab, and this used to spawn
    two processes on every single call.
    """
    now = time.time()
    if now - _uptime_cache["ts"] < _UPTIME_TTL:
        return _uptime_cache["value"]

    value = 0
    try:
        r = subprocess.run(
            ["systemctl", "show", SERVICE_NAME, "--no-pager",
             "-p", "ActiveState,ActiveEnterTimestampMonotonic"],
            capture_output=True, text=True, timeout=5
        )
        active = False
        enter_monotonic = None
        for line in r.stdout.splitlines():
            if line.startswith("ActiveState="):
                active = line.split("=", 1)[1].strip() == "active"
            elif line.startswith("ActiveEnterTimestampMonotonic="):
                raw = line.split("=", 1)[1].strip()
                enter_monotonic = int(raw) if raw.isdigit() else None
        if active and enter_monotonic:
            # Monotonic microseconds since boot — compare against /proc/uptime
            # instead of shelling out to `date`, and immune to wall-clock jumps.
            with open("/proc/uptime") as f:
                boot_elapsed = float(f.read().split()[0])
            value = max(0, int(boot_elapsed - enter_monotonic / 1_000_000))
    except Exception as e:
        logger.debug("tt_uptime error: %s", e)

    _uptime_cache["value"] = value
    _uptime_cache["ts"] = now
    return value


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
            # Roll points older than the window into the aggregate BEFORE the
            # memory guard can drop them.
            _aggregate_old_points()
            if len(_net_recent) > _RECENT_MAX:
                del _net_recent[:-_RECENT_MAX]
    _prev_rx = rx
    _prev_tx = tx
    _prev_net_ts = now
    _save_counter += 1
    if _save_counter >= 10:
        _save_counter = 0
        with _health_lock:
            _save_net_history()


def _aggregate_old_points():
    cutoff = time.time() - _RECENT_WINDOW
    old = [p for p in _net_recent if p["ts"] < cutoff]
    if not old:
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

    with _health_lock:
        fails = _fail_count
    if fails < settings.get("failover_threshold", 3):
        return

    current = get_active_server_id()
    next_id = get_next_failover_server(current)
    if not next_id:
        logger.warning("No failover server available")
        return

    logger.info("Failover: %s -> %s (after %d failures)", current, next_id, fails)

    log_entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "from": current,
        "to": next_id,
        "reason": f"health_check_failed_{fails}x",
    }

    def _mutate(d):
        flog = d.get("failover_log", [])
        flog.insert(0, log_entry)
        d["failover_log"] = flog[:200]
        d["on_backup"] = True

    update_panel_db(_mutate)

    with _health_lock:
        _fail_count = 0

    activate_server(next_id)


def health_loop():
    _load_net_history()
    logger.info("Health check loop started")
    _shutdown_event.wait(10)
    interval = 30
    while not _shutdown_event.is_set():
        try:
            _collect_net_stats()
            db = load_panel_db()
            try:
                interval = max(10, min(int(db.get("settings", {}).get("health_check_interval", 30)), 300))
            except (TypeError, ValueError):
                interval = 30
            if get_active_server_id():
                if _do_health_check() > 0:
                    _try_failover()
            if int(time.time()) % 300 < interval:
                cleanup_stale_rate_limits()
                cleanup_expired_sessions()
        except Exception as e:
            logger.error("Health check error: %s", e)
        # `interval` is initialised above the loop: an exception on the very first
        # iteration must not kill the thread with a NameError here.
        _shutdown_event.wait(interval)


def start_health_thread():
    t = threading.Thread(target=health_loop, daemon=True, name="health-check")
    t.start()
    return t
