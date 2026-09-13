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

# The panel is reachable from the internet, so a fixed 5-per-5-minutes window is
# not enough on its own: an attacker simply waits it out. Each further batch of
# failures from the same IP escalates the lockout, and bans survive a restart.
LOCKOUT_STEPS = (300, 900, 3600, 21600, 86400)
FAILED_LOG_MAX = 100
BAN_STORE_MAX = 500

# ip -> {"fails": int, "until": ts, "level": int}
_login_state = {}
_bans_loaded = False

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
        # The operator asserts a TLS-terminating proxy in front. Honour an
        # explicit X-Forwarded-Proto when the proxy sends one; TrustTunnel's
        # reverse proxy does not, and there TLS is always on (port 443).
        proto = request.headers.get("x-forwarded-proto", "")
        if proto:
            return proto.split(",")[0].strip().lower() == "https"
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


def _fmt_wait(seconds: int) -> str:
    seconds = max(1, int(seconds))
    if seconds < 60:
        return "%ds" % seconds
    if seconds < 3600:
        return "%dm" % ((seconds + 59) // 60)
    return "%dh" % ((seconds + 3599) // 3600)


def _load_bans():
    """Restore active lockouts written by a previous process."""
    global _bans_loaded
    if _bans_loaded:
        return
    _bans_loaded = True
    try:
        db = load_panel_db()
        now = time.time()
        for ip, rec in (db.get("login_bans") or {}).items():
            if isinstance(rec, dict) and rec.get("until", 0) > now:
                _login_state[ip] = {"fails": int(rec.get("fails", 0)),
                                    "until": float(rec["until"]),
                                    "level": int(rec.get("level", 0))}
        if _login_state:
            logger.info("Restored %d active login lockout(s)", len(_login_state))
    except Exception as e:
        logger.warning("Could not restore login lockouts: %s", e)


def _persist_bans():
    def _mutate(db):
        now = time.time()
        active = {ip: {"until": st["until"], "fails": st["fails"], "level": st["level"]}
                  for ip, st in _login_state.items() if st.get("until", 0) > now}
        if len(active) > BAN_STORE_MAX:
            keep = sorted(active.items(), key=lambda kv: -kv[1]["until"])[:BAN_STORE_MAX]
            active = dict(keep)
        db["login_bans"] = active

    try:
        update_panel_db(_mutate)
    except Exception as e:
        logger.warning("Could not persist login lockouts: %s", e)


def check_rate_limit(ip: str):
    """Raise 429 while `ip` is locked out. Call before verifying a password."""
    _load_bans()
    now = time.time()
    with _login_lock:
        st = _login_state.get(ip)
        if st and st.get("until", 0) > now:
            raise HTTPException(429, "Too many attempts. Try again in %s."
                                % _fmt_wait(st["until"] - now))


def record_login_failure(ip: str, user_agent: str = ""):
    """Count a failed login and escalate the lockout when the window is exceeded."""
    now = time.time()
    with _login_lock:
        st = _login_state.setdefault(ip, {"fails": 0, "until": 0.0, "level": 0, "first": now})
        if now - st.get("first", now) > LOGIN_WINDOW and st["until"] <= now:
            st["fails"] = 0
            st["first"] = now
        st["fails"] += 1
        banned_for = 0
        if st["fails"] >= LOGIN_MAX_ATTEMPTS:
            step = min(st["level"], len(LOCKOUT_STEPS) - 1)
            banned_for = LOCKOUT_STEPS[step]
            st["until"] = now + banned_for
            st["level"] = min(st["level"] + 1, len(LOCKOUT_STEPS) - 1)
            st["fails"] = 0
            st["first"] = now

    if banned_for:
        logger.warning("Login lockout: %s blocked for %s after %d failed attempts (UA: %.80s)",
                       ip, _fmt_wait(banned_for), LOGIN_MAX_ATTEMPTS, user_agent or "-")
        _persist_bans()
        try:
            from services.notify import notify_login_lockout
            notify_login_lockout(ip, banned_for)
        except Exception:
            pass
    else:
        logger.warning("Failed login from %s (UA: %.80s)", ip, user_agent or "-")

    def _mutate(db):
        log = db.get("failed_logins", [])
        log.insert(0, {"ts": int(now), "ip": ip, "ua": (user_agent or "")[:120],
                       "banned_for": banned_for})
        db["failed_logins"] = log[:FAILED_LOG_MAX]

    try:
        update_panel_db(_mutate)
    except Exception:
        pass
    return banned_for


def clear_login_failures(ip: str):
    with _login_lock:
        had_ban = bool(_login_state.pop(ip, None))
    if had_ban:
        _persist_bans()


def login_security_status():
    now = time.time()
    with _login_lock:
        active = [{"ip": ip, "until": int(st["until"]), "level": st["level"]}
                  for ip, st in _login_state.items() if st.get("until", 0) > now]
    db = load_panel_db()
    return {"locked_out": sorted(active, key=lambda x: -x["until"]),
            "recent_failures": db.get("failed_logins", [])[:50]}


def cleanup_stale_rate_limits():
    """Drop expired lockouts so the table cannot grow without bound."""
    now = time.time()
    removed = False
    with _login_lock:
        for ip in [ip for ip, st in _login_state.items()
                   if st.get("until", 0) <= now and now - st.get("first", 0) > LOGIN_WINDOW * 4]:
            _login_state.pop(ip, None)
            removed = True
    if removed:
        _persist_bans()


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
