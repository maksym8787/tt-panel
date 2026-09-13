import asyncio
import time
from datetime import datetime

from fastapi import Request

from auth import require_auth
from collector import fetch_live_metrics, fetch_client_stats, clients_available
from config import STATS_DB, LOG_FILE
from database import get_db
from network import rdns_lookup_cached, enrich_with_geo
from services import (
    parse_credentials, get_service_status, get_cert_days_remaining,
    get_server_ip, get_vps_resources, get_domain, is_reload_pending,
)
from routes import app


_status_cache = {"data": None, "ts": 0}
_STATUS_TTL = 10
# How recently an IP must have connected to count as "online".
ONLINE_WINDOW = 900


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
        # One batched lookup instead of a serial request per IP.
        items = [dict(info, ip=ip) for ip, info in ips.items()]
        enrich_with_geo(items, "ip")
        for item in items:
            ips[item["ip"]]["geo"] = item.get("geo", {})
        return ips

    ips = await asyncio.to_thread(_enrich)
    return {"active_ips": ips}


@app.get("/api/pending-reload")
async def pending_reload_status(request: Request):
    await require_auth(request)
    return {"pending": is_reload_pending()}


@app.get("/api/status")
async def server_status(request: Request):
    await require_auth(request)
    now = time.time()
    if _status_cache["data"] and (now - _status_cache["ts"]) < _STATUS_TTL:
        return _status_cache["data"]
    status, cert, live, clients, vps, ip = await asyncio.gather(
        asyncio.to_thread(get_service_status),
        asyncio.to_thread(get_cert_days_remaining),
        asyncio.to_thread(fetch_live_metrics),
        asyncio.to_thread(parse_credentials),
        asyncio.to_thread(get_vps_resources),
        asyncio.to_thread(get_server_ip),
    )
    result = {
        "service": status, "domain": get_domain(), "certificate": cert,
        "users_count": len(clients), "ip": ip,
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
    _status_cache["data"] = result
    _status_cache["ts"] = now
    return result


@app.get("/api/monitoring/history")
async def monitoring_history(request: Request, hours: int = 24):
    await require_auth(request)
    hours = max(1, min(hours, 8760))

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
async def monitoring_traffic(request: Request, days: int = 0, hours: int = 0):
    await require_auth(request)
    # Same ceiling as the other monitoring endpoints, so the UI's "1y" period
    # doesn't silently come back with only 30 days of traffic.
    if hours > 0:
        since_sec = max(1, min(hours, 8760)) * 3600
    elif days > 0:
        since_sec = max(1, min(days, 365)) * 86400
    else:
        since_sec = 7 * 86400

    def _query():
        since = int(time.time()) - since_sec
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
    hours = max(1, min(hours, 8760))
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
        domain_counts = {}
        for dst, cnt in raw_dst:
            resolved = rdns_lookup_cached(dst) if dst else dst
            domain = resolved.split(":")[0] if resolved else dst
            domain_counts[domain] = domain_counts.get(domain, 0) + cnt
        top_dst = [{"dst": d, "count": ct}
                   for d, ct in sorted(domain_counts.items(), key=lambda x: -x[1])[:20]]
        return rows, top_dst, unique_ips

    rows, top_dst, unique_ips = await asyncio.to_thread(_query)
    return {"connections": rows, "top_destinations": top_dst, "unique_ips": unique_ips}


@app.get("/api/monitoring/conn-timeline")
async def monitoring_conn_timeline(request: Request, hours: int = 24):
    await require_auth(request)
    hours = max(1, min(hours, 8760))

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
        # TrustTunnel's disconnect log lines carry only a client id, never the
        # client IP, so a connect/disconnect pairing per IP is not possible.
        # "Online" therefore means: this IP opened a connection very recently.
        since = int(time.time()) - ONLINE_WINDOW
        since_1h = int(time.time()) - 3600
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            c = conn.cursor()
            c.execute("""
                SELECT client_ip, MAX(ts) as last_seen,
                       GROUP_CONCAT(DISTINCT user_agent) as agents,
                       GROUP_CONCAT(DISTINCT destination) as dests
                FROM connections
                WHERE ts > ? AND client_ip IS NOT NULL AND event='connect'
                GROUP BY client_ip
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


@app.get("/api/monitoring/per-user")
async def monitoring_per_user(request: Request, hours: int = 24):
    """Per-user traffic and sessions from the endpoint's /clients data.

    Returns available=false when per_client_metrics is off, so the UI can
    explain how to turn it on instead of showing an empty table.
    """
    await require_auth(request)
    hours = max(1, min(hours, 8760))
    live = await asyncio.to_thread(fetch_client_stats)
    available = clients_available()

    def _query():
        since = int(time.time()) - hours * 3600
        with get_db() as conn:
            conn.execute("PRAGMA busy_timeout=5000")
            c = conn.cursor()
            c.execute("""
                SELECT username,
                       SUM(inbound_bytes), SUM(outbound_bytes),
                       MAX(sessions_max), MAX(last_seen)
                FROM client_usage_hourly
                WHERE hour_ts >= ?
                GROUP BY username
            """, (since,))
            return {r[0]: {"inbound": r[1] or 0, "outbound": r[2] or 0,
                           "peak_sessions": r[3] or 0, "last_seen": r[4] or 0}
                    for r in c.fetchall()}

    history = await asyncio.to_thread(_query)

    users = {}
    for username, agg in history.items():
        users[username] = dict(agg, username=username, sessions=0, ip=None)
    for entry in (live or []):
        username = entry.get("username")
        if not username:
            continue
        row = users.setdefault(username, {"username": username, "inbound": 0, "outbound": 0,
                                          "peak_sessions": 0, "last_seen": 0})
        row["sessions"] = int(entry.get("sessions") or 0)
        row["ip"] = entry.get("ip")
        row["total_inbound"] = int(entry.get("inbound") or 0)
        row["total_outbound"] = int(entry.get("outbound") or 0)

    rows = sorted(users.values(),
                  key=lambda u: (u.get("inbound", 0) + u.get("outbound", 0)), reverse=True)
    if rows:
        await asyncio.to_thread(enrich_with_geo, rows, "ip")
    return {"available": bool(available), "hours": hours, "users": rows}


@app.get("/api/monitoring/db-size")
async def db_size(request: Request):
    await require_auth(request)

    def _query():
        size = STATS_DB.stat().st_size if STATS_DB.exists() else 0
        log_size = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
        return {"db_bytes": size, "db_mb": round(size / 1024 / 1024, 2), "log_bytes": log_size, "log_mb": round(log_size / 1024 / 1024, 2)}

    return await asyncio.to_thread(_query)
