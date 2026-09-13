import asyncio
import secrets
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import config
from config import SERVICE_NAME, logger
from auth import (
    load_panel_db, update_panel_db, hash_password, verify_password,
    check_session, require_auth, check_rate_limit, _hash_token, needs_rehash,
    setup_locked, request_is_secure, session_ttl, MIN_PASSWORD_LEN,
    _login_lock, _login_attempts,
)
from servers import (
    get_servers, get_server, add_server, update_server, delete_server,
    reorder_servers, activate_server, get_active_server_id, parse_deeplink,
    _check_tun_up,
)
from health import get_health_status, get_net_history
from frontend import FRONTEND_HTML, APP_JS, APP_CSS

app = FastAPI(title="TrustTunnel Client Panel", docs_url=None, redoc_url=None)

_static_dir = Path(__file__).parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@app.middleware("http")
async def csrf_guard(request: Request, call_next):
    """Second line of defence behind SameSite for cookie-authenticated writes."""
    if request.method not in _SAFE_METHODS:
        site = request.headers.get("sec-fetch-site")
        if site is not None:
            if site not in ("same-origin", "none"):
                return JSONResponse({"detail": "Cross-site request blocked"}, status_code=403)
        else:
            origin = request.headers.get("origin")
            if origin and urlsplit(origin).netloc != request.headers.get("host", ""):
                return JSONResponse({"detail": "Cross-site request blocked"}, status_code=403)
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if config._ssl_configured:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "font-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "object-src 'none'"
    )
    return response


def _set_session_cookie(resp, token, ttl, secure):
    resp.set_cookie("tt_session", token, httponly=True, secure=secure,
                    max_age=ttl, samesite="strict" if secure else "lax", path="/")


def _int_field(body, key, lo, hi):
    try:
        return max(lo, min(int(body[key]), hi))
    except (ValueError, TypeError):
        raise HTTPException(400, "%s must be an integer between %d and %d" % (key, lo, hi))


def _str_list(body, key, max_items=64, max_len=255):
    value = body[key]
    if not isinstance(value, list):
        raise HTTPException(400, "%s must be a list" % key)
    if len(value) > max_items:
        raise HTTPException(400, "%s: too many entries (max %d)" % (key, max_items))
    out = []
    for item in value:
        if not isinstance(item, str):
            raise HTTPException(400, "%s must contain only strings" % key)
        item = item.strip()
        if len(item) > max_len:
            raise HTTPException(400, "%s: entry too long" % key)
        if item:
            out.append(item)
    return out


@app.post("/api/setup")
async def setup_admin(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)
    if setup_locked():
        raise HTTPException(409, "Panel database was lost or corrupted. Setup is locked; "
                                 "restore panel.json or remove panel.corrupt on the server.")
    db = await asyncio.to_thread(load_panel_db)
    if db.get("admin_password_hash"):
        raise HTTPException(400, "Already configured")
    body = await request.json()
    pw = body.get("password", "")
    if len(pw) < MIN_PASSWORD_LEN:
        raise HTTPException(400, "Password must be at least %d characters" % MIN_PASSWORD_LEN)
    new_hash = await asyncio.to_thread(hash_password, pw)

    def _mutate(d):
        if d.get("admin_password_hash"):
            raise HTTPException(400, "Already configured")
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
        ttl = session_ttl(d)
        cutoff = time.time() - ttl
        for k in [k for k, v in sessions.items() if v.get("created", 0) <= cutoff]:
            del sessions[k]
        sessions[token_hash] = {"created": time.time()}
        if new_hash:
            d["admin_password_hash"] = new_hash
        return ttl

    ttl = await asyncio.to_thread(update_panel_db, _mutate)
    with _login_lock:
        _login_attempts.pop(client_ip, None)
    resp = JSONResponse({"ok": True})
    _set_session_cookie(resp, token, ttl, request_is_secure(request))
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
async def change_password(request: Request):
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
    db = await asyncio.to_thread(load_panel_db)
    return {
        "health": health,
        "active_server": active,
        "active_server_id": active_id,
        "uptime_seconds": uptime,
        "on_backup": db.get("on_backup", False),
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
    try:
        if deeplink:
            if not str(deeplink).strip().startswith("tt://"):
                raise HTTPException(400, "A deeplink must start with tt://")
            parsed = await asyncio.to_thread(parse_deeplink, deeplink)
            if not parsed:
                raise HTTPException(400, "Could not parse this deeplink")
            for k in ("username", "password", "name"):
                if body.get(k):
                    parsed[k] = body[k]
            server = await asyncio.to_thread(add_server, parsed)
        else:
            if not body.get("hostname"):
                raise HTTPException(400, "Hostname required")
            server = await asyncio.to_thread(add_server, body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "server": server}


@app.put("/api/servers/reorder")
async def do_reorder(request: Request):
    await require_auth(request)
    body = await request.json()
    order = body.get("order", [])
    if not isinstance(order, list):
        raise HTTPException(400, "order must be a list")
    return await asyncio.to_thread(reorder_servers, order)


@app.put("/api/servers/{server_id}")
async def edit_server(server_id: str, request: Request):
    await require_auth(request)
    body = await request.json()
    try:
        result = await asyncio.to_thread(update_server, server_id, body)
    except ValueError as e:
        raise HTTPException(400, str(e))
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
    return await asyncio.to_thread(activate_server, server_id, True)


@app.get("/api/net-history")
async def net_history(request: Request, hours: int = 1):
    await require_auth(request)
    hours = max(1, min(hours, 8760))
    cutoff = time.time() - hours * 3600
    data = await asyncio.to_thread(get_net_history)
    filtered = [p for p in data if p.get("ts", 0) >= cutoff]
    max_points = 300
    if len(filtered) > max_points:
        filtered = filtered[::len(filtered) // max_points]
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
    updates = {}
    if "health_check_interval" in body:
        updates["health_check_interval"] = _int_field(body, "health_check_interval", 10, 300)
    if "auto_failover" in body:
        updates["auto_failover"] = bool(body["auto_failover"])
    if "failover_threshold" in body:
        updates["failover_threshold"] = _int_field(body, "failover_threshold", 1, 10)
    if "killswitch_enabled" in body:
        updates["killswitch_enabled"] = bool(body["killswitch_enabled"])
    if "vpn_mode" in body:
        if body["vpn_mode"] not in ("general", "selective"):
            raise HTTPException(400, "vpn_mode must be 'general' or 'selective'")
        updates["vpn_mode"] = body["vpn_mode"]
    if "dns_upstreams" in body:
        updates["dns_upstreams"] = _str_list(body, "dns_upstreams")
    if "exclusions" in body:
        updates["exclusions"] = _str_list(body, "exclusions", max_items=512)
    if "mtu_size" in body:
        updates["mtu_size"] = _int_field(body, "mtu_size", 1200, 9000)
    if "activate_timeout" in body:
        updates["activate_timeout"] = _int_field(body, "activate_timeout", 3, 30)
    if "failover_timeout" in body:
        updates["failover_timeout"] = _int_field(body, "failover_timeout", 3, 15)
    if "session_ttl" in body:
        updates["session_ttl"] = _int_field(body, "session_ttl", 300, 604800)

    def _mutate(d):
        settings = d.setdefault("settings", {})
        settings.update(updates)
        return dict(settings)

    settings = await asyncio.to_thread(update_panel_db, _mutate)
    return {"ok": True, "settings": settings}


@app.post("/api/service/{action}")
async def control_service(action: str, request: Request):
    await require_auth(request)
    if action not in ("restart", "stop", "start"):
        raise HTTPException(400, "Invalid action")

    def _run():
        try:
            r = subprocess.run(["systemctl", action, SERVICE_NAME],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                return {"ok": True}
            err = (r.stderr or r.stdout or "").strip()[:300] or ("exit code %d" % r.returncode)
            logger.error("systemctl %s %s failed: %s", action, SERVICE_NAME, err)
            return {"ok": False, "error": err}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "systemctl %s timed out" % action}
        except Exception as e:
            logger.error("systemctl %s error: %s", action, e)
            return {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}

    return await asyncio.to_thread(_run)


@app.get("/app.js")
async def app_js():
    return Response(content=APP_JS, media_type="application/javascript; charset=utf-8")


@app.get("/app.css")
async def app_css():
    return Response(content=APP_CSS, media_type="text/css; charset=utf-8")


@app.get("/favicon.ico")
async def favicon():
    fav = _static_dir / "favicon.png"
    if fav.exists():
        return FileResponse(str(fav), media_type="image/png")
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
async def index():
    return FRONTEND_HTML
