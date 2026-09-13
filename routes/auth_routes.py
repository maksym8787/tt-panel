import asyncio
import secrets
import time

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

import config
from auth import (
    load_panel_db, update_panel_db, hash_password, verify_password,
    check_session, require_auth, check_rate_limit, _hash_token, needs_rehash,
    setup_locked, request_is_secure, MIN_PASSWORD_LEN,
    _login_lock, _login_attempts,
)
from routes import app


def _set_session_cookie(resp, token, ttl, secure):
    resp.set_cookie(
        "tt_session", token,
        httponly=True,
        secure=secure,
        max_age=ttl,
        samesite="strict" if secure else "lax",
        path="/",
    )


@app.post("/api/setup")
async def setup_admin(request: Request):
    if setup_locked():
        raise HTTPException(
            409,
            "Panel database was lost or corrupted. Setup is locked to prevent takeover. "
            "Restore panel.json from a backup, or remove panel.corrupt on the server to re-run setup.",
        )
    db = await asyncio.to_thread(load_panel_db)
    if db.get("admin_password_hash"):
        raise HTTPException(400, "Already configured. Use change-password instead.")
    body = await request.json()
    pw = body.get("password", "")
    if len(pw) < MIN_PASSWORD_LEN:
        raise HTTPException(400, "Password must be at least %d characters" % MIN_PASSWORD_LEN)
    new_hash = await asyncio.to_thread(hash_password, pw)

    def _mutate(d):
        if d.get("admin_password_hash"):
            raise HTTPException(400, "Already configured. Use change-password instead.")
        d["admin_password_hash"] = new_hash
        d["sessions"] = {}

    await asyncio.to_thread(update_panel_db, _mutate)
    return {"ok": True}


@app.post("/api/login")
async def login(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)
    body = await request.json()
    pw = body.get("password", "")
    db = await asyncio.to_thread(load_panel_db)
    stored = db.get("admin_password_hash", "")
    if not stored:
        raise HTTPException(400, "Setup required")
    if not await asyncio.to_thread(verify_password, pw, stored):
        raise HTTPException(401, "Bad password")

    token = secrets.token_hex(32)
    token_hash = _hash_token(token)
    new_hash = await asyncio.to_thread(hash_password, pw) if needs_rehash(stored) else None

    def _mutate(d):
        sessions = d.setdefault("sessions", {})
        ttl = d.get("panel_settings", {}).get("session_ttl", 86400)
        cutoff = time.time() - ttl
        for k in [k for k, v in sessions.items() if v.get("created", 0) <= cutoff]:
            del sessions[k]
        sessions[token_hash] = {"created": time.time()}
        if new_hash:
            d["admin_password_hash"] = new_hash
        return ttl

    session_ttl = await asyncio.to_thread(update_panel_db, _mutate)
    with _login_lock:
        _login_attempts.pop(client_ip, None)

    resp = JSONResponse({"ok": True})
    _set_session_cookie(resp, token, session_ttl, request_is_secure(request))
    return resp


@app.post("/api/logout")
async def logout(request: Request):
    token = request.cookies.get("tt_session")
    if token:
        def _mutate(d):
            d.get("sessions", {}).pop(_hash_token(token), None)

        await asyncio.to_thread(update_panel_db, _mutate)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("tt_session", path="/")
    return resp


@app.get("/api/auth-status")
async def auth_status(request: Request):
    db = await asyncio.to_thread(load_panel_db)
    authed = await asyncio.to_thread(check_session, request)
    return {
        "authenticated": authed,
        "setup_required": not db.get("admin_password_hash") and not setup_locked(),
        "setup_locked": setup_locked(),
        "min_password_len": MIN_PASSWORD_LEN,
    }


@app.post("/api/change-password")
async def change_admin_password(request: Request):
    await require_auth(request)
    body = await request.json()
    current = body.get("current_password", "")
    pw = body.get("password", "")
    if len(pw) < MIN_PASSWORD_LEN:
        raise HTTPException(400, "Password must be at least %d characters" % MIN_PASSWORD_LEN)
    db = await asyncio.to_thread(load_panel_db)
    stored = db.get("admin_password_hash", "")
    # Always required: a stolen session must not be enough to lock the owner out.
    if not stored or not await asyncio.to_thread(verify_password, current, stored):
        raise HTTPException(401, "Current password is wrong")
    new_hash = await asyncio.to_thread(hash_password, pw)

    def _mutate(d):
        d["admin_password_hash"] = new_hash
        d["sessions"] = {}

    await asyncio.to_thread(update_panel_db, _mutate)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("tt_session", path="/")
    return resp
