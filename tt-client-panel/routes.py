import asyncio
import secrets
import subprocess
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import config
from config import SERVICE_NAME, logger
from auth import (
    load_panel_db, save_panel_db, hash_password, verify_password,
    check_session, require_auth, check_rate_limit, _hash_token,
    _login_lock, _login_attempts,
)
from servers import (
    get_servers, get_server, add_server, update_server, delete_server,
    reorder_servers, activate_server, get_active_server_id, parse_deeplink,
    _check_tun_up,
)
from health import get_health_status, get_net_history
from frontend import FRONTEND_HTML

app = FastAPI(title="TrustTunnel Client Panel", docs_url=None, redoc_url=None)

_static_dir = Path(__file__).parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.post("/api/setup")
async def setup_admin(request: Request):
    db = await asyncio.to_thread(load_panel_db)
    if db.get("admin_password_hash"):
        raise HTTPException(400, "Already configured")
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
    token = secrets.token_hex(32)
    token_hash = _hash_token(token)
    db.setdefault("sessions", {})[token_hash] = {"created": time.time()}
    cutoff = time.time() - 86400
    db["sessions"] = {k: v for k, v in db["sessions"].items() if v.get("created", 0) > cutoff}
    await asyncio.to_thread(save_panel_db, db)
    with _login_lock:
        _login_attempts.pop(client_ip, None)
    resp = JSONResponse({"ok": True})
    resp.set_cookie("tt_session", token, httponly=True, secure=False, max_age=86400, samesite="lax")
    return resp


@app.post("/api/logout")
async def logout(request: Request):
    token = request.cookies.get("tt_session")
    if token:
        db = await asyncio.to_thread(load_panel_db)
        db.get("sessions", {}).pop(_hash_token(token), None)
        await asyncio.to_thread(save_panel_db, db)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("tt_session")
    return resp


@app.get("/api/auth-status")
async def auth_status(request: Request):
    db = await asyncio.to_thread(load_panel_db)
    authed = await asyncio.to_thread(check_session, request)
    return {"authenticated": authed, "setup_required": not db.get("admin_password_hash")}


@app.get("/api/status")
async def status(request: Request):
    await require_auth(request)
    health = await asyncio.to_thread(get_health_status)
    active_id = await asyncio.to_thread(get_active_server_id)
    active = await asyncio.to_thread(get_server, active_id) if active_id else None

    def _uptime():
        try:
            with open("/proc/uptime") as f:
                return int(float(f.read().split()[0]))
        except Exception:
            return 0

    uptime = await asyncio.to_thread(_uptime)
    return {
        "health": health,
        "active_server": active,
        "active_server_id": active_id,
        "uptime_seconds": uptime,
    }


@app.get("/api/servers")
async def list_servers(request: Request):
    await require_auth(request)
    servers = await asyncio.to_thread(get_servers)
    active_id = await asyncio.to_thread(get_active_server_id)
    return {"servers": servers, "active_server_id": active_id}


@app.post("/api/servers")
async def create_server(request: Request):
    await require_auth(request)
    body = await request.json()
    deeplink = body.get("deeplink", "")
    if deeplink:
        parsed = await asyncio.to_thread(parse_deeplink, deeplink)
        if not parsed:
            raise HTTPException(400, "Invalid deeplink")
        for k in ["username", "password", "name"]:
            if k in body and body[k]:
                parsed[k] = body[k]
        server = await asyncio.to_thread(add_server, parsed)
    else:
        if not body.get("hostname"):
            raise HTTPException(400, "Hostname required")
        server = await asyncio.to_thread(add_server, body)
    return {"ok": True, "server": server}


@app.put("/api/servers/{server_id}")
async def edit_server(server_id: str, request: Request):
    await require_auth(request)
    body = await request.json()
    result = await asyncio.to_thread(update_server, server_id, body)
    if not result:
        raise HTTPException(404, "Server not found")
    return {"ok": True, "server": result}


@app.delete("/api/servers/{server_id}")
async def remove_server(server_id: str, request: Request):
    await require_auth(request)
    ok = await asyncio.to_thread(delete_server, server_id)
    if not ok:
        raise HTTPException(404, "Server not found")
    return {"ok": True}


@app.post("/api/servers/{server_id}/activate")
async def do_activate(server_id: str, request: Request):
    await require_auth(request)
    result = await asyncio.to_thread(activate_server, server_id)
    return result


@app.put("/api/servers/reorder")
async def do_reorder(request: Request):
    await require_auth(request)
    body = await request.json()
    order = body.get("order", [])
    await asyncio.to_thread(reorder_servers, order)
    return {"ok": True}


@app.get("/api/net-history")
async def net_history(request: Request, hours: int = 1):
    await require_auth(request)
    import time
    hours = max(1, min(hours, 168))
    cutoff = time.time() - hours * 3600
    data = await asyncio.to_thread(get_net_history)
    filtered = [p for p in data if p.get("ts", 0) >= cutoff]
    max_points = 300
    if len(filtered) > max_points:
        step = len(filtered) // max_points
        filtered = filtered[::step]
    return {"history": filtered}


@app.get("/api/failover-log")
async def failover_log(request: Request):
    await require_auth(request)
    db = await asyncio.to_thread(load_panel_db)
    return {"log": db.get("failover_log", [])}


@app.get("/api/settings")
async def get_settings(request: Request):
    await require_auth(request)
    db = await asyncio.to_thread(load_panel_db)
    return {"settings": db.get("settings", {})}


@app.put("/api/settings")
async def update_settings(request: Request):
    await require_auth(request)
    body = await request.json()
    db = await asyncio.to_thread(load_panel_db)
    settings = db.get("settings", {})
    for key in ["health_check_interval", "auto_failover", "failover_threshold",
                "killswitch_enabled", "vpn_mode", "dns_upstreams", "exclusions", "mtu_size"]:
        if key in body:
            settings[key] = body[key]
    db["settings"] = settings
    await asyncio.to_thread(save_panel_db, db)
    return {"ok": True, "settings": settings}


@app.post("/api/service/{action}")
async def control_service(action: str, request: Request):
    await require_auth(request)
    if action not in ("restart", "stop", "start"):
        raise HTTPException(400, "Invalid action")

    def _run():
        try:
            r = subprocess.run(["systemctl", action, SERVICE_NAME],
                               capture_output=True, text=True, timeout=15)
            return {"ok": r.returncode == 0}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return await asyncio.to_thread(_run)


@app.post("/api/change-password")
async def change_password(request: Request):
    await require_auth(request)
    body = await request.json()
    pw = body.get("password", "")
    if len(pw) < 6:
        raise HTTPException(400, "Min 6 chars")
    db = await asyncio.to_thread(load_panel_db)
    db["admin_password_hash"] = hash_password(pw)
    db["sessions"] = {}
    await asyncio.to_thread(save_panel_db, db)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("tt_session")
    return resp


@app.get("/", response_class=HTMLResponse)
async def index():
    return FRONTEND_HTML
