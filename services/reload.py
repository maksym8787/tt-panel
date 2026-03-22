import subprocess
import threading

from config import logger


_pending_reload = False
_reload_timer = None
_reload_lock = threading.Lock()
_reload_detail = ""
RELOAD_DEBOUNCE = 5.0


def _log_restart(reason, detail=""):
    from auth import load_panel_db, save_panel_db
    from datetime import datetime
    try:
        panel = load_panel_db()
        history = panel.get("restart_history", [])
        entry = {"ts": datetime.now().strftime("%d.%m.%Y %H:%M:%S"), "reason": reason}
        if detail:
            entry["detail"] = detail
        history.insert(0, entry)
        panel["restart_history"] = history[:100]
        save_panel_db(panel)
    except Exception as e:
        logger.error("Failed to log restart: %s", e)


def _do_deferred_reload():
    global _pending_reload, _reload_detail
    with _reload_lock:
        _pending_reload = False
        detail = _reload_detail
        _reload_detail = ""
    try:
        subprocess.run(["systemctl", "restart", "trusttunnel"], timeout=10)
        logger.info("Service restarted (debounced)")
        _log_restart("config_change", detail)
    except Exception as e:
        logger.error("Service restart error: %s", e)


def schedule_reload(detail=""):
    global _pending_reload, _reload_timer, _reload_detail
    with _reload_lock:
        _pending_reload = True
        if detail:
            if _reload_detail:
                _reload_detail += ", " + detail
            else:
                _reload_detail = detail
        if _reload_timer is not None:
            _reload_timer.cancel()
        _reload_timer = threading.Timer(RELOAD_DEBOUNCE, _do_deferred_reload)
        _reload_timer.daemon = True
        _reload_timer.start()


def apply_reload_now(reason="manual"):
    global _pending_reload, _reload_timer
    with _reload_lock:
        if _reload_timer is not None:
            _reload_timer.cancel()
            _reload_timer = None
        _pending_reload = False
    try:
        subprocess.run(["systemctl", "restart", "trusttunnel"], timeout=10)
        logger.info("Service restarted (immediate)")
        _log_restart(reason)
    except Exception as e:
        logger.error("Service restart error: %s", e)


def is_reload_pending():
    return _pending_reload
