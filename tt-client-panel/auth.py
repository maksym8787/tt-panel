import asyncio
import copy
import hashlib
import hmac
import json
import os
import secrets
import threading
import time

from fastapi import HTTPException, Request

from config import PANEL_DIR, PANEL_DB, logger

# Re-entrant: update_panel_db() nests load/save inside one transaction, and a
# plain Lock would deadlock there (it previously did, in reorder_servers).
_panel_lock = threading.RLock()
_panel_cache = None
_panel_mtime = 0.0

PANEL_CORRUPT_FLAG = PANEL_DIR / "panel.corrupt"

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
        "mtu_size": 1350,
        "session_ttl": 86400,
    },
    "servers": [],
    "failover_log": [],
}

_login_attempts = {}
_login_lock = threading.Lock()
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW = 300
MIN_PASSWORD_LEN = 12
DEFAULT_SESSION_TTL = 86400

PBKDF2_ITERATIONS = 200_000


def _atomic_write_json(path, data):
    """Write JSON 0600, durably. The file holds VPN passwords and session keys."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(path.parent), 0o700)
    except OSError:
        pass
    tmp = path.with_suffix(".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    os.replace(str(tmp), str(path))
    try:
        os.chmod(str(path), 0o600)
    except OSError:
        pass
    try:
        dfd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass


def setup_locked() -> bool:
    return PANEL_CORRUPT_FLAG.exists()


def _mark_corrupt(reason: str):
    ts = time.strftime("%Y%m%d-%H%M%S")
    backup = PANEL_DB.with_name("panel.json.corrupt-%s" % ts)
    try:
        PANEL_DB.rename(backup)
    except OSError as e:
        logger.error("Could not back up corrupted %s: %s", PANEL_DB, e)
        backup = None
    logger.error(
        "%s is unreadable (%s). Setup is LOCKED to prevent takeover. "
        "Restore a backup (%s) or delete %s to re-run setup.",
        PANEL_DB, reason, backup or "n/a", PANEL_CORRUPT_FLAG,
    )
    try:
        PANEL_DIR.mkdir(parents=True, exist_ok=True)
        PANEL_CORRUPT_FLAG.write_text(
            "panel.json was unreadable at %s (%s).\nBackup: %s\n" % (ts, reason, backup or "n/a"))
        os.chmod(str(PANEL_CORRUPT_FLAG), 0o600)
    except OSError:
        pass


def _load_unlocked():
    global _panel_cache, _panel_mtime
    if PANEL_DB.exists():
        try:
            mt = PANEL_DB.stat().st_mtime
            if _panel_cache is not None and mt == _panel_mtime:
                return _panel_cache
            data = json.loads(PANEL_DB.read_text())
            if not isinstance(data, dict):
                raise ValueError("panel.json must be a JSON object")
            _panel_cache = data
            _panel_mtime = mt
            return data
        except (json.JSONDecodeError, ValueError, OSError) as e:
            _mark_corrupt(type(e).__name__)
    return _default_panel


def _save_unlocked(data):
    global _panel_cache, _panel_mtime
    _atomic_write_json(PANEL_DB, data)
    _panel_cache = copy.deepcopy(data)
    _panel_mtime = PANEL_DB.stat().st_mtime


def load_panel_db():
    with _panel_lock:
        return copy.deepcopy(_load_unlocked())


def save_panel_db(data):
    with _panel_lock:
        _save_unlocked(data)


def update_panel_db(mutator):
    """Atomic read-modify-write.

    The health thread (failover) and request handlers both mutate this file; a
    load/modify/save without the lock loses whichever write finishes first.
    """
    with _panel_lock:
        db = copy.deepcopy(_load_unlocked())
        result = mutator(db)
        _save_unlocked(db)
        return result


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(pw: str, salt: str = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), iterations=iterations)
    return "%s$%d$%s" % (salt, iterations, h.hex())


def verify_password(pw: str, stored: str) -> bool:
    if not stored:
        return False
    parts = stored.split('$')
    if len(parts) == 3:
        salt, iters, expected = parts
        try:
            iterations = int(iters)
        except ValueError:
            return False
        h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), iterations=iterations)
        return hmac.compare_digest(h.hex(), expected)
    if len(parts) == 2:
        salt, expected = parts
        h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), iterations=100_000)
        return hmac.compare_digest(h.hex(), expected)
    return hmac.compare_digest(hashlib.sha256(pw.encode()).hexdigest(), stored)


def needs_rehash(stored: str) -> bool:
    parts = stored.split('$')
    if len(parts) != 3:
        return True
    try:
        return int(parts[1]) < PBKDF2_ITERATIONS
    except ValueError:
        return True


def session_ttl(db=None) -> int:
    db = db if db is not None else load_panel_db()
    try:
        return int(db.get("settings", {}).get("session_ttl", DEFAULT_SESSION_TTL))
    except (TypeError, ValueError):
        return DEFAULT_SESSION_TTL


def check_rate_limit(ip: str):
    now = time.time()
    with _login_lock:
        attempts = [t for t in _login_attempts.get(ip, []) if now - t < LOGIN_WINDOW]
        _login_attempts[ip] = attempts
        if len(attempts) >= LOGIN_MAX_ATTEMPTS:
            retry_in = int(LOGIN_WINDOW - (now - attempts[0])) + 1
            raise HTTPException(429, "Too many attempts. Try again in %ds." % retry_in)
        attempts.append(now)


def request_is_secure(request: Request) -> bool:
    import config
    if config._ssl_configured:
        return True
    if getattr(config, "BEHIND_PROXY", False):
        proto = request.headers.get("x-forwarded-proto", "")
        if proto.split(",")[0].strip().lower() == "https":
            return True
    return request.url.scheme == "https"


def check_session(request: Request) -> bool:
    token = request.cookies.get("tt_session")
    if not token:
        return False
    db = load_panel_db()
    # Only the hashed token is accepted: the stored keys ARE the hashes, so
    # honouring a raw key would let anyone who read panel.json authenticate.
    s = db.get("sessions", {}).get(_hash_token(token))
    if not s:
        return False
    return time.time() - s.get("created", 0) <= session_ttl(db)


async def require_auth(request: Request):
    authed = await asyncio.to_thread(check_session, request)
    if not authed:
        raise HTTPException(401, "Not authenticated")


def cleanup_expired_sessions():
    def _prune(db):
        sessions = db.get("sessions", {})
        if not sessions:
            return 0
        cutoff = time.time() - session_ttl(db)
        alive = {k: v for k, v in sessions.items() if v.get("created", 0) > cutoff}
        removed = len(sessions) - len(alive)
        if removed:
            db["sessions"] = alive
        return removed

    try:
        removed = update_panel_db(_prune)
        if removed:
            logger.info("Reaped %d expired session(s)", removed)
    except Exception as e:
        logger.warning("Session cleanup failed: %s", e)


def cleanup_stale_rate_limits():
    now = time.time()
    with _login_lock:
        for ip in [ip for ip, ts in _login_attempts.items() if all(now - t > LOGIN_WINDOW for t in ts)]:
            _login_attempts.pop(ip, None)
