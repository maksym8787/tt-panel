import asyncio
import copy
import hashlib
import hmac
import json
import os
import secrets
import threading
import time

from fastapi import HTTPException

from config import PANEL_DIR, PANEL_DB, logger

# Re-entrant: several call sites legitimately nest load/save inside an
# update_panel_db() transaction. A plain Lock deadlocks there.
_panel_lock = threading.RLock()
_panel_cache = None
_panel_mtime = 0.0

# Written when panel.json turns out to be unreadable. While it exists we refuse
# to treat the panel as "unconfigured", so a corrupted DB cannot be used to
# re-run /api/setup and take the panel over.
PANEL_CORRUPT_FLAG = PANEL_DIR / "panel.corrupt"

_default_panel = {"admin_password_hash": "", "sessions": {}, "panel_settings": {"session_ttl": 86400}}

_login_attempts = {}
_login_lock = threading.Lock()
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW = 300
MIN_PASSWORD_LEN = 12

PBKDF2_ITERATIONS = 200_000


def _deep_copy_panel(d):
    return copy.deepcopy(d) if isinstance(d, dict) else dict(d)


def _atomic_write_json(path, data):
    """Write JSON 0600, durably (fsync + atomic rename), never leaving a partial file."""
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
    """True when panel.json was lost/corrupted and setup must not be re-run blindly."""
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
        "%s is unreadable (%s). Admin authentication is LOCKED to prevent takeover. "
        "Restore a backup (%s) or delete %s to re-run setup.",
        PANEL_DB, reason, backup or "n/a", PANEL_CORRUPT_FLAG,
    )
    try:
        PANEL_DIR.mkdir(parents=True, exist_ok=True)
        PANEL_CORRUPT_FLAG.write_text(
            "panel.json was unreadable at %s (%s).\n"
            "Backup: %s\n"
            "Restore it, or delete this file to allow /api/setup to run again.\n"
            % (ts, reason, backup or "n/a")
        )
        os.chmod(str(PANEL_CORRUPT_FLAG), 0o600)
    except OSError:
        pass


def _load_unlocked():
    """Read the panel DB. Caller must hold _panel_lock. Returns the cached object."""
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
    _panel_cache = _deep_copy_panel(data)
    _panel_mtime = PANEL_DB.stat().st_mtime


def load_panel_db():
    with _panel_lock:
        return _deep_copy_panel(_load_unlocked())


def save_panel_db(data):
    with _panel_lock:
        _save_unlocked(data)


def update_panel_db(mutator):
    """Atomic read-modify-write.

    `mutator(db)` mutates the dict in place; its return value is passed back to
    the caller. Without this, concurrent callers each load their own copy and
    the last save silently discards the other's changes.
    """
    with _panel_lock:
        db = _deep_copy_panel(_load_unlocked())
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
        # legacy: salt$hash at the old fixed 100k iterations
        salt, expected = parts
        h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), iterations=100_000)
        return hmac.compare_digest(h.hex(), expected)
    # legacy: bare sha256
    return hmac.compare_digest(hashlib.sha256(pw.encode()).hexdigest(), stored)


def needs_rehash(stored: str) -> bool:
    parts = stored.split('$')
    if len(parts) != 3:
        return True
    try:
        return int(parts[1]) < PBKDF2_ITERATIONS
    except ValueError:
        return True


def request_is_secure(request) -> bool:
    """Whether this request reached us over TLS.

    X-Forwarded-Proto is only honoured when the operator has declared that the
    panel sits behind a trusted reverse proxy (TT_BEHIND_PROXY=1) — otherwise a
    client could simply send the header and downgrade its own cookie flags.
    """
    import config
    if config._ssl_configured:
        return True
    if getattr(config, "BEHIND_PROXY", False):
        proto = request.headers.get("x-forwarded-proto", "")
        if proto.split(",")[0].strip().lower() == "https":
            return True
    return request.url.scheme == "https"


def check_session(request) -> bool:
    token = request.cookies.get("tt_session")
    if not token:
        return False
    db = load_panel_db()
    s = db.get("sessions", {}).get(_hash_token(token))
    if not s:
        return False
    ttl = db.get("panel_settings", {}).get("session_ttl", 86400)
    # Expired sessions are reaped by the collector; the read path stays read-only
    # so that concurrent requests cannot clobber each other's writes.
    return time.time() - s.get("created", 0) <= ttl


async def require_auth(request):
    ok = await asyncio.to_thread(check_session, request)
    if not ok:
        raise HTTPException(401, "Unauthorized")


def check_rate_limit(ip: str):
    now = time.time()
    with _login_lock:
        attempts = [t for t in _login_attempts.get(ip, []) if now - t < LOGIN_WINDOW]
        _login_attempts[ip] = attempts
        if len(attempts) >= LOGIN_MAX_ATTEMPTS:
            retry_in = int(LOGIN_WINDOW - (now - attempts[0])) + 1
            raise HTTPException(429, "Too many attempts. Try again in %ds." % retry_in)
        attempts.append(now)


def cleanup_stale_rate_limits():
    now = time.time()
    with _login_lock:
        stale_ips = [ip for ip, ts_list in _login_attempts.items()
                     if all(now - t > LOGIN_WINDOW for t in ts_list)]
        for ip in stale_ips:
            _login_attempts.pop(ip, None)


def cleanup_expired_sessions():
    """Drop timed-out sessions. Runs on the collector thread, not on request paths."""
    def _prune(db):
        sessions = db.get("sessions", {})
        if not sessions:
            return 0
        ttl = db.get("panel_settings", {}).get("session_ttl", 86400)
        cutoff = time.time() - ttl
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
