import asyncio
import re
import secrets
import subprocess
import time
from datetime import datetime

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import config
from config import LOG_FILE, PANEL_DIR, STATS_DB, VPN_TOML, RULES_TOML, HOSTS_TOML, logger
from auth import (
    load_panel_db, save_panel_db, hash_password, verify_password,
    check_session, require_auth, check_rate_limit, _hash_token,
    _login_lock, _login_attempts,
)
from services import (
    parse_credentials, write_credentials, get_domain, export_client_config,
    get_service_status, get_cert_days_remaining, get_server_ip,
    generate_password, _do_cert_renewal, schedule_reload, apply_reload_now,
    is_reload_pending, get_vps_resources,
)
from collector import fetch_live_metrics
from database import get_db
from network import rdns_lookup, rdns_lookup_cached, geo_lookup, enrich_with_geo
from frontend import FRONTEND_HTML

app = FastAPI(title="TrustTunnel Admin", docs_url=None, redoc_url=None)

_static_dir = Path(__file__).parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


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
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    return response


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


@app.get("/api/users")
async def list_users(request: Request):
    await require_auth(request)
    clients = await asyncio.to_thread(parse_credentials)
    return {"users": [{"username": c["username"], "password": c.get("password", "")} for c in clients]}


@app.post("/api/users")
async def add_user(request: Request):
    await require_auth(request)
    body = await request.json()
    username = body.get("username", "").strip()
    password = body.get("password", "").strip() or generate_password()
    if not username:
        raise HTTPException(400, "Username required")
    if not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', username):
        raise HTTPException(400, "Username must be 1-64 chars: letters, digits, hyphens, underscores")
    clients = await asyncio.to_thread(parse_credentials)
    if any(c["username"] == username for c in clients):
        raise HTTPException(400, "User exists")
    clients.append({"username": username, "password": password})
    await asyncio.to_thread(write_credentials, clients)
    schedule_reload()
    return {"ok": True, "username": username, "password": password}


@app.put("/api/users/{username}")
async def update_user(username: str, request: Request):
    await require_auth(request)
    body = await request.json()
    pw = body.get("password", "").strip()
    if not pw:
        raise HTTPException(400, "Password required")
    clients = await asyncio.to_thread(parse_credentials)
    found = False
    for c in clients:
        if c["username"] == username:
            c["password"] = pw
            found = True
            break
    if not found:
        raise HTTPException(404, "Not found")
    await asyncio.to_thread(write_credentials, clients)
    schedule_reload()
    return {"ok": True}


@app.delete("/api/users/{username}")
async def delete_user(username: str, request: Request):
    await require_auth(request)
    clients = await asyncio.to_thread(parse_credentials)
    new = [c for c in clients if c["username"] != username]
    if len(new) == len(clients):
        raise HTTPException(404, "Not found")
    await asyncio.to_thread(write_credentials, new)
    schedule_reload()
    return {"ok": True}


@app.get("/api/users/{username}/config")
async def get_user_config(username: str, request: Request, fmt: str = "toml"):
    await require_auth(request)
    if fmt not in ("toml", "json", "deeplink"):
        raise HTTPException(400, "Invalid format")
    clients = await asyncio.to_thread(parse_credentials)
    if not any(c["username"] == username for c in clients):
        raise HTTPException(404)
    cfg = await asyncio.to_thread(export_client_config, username, fmt)
    return {"config": cfg, "format": fmt}


@app.get("/api/active-ips")
async def active_ips(request: Request):
    await require_auth(request)

    def _query():
        since = int(time.time()) - 1800
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            c = conn.cursor()
            c.execute("""
                SELECT client_ip, MAX(ts) as last_seen,
                       GROUP_CONCAT(DISTINCT user_agent) as agents,
                       COUNT(*) as conn_count
                FROM connections
                WHERE ts > ? AND client_ip IS NOT NULL AND event='connect'
                GROUP BY client_ip
                ORDER BY last_seen DESC
            """, (since,))
            ips = {}
            for row in c.fetchall():
                ips[row[0]] = {"last_seen": row[1], "user_agent": (row[2] or "").split(",")[0], "connections": row[3]}
        return ips

    ips = await asyncio.to_thread(_query)

    def _enrich():
        for ip, info in ips.items():
            geo = geo_lookup(ip)
            info["geo"] = {k: v for k, v in geo.items() if k != "_ts"}
        return ips

    ips = await asyncio.to_thread(_enrich)
    return {"active_ips": ips}


@app.get("/api/pending-reload")
async def pending_reload_status(request: Request):
    await require_auth(request)
    return {"pending": is_reload_pending()}


@app.post("/api/apply-reload")
async def apply_reload(request: Request):
    await require_auth(request)
    await asyncio.to_thread(apply_reload_now)
    return {"ok": True}


@app.get("/api/status")
async def server_status(request: Request):
    await require_auth(request)
    status = await asyncio.to_thread(get_service_status)
    cert = await asyncio.to_thread(get_cert_days_remaining)
    live = await asyncio.to_thread(fetch_live_metrics)
    clients = await asyncio.to_thread(parse_credentials)
    vps = await asyncio.to_thread(get_vps_resources)
    return {
        "service": status, "domain": get_domain(), "certificate": cert,
        "users_count": len(clients), "ip": await asyncio.to_thread(get_server_ip),
        "vps": vps,
        "live": {
            "sessions": live.get("client_sessions", 0),
            "inbound_bytes": live.get("inbound_traffic_bytes", 0),
            "outbound_bytes": live.get("outbound_traffic_bytes", 0),
            "tcp_sockets": live.get("outbound_tcp_sockets", 0),
            "udp_sockets": live.get("outbound_udp_sockets", 0),
            "memory_mb": round(live.get("process_resident_memory_bytes", 0) / 1024 / 1024, 1),
            "cpu_seconds": round(live.get("process_cpu_seconds_total", 0), 2),
            "open_fds": live.get("process_open_fds", 0),
        },
    }


@app.get("/api/monitoring/history")
async def monitoring_history(request: Request, hours: int = 24):
    await require_auth(request)
    hours = max(1, min(hours, 720))

    def _query():
        since = int(time.time()) - hours * 3600
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            c = conn.cursor()
            c.execute("""SELECT ts, sessions, inbound_bytes, outbound_bytes, memory_bytes, cpu_seconds
                FROM metrics_snapshots WHERE ts > ? ORDER BY ts""", (since,))
            snapshots = [{"ts": r[0], "sessions": r[1], "in": r[2], "out": r[3], "mem": r[4], "cpu": r[5]} for r in c.fetchall()]
            max_points = 360
            if len(snapshots) > max_points:
                step = len(snapshots) // max_points
                snapshots = snapshots[::step]
        return snapshots

    snapshots = await asyncio.to_thread(_query)
    return {"snapshots": snapshots, "hours": hours}


@app.get("/api/monitoring/traffic")
async def monitoring_traffic(request: Request, days: int = 7):
    await require_auth(request)
    days = max(1, min(days, 30))

    def _query():
        since = int(time.time()) - days * 86400
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            c = conn.cursor()
            c.execute("""SELECT hour_ts, inbound_bytes, outbound_bytes, sessions_max
                FROM traffic_hourly WHERE hour_ts > ? ORDER BY hour_ts""", (since,))
            return [{"ts": r[0], "in": r[1], "out": r[2], "peak": r[3]} for r in c.fetchall()]

    hourly = await asyncio.to_thread(_query)
    return {"hourly": hourly, "days": days}


@app.get("/api/monitoring/connections")
async def monitoring_connections(request: Request, hours: int = 24, limit: int = 200):
    await require_auth(request)
    hours = max(1, min(hours, 720))
    limit = max(1, min(limit, 1000))

    def _query():
        since = int(time.time()) - hours * 3600
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT ts, client_ip, user_agent, destination, event
                FROM connections WHERE ts > ? ORDER BY ts DESC LIMIT ?""", (since, limit))
            rows = [{"ts": r[0], "ip": r[1], "ua": r[2], "dst": rdns_lookup_cached(r[3]) if r[3] else r[3], "event": r[4]} for r in c.fetchall()]
            c.execute("""SELECT destination, COUNT(*) as cnt FROM connections
                WHERE ts > ? AND destination IS NOT NULL GROUP BY destination ORDER BY cnt DESC LIMIT 50""", (since,))
            raw_dst = c.fetchall()
            c.execute("SELECT DISTINCT client_ip FROM connections WHERE ts > ? AND client_ip IS NOT NULL", (since,))
            unique_ips = [r[0] for r in c.fetchall()]
            c.execute("""SELECT client_ip, COUNT(*) as cnt, MAX(ts) as last_seen,
                GROUP_CONCAT(DISTINCT user_agent) as agents
                FROM connections WHERE ts > ? AND client_ip IS NOT NULL AND event='connect'
                GROUP BY client_ip ORDER BY cnt DESC LIMIT 20""", (since,))
            per_client = [{"ip": r[0], "connections": r[1], "last_seen": r[2],
                          "user_agent": (r[3] or "").split(",")[0]} for r in c.fetchall()]
            c.execute("""SELECT destination FROM connections
                WHERE ts > ? AND destination IS NOT NULL""", (since,))
            all_dsts = [r[0] for r in c.fetchall()]
        domain_counts = {}
        for dst, cnt in raw_dst:
            resolved = rdns_lookup_cached(dst) if dst else dst
            domain = resolved.split(":")[0] if resolved else dst
            domain_counts[domain] = domain_counts.get(domain, 0) + cnt
        top_dst = sorted(domain_counts.items(), key=lambda x: -x[1])[:20]
        top_dst = [{"dst": d, "count": c} for d, c in top_dst]
        port_counts = {}
        for d in all_dsts:
            port = d.split(":")[-1] if ":" in d else "?"
            port_counts[port] = port_counts.get(port, 0) + 1
        top_ports = sorted(port_counts.items(), key=lambda x: -x[1])[:10]
        top_ports = [{"port": p, "count": c} for p, c in top_ports]
        return rows, top_dst, unique_ips, per_client, top_ports

    rows, top_dst, unique_ips, per_client, top_ports = await asyncio.to_thread(_query)
    per_client = await asyncio.to_thread(enrich_with_geo, per_client, "ip")
    return {"connections": rows, "top_destinations": top_dst, "unique_ips": unique_ips,
            "per_client": per_client, "top_ports": top_ports}


@app.get("/api/monitoring/conn-timeline")
async def monitoring_conn_timeline(request: Request, hours: int = 24):
    await require_auth(request)
    hours = max(1, min(hours, 720))

    def _query():
        since = int(time.time()) - hours * 3600
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            c = conn.cursor()
            c.execute("""
                SELECT (ts / 3600) * 3600 as hour_ts,
                       COUNT(*) as total_conns,
                       COUNT(DISTINCT client_ip) as unique_ips
                FROM connections
                WHERE ts > ? AND event='connect'
                GROUP BY hour_ts ORDER BY hour_ts
            """, (since,))
            return [{"ts": r[0], "connections": r[1], "unique_ips": r[2]} for r in c.fetchall()]

    data = await asyncio.to_thread(_query)
    return {"timeline": data}


@app.get("/api/monitoring/online")
async def monitoring_online(request: Request):
    await require_auth(request)
    live = await asyncio.to_thread(fetch_live_metrics)
    live_sessions = live.get("client_sessions", 0)

    def _query():
        since = int(time.time()) - 1800
        since_1h = int(time.time()) - 3600
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            c = conn.cursor()
            c.execute("""
                SELECT client_ip, MAX(ts) as last_seen,
                       GROUP_CONCAT(DISTINCT user_agent) as agents,
                       GROUP_CONCAT(DISTINCT destination) as dests
                FROM connections
                WHERE ts > ? AND client_ip IS NOT NULL
                GROUP BY client_ip
                HAVING MAX(CASE WHEN event='connect' OR event='tunnel' THEN ts ELSE 0 END) >=
                       MAX(CASE WHEN event='disconnect' THEN ts ELSE 0 END)
                ORDER BY last_seen DESC
            """, (since,))
            users = []
            for row in c.fetchall():
                agents = [a for a in (row[2] or "").split(",") if a]
                dests = [d for d in (row[3] or "").split(",") if d]
                users.append({"ip": row[0], "last_seen": row[1], "user_agents": agents[:3], "destinations": dests[:5]})
            c.execute("""
                SELECT client_ip, MAX(ts) as last_seen,
                       GROUP_CONCAT(DISTINCT user_agent) as agents
                FROM connections
                WHERE ts > ? AND client_ip IS NOT NULL
                GROUP BY client_ip
                ORDER BY last_seen DESC LIMIT 50
            """, (since_1h,))
            recent = []
            for row in c.fetchall():
                agents = [a for a in (row[2] or "").split(",") if a]
                recent.append({"ip": row[0], "last_seen": row[1], "user_agents": agents[:3]})
        return users, recent

    users, recent = await asyncio.to_thread(_query)

    def _enrich():
        enrich_with_geo(users, "ip")
        enrich_with_geo(recent, "ip")

    await asyncio.to_thread(_enrich)
    return {"live_sessions": live_sessions, "online_users": users, "recently_active": recent}


@app.get("/api/monitoring/summary")
async def monitoring_summary(request: Request):
    await require_auth(request)

    def _query():
        now = int(time.time())
        local_now = datetime.now()
        today_start = int(local_now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        week_start = now - 7 * 86400
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            c = conn.cursor()

            def sum_deltas(since):
                try:
                    c.execute("""
                        WITH deltas AS (
                            SELECT
                                inbound_bytes - LAG(inbound_bytes) OVER (ORDER BY ts) AS d_in,
                                outbound_bytes - LAG(outbound_bytes) OVER (ORDER BY ts) AS d_out
                            FROM metrics_snapshots WHERE ts >= ?
                        )
                        SELECT COALESCE(SUM(CASE WHEN d_in > 0 THEN d_in ELSE 0 END), 0),
                               COALESCE(SUM(CASE WHEN d_out > 0 THEN d_out ELSE 0 END), 0)
                        FROM deltas
                    """, (since,))
                    row = c.fetchone()
                    return row[0], row[1]
                except Exception:
                    c.execute("""SELECT inbound_bytes, outbound_bytes FROM metrics_snapshots
                        WHERE ts >= ? ORDER BY ts""", (since,))
                    rows = c.fetchall()
                    total_in, total_out = 0, 0
                    for i in range(1, len(rows)):
                        d_in = (rows[i][0] or 0) - (rows[i - 1][0] or 0)
                        d_out = (rows[i][1] or 0) - (rows[i - 1][1] or 0)
                        if d_in > 0:
                            total_in += d_in
                        if d_out > 0:
                            total_out += d_out
                    return total_in, total_out

            today_in, today_out = sum_deltas(today_start)
            week_in, week_out = sum_deltas(week_start)
            c.execute("SELECT MAX(sessions) FROM metrics_snapshots WHERE ts >= ?", (today_start,))
            peak_today = (c.fetchone() or [0])[0] or 0
            c.execute("SELECT MAX(sessions) FROM metrics_snapshots WHERE ts >= ?", (week_start,))
            peak_week = (c.fetchone() or [0])[0] or 0
            c.execute("SELECT COUNT(*) FROM connections WHERE ts >= ? AND event='connect'", (today_start,))
            conns_today = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM connections WHERE ts >= ? AND event='connect'", (week_start,))
            conns_week = c.fetchone()[0]
        return {
            "today": {"inbound": today_in, "outbound": today_out, "peak_sessions": peak_today, "connections": conns_today},
            "week": {"inbound": week_in, "outbound": week_out, "peak_sessions": peak_week, "connections": conns_week},
        }

    return await asyncio.to_thread(_query)


@app.get("/api/monitoring/db-size")
async def db_size(request: Request):
    await require_auth(request)

    def _query():
        size = STATS_DB.stat().st_size if STATS_DB.exists() else 0
        log_size = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
        return {"db_bytes": size, "db_mb": round(size / 1024 / 1024, 2), "log_bytes": log_size, "log_mb": round(log_size / 1024 / 1024, 2)}

    return await asyncio.to_thread(_query)


@app.post("/api/cert/renew")
async def renew_certificate(request: Request):
    await require_auth(request)
    domain = get_domain()
    return await asyncio.to_thread(_do_cert_renewal, domain)


@app.get("/api/settings")
async def get_settings(request: Request):
    await require_auth(request)

    def _read():
        return {
            "vpn_toml": VPN_TOML.read_text() if VPN_TOML.exists() else "",
            "rules_toml": RULES_TOML.read_text() if RULES_TOML.exists() else "",
            "hosts_toml": HOSTS_TOML.read_text() if HOSTS_TOML.exists() else "",
        }

    return await asyncio.to_thread(_read)


@app.put("/api/settings/{filename}")
async def update_settings(filename: str, request: Request):
    await require_auth(request)
    allowed = {"vpn_toml": VPN_TOML, "rules_toml": RULES_TOML}
    if filename not in allowed:
        raise HTTPException(400, "Cannot edit")
    body = await request.json()

    def _write():
        target = allowed[filename]
        if target.exists():
            target.with_suffix(target.suffix + ".bak").write_text(target.read_text())
        target.write_text(body.get("content", ""))

    await asyncio.to_thread(_write)
    return {"ok": True}


@app.get("/api/logs")
async def get_logs(request: Request, lines: int = 100):
    await require_auth(request)
    lines = max(1, min(lines, 1000))

    def _read():
        try:
            if LOG_FILE.exists() and LOG_FILE.stat().st_size > 0:
                r = subprocess.run(["tail", "-n", str(lines), str(LOG_FILE)], capture_output=True, text=True, timeout=10)
                if r.stdout.strip():
                    return r.stdout
            r2 = subprocess.run(
                ["journalctl", "-u", "trusttunnel", "--no-pager", "-q", "-n", str(lines)],
                capture_output=True, text=True, timeout=10
            )
            if r2.returncode == 0 and r2.stdout.strip():
                return r2.stdout
            return "(no log data available)"
        except Exception as e:
            logger.error("Log read error: %s", e)
            return "Error reading logs"

    return {"logs": await asyncio.to_thread(_read)}


@app.post("/api/service/{action}")
async def control_service(action: str, request: Request):
    await require_auth(request)
    if action not in ("restart", "stop", "start", "reload"):
        raise HTTPException(400)

    def _run():
        try:
            r = subprocess.run(["systemctl", action, "trusttunnel"], capture_output=True, text=True, timeout=15)
            return {"ok": r.returncode == 0, "output": "Service action completed" if r.returncode == 0 else "Service action failed"}
        except Exception as e:
            logger.error("Service %s error: %s", action, e)
            raise HTTPException(500, "Service action failed")

    return await asyncio.to_thread(_run)


@app.post("/api/change-password")
async def change_admin_password(request: Request):
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
