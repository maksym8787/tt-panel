"""Telegram alerts.

Conditions are evaluated on the collector thread. Each alert has a key and only
fires on a state change (ok -> problem), with a re-notify interval so a lasting
problem reminds without spamming. Recovery sends one "resolved" message.
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from config import logger

TELEGRAM_API = "https://api.telegram.org/bot%s/sendMessage"
SEND_TIMEOUT = 10
# A problem that persists re-notifies at most this often.
RENOTIFY_SECS = 6 * 3600

DEFAULTS = {
    "enabled": False,
    "bot_token": "",
    "chat_id": "",
    "alert_service_down": True,
    "alert_cert_expiring": True,
    "alert_disk_full": True,
    "alert_login_lockout": True,
    "cert_days_threshold": 14,
    "disk_percent_threshold": 85,
}


def get_settings():
    from auth import load_panel_db
    cfg = dict(DEFAULTS)
    cfg.update(load_panel_db().get("telegram", {}) or {})
    return cfg


def send_message(text: str, cfg=None) -> tuple:
    """Returns (ok, error_text). Never raises."""
    cfg = cfg or get_settings()
    token = str(cfg.get("bot_token", "")).strip()
    chat_id = str(cfg.get("chat_id", "")).strip()
    if not token or not chat_id:
        return False, "bot token or chat id is not set"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        req = urllib.request.Request(TELEGRAM_API % token, data=payload)
        with urllib.request.urlopen(req, timeout=SEND_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        if data.get("ok"):
            return True, ""
        return False, str(data.get("description", "unknown error"))[:200]
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
            return False, str(body.get("description", e.reason))[:200]
        except Exception:
            return False, "HTTP %s" % e.code
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)


def _alert_state():
    from auth import load_panel_db
    return load_panel_db().get("alert_state", {}) or {}


def _set_alert_state(key, value):
    from auth import update_panel_db

    def _mutate(db):
        st = db.setdefault("alert_state", {})
        if value is None:
            st.pop(key, None)
        else:
            st[key] = value

    update_panel_db(_mutate)


def _fire(key, title, body, cfg):
    """Send when the condition newly appears or the re-notify window elapsed."""
    now = time.time()
    st = _alert_state().get(key)
    if st and now - st.get("sent", 0) < RENOTIFY_SECS:
        return
    host = _hostname()
    ok, err = send_message("⚠️ <b>%s</b>\n%s\n\n<i>%s</i>" % (title, body, host), cfg)
    if ok:
        _set_alert_state(key, {"sent": now})
        logger.info("Alert sent: %s", key)
    else:
        logger.warning("Alert %s not sent: %s", key, err)


def _resolve(key, title, cfg):
    if not _alert_state().get(key):
        return
    _set_alert_state(key, None)
    send_message("✅ <b>%s</b>\n\n<i>%s</i>" % (title, _hostname()), cfg)
    logger.info("Alert resolved: %s", key)


def _hostname():
    try:
        import socket
        return socket.gethostname()
    except Exception:
        return "tt-panel"


def check_and_alert():
    """Evaluate all alert conditions. Called from the collector loop."""
    cfg = get_settings()
    if not cfg.get("enabled") or not cfg.get("bot_token") or not cfg.get("chat_id"):
        return

    if cfg.get("alert_service_down", True):
        try:
            from services.system import get_service_status
            svc = get_service_status()
            if svc and not svc.get("active"):
                _fire("service_down", "TrustTunnel is down",
                      "The VPN service is not active. Clients cannot connect.", cfg)
            else:
                _resolve("service_down", "TrustTunnel is back up", cfg)
        except Exception as e:
            logger.debug("service alert check failed: %s", e)

    if cfg.get("alert_cert_expiring", True):
        try:
            from services.cert import get_cert_days_remaining
            info = get_cert_days_remaining()
            threshold = int(cfg.get("cert_days_threshold", 14))
            if info and info.get("days") is not None:
                days = info["days"]
                if days <= threshold:
                    _fire("cert_expiring", "TLS certificate expires soon",
                          "%d day(s) left (expires %s)." % (days, info.get("date", "?")), cfg)
                else:
                    _resolve("cert_expiring", "TLS certificate renewed", cfg)
        except Exception as e:
            logger.debug("cert alert check failed: %s", e)

    if cfg.get("alert_disk_full", True):
        try:
            import os
            st = os.statvfs("/")
            total = st.f_frsize * st.f_blocks
            free = st.f_frsize * st.f_bfree
            pct = round(100 * (total - free) / total, 1) if total else 0
            threshold = int(cfg.get("disk_percent_threshold", 85))
            if pct >= threshold:
                _fire("disk_full", "Disk is filling up",
                      "Root filesystem at %.1f%% (%.1f GB free)." % (pct, free / 1073741824), cfg)
            else:
                _resolve("disk_full", "Disk usage back to normal", cfg)
        except Exception as e:
            logger.debug("disk alert check failed: %s", e)


def notify_login_lockout(ip: str, seconds: int):
    """Called straight from the auth path when an IP gets locked out."""
    cfg = get_settings()
    if not cfg.get("enabled") or not cfg.get("alert_login_lockout", True):
        return
    mins = max(1, seconds // 60)
    _fire("lockout_%s" % ip, "Panel login blocked",
          "IP <code>%s</code> was blocked for %d min after repeated failed logins."
          % (ip, mins), cfg)
