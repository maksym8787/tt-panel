import asyncio
import hashlib
import hmac
import json
import secrets
import threading
import time

from fastapi import HTTPException

from config import PANEL_DIR, PANEL_DB, logger

_panel_lock = threading.Lock()
_panel_cache = None
_panel_mtime = 0.0

_default_panel = {"admin_password_hash": "", "sessions": {}, "panel_settings": {"session_ttl": 86400}}

_login_attempts = {}
_login_lock = threading.Lock()
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW = 300


def _deep_copy_panel(d):
    return {"admin_password_hash": d.get("admin_password_hash", ""),
            "sessions": dict(d.get("sessions", {})),
            "panel_settings": dict(d.get("panel_settings", {"session_ttl": 86400}))}


def load_panel_db():
    global _panel_cache, _panel_mtime
    with _panel_lock:
        if PANEL_DB.exists():
            try:
                mt = PANEL_DB.stat().st_mtime
                if _panel_cache is not None and mt == _panel_mtime:
                    return _deep_copy_panel(_panel_cache)
                data = json.loads(PANEL_DB.read_text())
                if not isinstance(data, dict):
                    raise ValueError("panel.json must be a JSON object")
                _panel_cache = data
                _panel_mtime = mt
                return _deep_copy_panel(data)
            except (json.JSONDecodeError, ValueError):
                logger.warning("%s corrupted, backing up and resetting", PANEL_DB)
                PANEL_DB.rename(PANEL_DB.with_suffix(".bak"))
        return _deep_copy_panel(_default_panel)


def save_panel_db(data):
    global _panel_cache, _panel_mtime
    with _panel_lock:
        PANEL_DIR.mkdir(parents=True, exist_ok=True)
        tmp = PANEL_DB.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(PANEL_DB)
        _panel_cache = _deep_copy_panel(data)
        _panel_mtime = PANEL_DB.stat().st_mtime


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(pw: str, salt: str = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), iterations=100_000)
    return f"{salt}${h.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    if '$' in stored:
        salt, _ = stored.split('$', 1)
        return hmac.compare_digest(hash_password(pw, salt), stored)
    return hmac.compare_digest(hashlib.sha256(pw.encode()).hexdigest(), stored)


def check_session(request):
    token = request.cookies.get("tt_session")
    if not token:
        return False
    db = load_panel_db()
    token_hash = _hash_token(token)
    s = db.get("sessions", {}).get(token_hash)
    if not s:
        s = db.get("sessions", {}).get(token)
        if s:
            del db["sessions"][token]
            db["sessions"][token_hash] = s
            save_panel_db(db)
            logger.info("Migrated session token to hashed format")
        else:
            return False
    ttl = db.get("panel_settings", {}).get("session_ttl", 86400)
    if time.time() - s.get("created", 0) > ttl:
        del db["sessions"][token_hash]
        save_panel_db(db)
        return False
    return True


async def require_auth(request):
    ok = await asyncio.to_thread(check_session, request)
    if not ok:
        raise HTTPException(401, "Unauthorized")


def check_rate_limit(ip: str):
    now = time.time()
    with _login_lock:
        attempts = _login_attempts.get(ip, [])
        attempts = [t for t in attempts if now - t < LOGIN_WINDOW]
        _login_attempts[ip] = attempts
        if len(attempts) >= LOGIN_MAX_ATTEMPTS:
            raise HTTPException(429, f"Too many attempts. Try again in {LOGIN_WINDOW}s.")
        attempts.append(now)


def cleanup_stale_rate_limits():
    now = time.time()
    with _login_lock:
        stale_ips = [ip for ip, ts_list in _login_attempts.items()
                     if all(now - t > LOGIN_WINDOW for t in ts_list)]
        for ip in stale_ips:
            _login_attempts.pop(ip, None)
