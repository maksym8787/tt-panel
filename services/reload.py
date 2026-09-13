import os
import subprocess
import threading

from config import logger

_pending_reload = False
_reload_timer = None
_reload_lock = threading.Lock()
_reload_detail = ""
_last_reload_ok = True
_last_reload_error = ""
RELOAD_DEBOUNCE = 5.0

# `restart` is the default because it is the only mode guaranteed to pick up new
# credentials. Set TT_RELOAD_MODE=reload to use the unit's ExecReload (SIGHUP)
# instead, which keeps existing tunnels alive — only do that if your TrustTunnel
# build re-reads credentials.toml on SIGHUP.
RELOAD_MODE = os.environ.get("TT_RELOAD_MODE", "restart").strip().lower()
if RELOAD_MODE not in ("restart", "reload"):
    RELOAD_MODE = "restart"


def _log_restart(reason, detail=""):
    from auth import update_panel_db
    from datetime import datetime
    try:
        entry = {"ts": datetime.now().strftime("%d.%m.%Y %H:%M:%S"), "reason": reason}
        if detail:
            entry["detail"] = detail

        def _mutate(panel):
            history = panel.get("restart_history", [])
            history.insert(0, entry)
            panel["restart_history"] = history[:100]

        update_panel_db(_mutate)
    except Exception as e:
        logger.error("Failed to log restart: %s", e)


def _run_service_action(action):
    """Returns (ok, error_text)."""
    try:
        r = subprocess.run(["systemctl", action, "trusttunnel"],
                           timeout=30, capture_output=True, text=True)
        if r.returncode == 0:
            return True, ""
        err = (r.stderr or r.stdout or "").strip()[:300] or ("exit code %d" % r.returncode)
        return False, err
    except subprocess.TimeoutExpired:
        return False, "systemctl %s timed out" % action
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)


def _apply(reason, detail):
    global _last_reload_ok, _last_reload_error
    ok, err = _run_service_action(RELOAD_MODE)
    _last_reload_ok = ok
    _last_reload_error = err
    if ok:
        logger.info("Service %s succeeded (%s)", RELOAD_MODE, reason)
        _log_restart(reason, detail)
    else:
        logger.error("Service %s failed: %s", RELOAD_MODE, err)
    return ok


def _do_deferred_reload():
    global _pending_reload, _reload_detail
    with _reload_lock:
        _pending_reload = False
        detail = _reload_detail
        _reload_detail = ""
    _apply("config_change", detail)


def schedule_reload(detail=""):
    global _pending_reload, _reload_timer, _reload_detail
    with _reload_lock:
        _pending_reload = True
        if detail:
            _reload_detail = (_reload_detail + ", " + detail) if _reload_detail else detail
        if _reload_timer is not None:
            _reload_timer.cancel()
        _reload_timer = threading.Timer(RELOAD_DEBOUNCE, _do_deferred_reload)
        _reload_timer.daemon = True
        _reload_timer.start()


def apply_reload_now(reason="manual"):
    global _pending_reload, _reload_timer, _reload_detail
    with _reload_lock:
        if _reload_timer is not None:
            _reload_timer.cancel()
            _reload_timer = None
        _pending_reload = False
        detail = _reload_detail
        _reload_detail = ""
    ok = _apply(reason, detail)
    return {"ok": ok, "error": _last_reload_error}


def is_reload_pending():
    return _pending_reload


def last_reload_ok():
    return _last_reload_ok


def last_reload_error():
    return _last_reload_error
