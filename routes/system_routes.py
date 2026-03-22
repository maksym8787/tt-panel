import asyncio
import subprocess

from fastapi import HTTPException, Request

from auth import load_panel_db, save_panel_db, require_auth
from config import VPN_TOML, RULES_TOML, HOSTS_TOML, LOG_FILE, logger
from services import (
    get_domain, _do_cert_renewal, apply_reload_now, _log_restart,
)
from routes import app


@app.post("/api/apply-reload")
async def apply_reload(request: Request):
    await require_auth(request)
    await asyncio.to_thread(apply_reload_now)
    return {"ok": True}


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
            if r.returncode == 0 and action in ("restart", "start"):
                _log_restart("manual_" + action)
            return {"ok": r.returncode == 0, "output": "Service action completed" if r.returncode == 0 else "Service action failed"}
        except Exception as e:
            logger.error("Service %s error: %s", action, e)
            raise HTTPException(500, "Service action failed")

    return await asyncio.to_thread(_run)


@app.get("/api/restart-history")
async def restart_history(request: Request):
    await require_auth(request)
    db = await asyncio.to_thread(load_panel_db)
    return {"history": db.get("restart_history", [])}


@app.get("/api/panel-settings")
async def get_panel_settings(request: Request):
    await require_auth(request)
    db = await asyncio.to_thread(load_panel_db)
    defaults = {
        "session_ttl": 86400,
        "auto_renew_enabled": True,
        "auto_renew_days": 10,
        "max_history_days": 30,
        "max_log_mb": 50,
    }
    settings = db.get("panel_settings", {})
    for k, v in defaults.items():
        settings.setdefault(k, v)
    return {"settings": settings}


@app.put("/api/panel-settings")
async def update_panel_settings(request: Request):
    await require_auth(request)
    body = await request.json()
    db = await asyncio.to_thread(load_panel_db)
    settings = db.get("panel_settings", {})
    if "session_ttl" in body:
        ttl = int(body["session_ttl"])
        settings["session_ttl"] = max(300, min(ttl, 604800))
    if "auto_renew_enabled" in body:
        settings["auto_renew_enabled"] = bool(body["auto_renew_enabled"])
    if "auto_renew_days" in body:
        settings["auto_renew_days"] = max(1, min(int(body["auto_renew_days"]), 60))
    if "max_history_days" in body:
        days = int(body["max_history_days"])
        settings["max_history_days"] = max(1, min(days, 365))
    if "max_log_mb" in body:
        mb = int(body["max_log_mb"])
        settings["max_log_mb"] = max(5, min(mb, 500))
    db["panel_settings"] = settings
    await asyncio.to_thread(save_panel_db, db)
    _apply_log_rotation(settings)
    return {"ok": True, "settings": settings}


def _apply_log_rotation(settings):
    import os
    max_mb = settings.get("max_log_mb", 50)
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > max_mb * 1024 * 1024:
            rotated = LOG_FILE.with_suffix(".log.old")
            if rotated.exists():
                rotated.unlink()
            LOG_FILE.rename(rotated)
            subprocess.run(["systemctl", "reload", "trusttunnel"], timeout=5, capture_output=True)
    except Exception as e:
        logger.error("Log rotation error: %s", e)
    try:
        conf_dir = "/etc/systemd/journald.conf.d"
        os.makedirs(conf_dir, exist_ok=True)
        with open(os.path.join(conf_dir, "tt-panel.conf"), "w") as f:
            f.write("[Journal]\nSystemMaxUse=%dM\n" % max_mb)
    except Exception:
        pass


@app.get("/api/disk-info")
async def disk_info(request: Request):
    await require_auth(request)

    def _query():
        import os
        result = {"items": []}
        try:
            st = os.statvfs("/")
            total = st.f_frsize * st.f_blocks
            free = st.f_frsize * st.f_bfree
            result["disk_total_gb"] = round(total / 1073741824, 1)
            result["disk_free_gb"] = round(free / 1073741824, 1)
            result["disk_pct"] = round(100 * (total - free) / total, 1) if total > 0 else 0
        except Exception:
            pass
        paths = [
            ("/var/log/journal", "journald"),
            (str(LOG_FILE), "trusttunnel log"),
            (str(LOG_FILE) + ".1", "trusttunnel log.1"),
        ]
        from config import STATS_DB
        paths.append((str(STATS_DB), "stats.db"))
        for p, label in paths:
            try:
                from pathlib import Path
                pp = Path(p)
                if pp.is_dir():
                    size = sum(f.stat().st_size for f in pp.rglob("*") if f.is_file())
                elif pp.exists():
                    size = pp.stat().st_size
                else:
                    continue
                result["items"].append({"path": p, "label": label, "size_mb": round(size / 1048576, 1)})
            except Exception:
                pass
        return result

    return await asyncio.to_thread(_query)


@app.post("/api/cleanup-logs")
async def cleanup_logs(request: Request):
    await require_auth(request)

    def _run():
        cleaned = []
        try:
            r = subprocess.run(
                ["journalctl", "--vacuum-size=50M"],
                capture_output=True, text=True, timeout=30
            )
            if "freed" in r.stdout:
                cleaned.append("journald: " + r.stdout.strip().split("\n")[-1])
        except Exception:
            pass
        try:
            for suffix in [".2.gz", ".3.gz", ".4.gz", ".1"]:
                old = LOG_FILE.with_name(LOG_FILE.name + suffix)
                if old.exists():
                    size = old.stat().st_size
                    old.unlink()
                    cleaned.append("removed %s (%.1f MB)" % (old.name, size / 1048576))
        except Exception as e:
            logger.error("Log cleanup error: %s", e)
        return {"ok": True, "cleaned": cleaned}

    return await asyncio.to_thread(_run)
