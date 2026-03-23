import asyncio
import secrets
import time

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

import config
from auth import (
    load_panel_db, save_panel_db, hash_password, verify_password,
    check_session, require_auth, check_rate_limit, _hash_token,
    _login_lock, _login_attempts,
)
from routes import app


@app.post("/api/setup")
async def setup_admin(request: Request):
    db = await asyncio.to_thread(load_panel_db)
    if db.get("admin_password_hash"):
        raise HTTPException(400, "Already configured. Use change-password instead.")
    body = await request.json()
    pw = body.get("password", "")
    if len(pw) < 6:
        raise HTTPException(400, "Min 6 chars")
    db["admin_password_hash"] = hash_password(pw)
    await asyncio.to_thread(save_panel_db, db)
    return {"ok": True}


@app.post("/api/login")
async def login(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)
    db = await asyncio.to_thread(load_panel_db)
    body = await request.json()
    pw = body.get("password", "")
    if not db.get("admin_password_hash"):
        raise HTTPException(400, "Setup required")
    if not verify_password(pw, db["admin_password_hash"]):
        raise HTTPException(401, "Bad password")
    if '$' not in db["admin_password_hash"]:
        db["admin_password_hash"] = hash_password(pw)
    token = secrets.token_hex(32)
    token_hash = _hash_token(token)
    db.setdefault("sessions", {})[token_hash] = {"created": time.time()}
    cutoff = time.time() - db.get("panel_settings", {}).get("session_ttl", 86400)
    db["sessions"] = {k: v for k, v in db["sessions"].items() if v["created"] > cutoff}
    await asyncio.to_thread(save_panel_db, db)
    with _login_lock:
        _login_attempts.pop(client_ip, None)
    session_ttl = db.get("panel_settings", {}).get("session_ttl", 86400)
    resp = JSONResponse({"ok": True})
    resp.set_cookie("tt_session", token, httponly=True, secure=config._ssl_configured, max_age=session_ttl, samesite="strict" if config._ssl_configured else "lax")
    return resp


@app.post("/api/logout")
async def logout(request: Request):
    token = request.cookies.get("tt_session")
    if token:
        db = await asyncio.to_thread(load_panel_db)
        db.get("sessions", {}).pop(_hash_token(token), None)
        db.get("sessions", {}).pop(token, None)
        await asyncio.to_thread(save_panel_db, db)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("tt_session")
    return resp


@app.get("/api/auth-status")
async def auth_status(request: Request):
    db = await asyncio.to_thread(load_panel_db)
    authed = await asyncio.to_thread(check_session, request)
    return {"authenticated": authed, "setup_required": not db.get("admin_password_hash")}


@app.post("/api/change-password")
async def change_admin_password(request: Request):
    await require_auth(request)
    body = await request.json()
    current = body.get("current_password", "")
    pw = body.get("password", "")
    if len(pw) < 6:
        raise HTTPException(400, "Min 6 chars")
    db = await asyncio.to_thread(load_panel_db)
    if current and not verify_password(current, db.get("admin_password_hash", "")):
        raise HTTPException(401, "Current password is wrong")
    db["admin_password_hash"] = hash_password(pw)
    db["sessions"] = {}
    await asyncio.to_thread(save_panel_db, db)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("tt_session")
    return resp
