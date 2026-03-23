import hashlib
import json
import secrets
import threading
import time

from fastapi import HTTPException, Request

from config import PANEL_DIR, PANEL_DB, logger

_panel_lock = threading.Lock()
_panel_cache = None
_panel_mtime = 0.0

_default_panel = {
    "admin_password_hash": "",
    "sessions": {},
    "active_server": "",
    "settings": {
        "health_check_interval": 30,
        "auto_failover": True,
        "failover_threshold": 3,
        "killswitch_enabled": True,
        "vpn_mode": "general",
        "dns_upstreams": [],
        "exclusions": [],
        "mtu_size": 1280,
    },
    "servers": [],
    "failover_log": [],
}

_login_attempts = {}
_login_lock = threading.Lock()
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW = 300


def load_panel_db():
    global _panel_cache, _panel_mtime
    import copy
    with _panel_lock:
        if PANEL_DB.exists():
            try:
                mt = PANEL_DB.stat().st_mtime
                if _panel_cache is not None and mt == _panel_mtime:
                    return copy.deepcopy(_panel_cache)
                data = json.loads(PANEL_DB.read_text())
                if not isinstance(data, dict):
                    raise ValueError("panel.json must be a JSON object")
                _panel_cache = data
                _panel_mtime = mt
                return copy.deepcopy(data)
            except (json.JSONDecodeError, ValueError):
                logger.warning("%s corrupted, backing up and resetting", PANEL_DB)
                PANEL_DB.rename(PANEL_DB.with_suffix(".bak"))
        return copy.deepcopy(_default_panel)


def save_panel_db(data):
    global _panel_cache, _panel_mtime
    import copy
    with _panel_lock:
        PANEL_DIR.mkdir(parents=True, exist_ok=True)
        tmp = PANEL_DB.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        tmp.replace(PANEL_DB)
        _panel_cache = copy.deepcopy(data)
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
        salt, expected = stored.split('$', 1)
        h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), iterations=100_000)
        import hmac as _hmac
    return _hmac.compare_digest(h.hex(), expected)
    return hashlib.sha256(pw.encode()).hexdigest() == stored


def check_rate_limit(ip: str):
    with _login_lock:
        now = time.time()
        attempts = _login_attempts.get(ip, [])
        attempts = [t for t in attempts if now - t < LOGIN_WINDOW]
        if len(attempts) >= LOGIN_MAX_ATTEMPTS:
            raise HTTPException(429, "Too many attempts, try later")
        attempts.append(now)
        _login_attempts[ip] = attempts


def check_session(request: Request) -> bool:
    token = request.cookies.get("tt_session")
    if not token:
        return False
    db = load_panel_db()
    token_hash = _hash_token(token)
    session = db.get("sessions", {}).get(token_hash)
    old_key = None
    if not session:
        session = db.get("sessions", {}).get(token)
        if session:
            old_key = token
        else:
            return False
    ttl = db.get("settings", {}).get("session_ttl", 86400)
    if time.time() - session.get("created", 0) > ttl:
        db.get("sessions", {}).pop(token_hash, None)
        if old_key:
            db.get("sessions", {}).pop(old_key, None)
        save_panel_db(db)
        return False
    if old_key:
        db.get("sessions", {}).pop(old_key, None)
        db["sessions"][token_hash] = session
        save_panel_db(db)
    return True


async def require_auth(request: Request):
    import asyncio
    authed = await asyncio.to_thread(check_session, request)
    if not authed:
        raise HTTPException(401, "Not authenticated")
