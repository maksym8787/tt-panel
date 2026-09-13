import asyncio
import subprocess

from fastapi import HTTPException, Request

from auth import load_panel_db, update_panel_db, require_auth
from config import VPN_TOML, RULES_TOML, HOSTS_TOML, LOG_FILE, logger
from services import (
    get_domain, _do_cert_renewal, apply_reload_now, schedule_reload, _log_restart,
)
from routes import app


@app.post("/api/apply-reload")
async def apply_reload(request: Request):
    await require_auth(request)
    result = await asyncio.to_thread(apply_reload_now)
    if not result.get("ok"):
        raise HTTPException(500, "Service restart failed: " + (result.get("error") or "unknown"))
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


@app.get("/api/settings/structured")
async def get_settings_structured(request: Request):
    await require_auth(request)
    from services.toml_settings import parse_vpn_structured, parse_hosts_structured, parse_rules_structured, get_schema

    def _read():
        return {
            "vpn": parse_vpn_structured(),
            "hosts": parse_hosts_structured(),
            "rules": parse_rules_structured(),
            "schema": get_schema(),
        }

    return await asyncio.to_thread(_read)


@app.put("/api/settings/vpn")
async def save_vpn_settings(request: Request):
    await require_auth(request)
    from services.toml_settings import save_vpn_structured
    body = await request.json()
    try:
        await asyncio.to_thread(save_vpn_structured, body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    schedule_reload("config_change:vpn.toml")
    return {"ok": True}


@app.put("/api/settings/rules")
async def save_rules_settings(request: Request):
    await require_auth(request)
    from services.toml_settings import save_rules_structured
    body = await request.json()
    rules = body.get("rules", [])
    if not isinstance(rules, list):
        raise HTTPException(400, "rules must be a list")
    try:
        await asyncio.to_thread(save_rules_structured, rules)
    except ValueError as e:
        raise HTTPException(400, str(e))
    schedule_reload("config_change:rules.toml")
    return {"ok": True}


@app.put("/api/settings/{filename}")
async def update_settings(filename: str, request: Request):
    await require_auth(request)
    allowed = {"vpn_toml": VPN_TOML, "rules_toml": RULES_TOML}
    if filename not in allowed:
        raise HTTPException(400, "Cannot edit")
    body = await request.json()
    content = body.get("content", "")
    if not isinstance(content, str):
        raise HTTPException(400, "content must be a string")
    if len(content) > 1_000_000:
        raise HTTPException(400, "content too large")

    def _write():
        from services.toml_settings import _atomic_write_text, _backup, _parse_toml_file
        target = allowed[filename]
        _backup(target)
        _atomic_write_text(target, content)
        # Surface a syntax error immediately instead of letting the service fail to start.
        try:
            _parse_toml_file(target)
        except Exception as e:
            return str(e)
        return None

    err = await asyncio.to_thread(_write)
    if err:
        return {"ok": True, "warning": "Saved, but the file does not parse as TOML: " + err}
    schedule_reload("config_change:" + filename)
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


def _clamped_int(body, key, lo, hi):
    try:
        return max(lo, min(int(body[key]), hi))
    except (ValueError, TypeError):
        raise HTTPException(400, "%s must be an integer between %d and %d" % (key, lo, hi))


@app.put("/api/panel-settings")
async def update_panel_settings(request: Request):
    await require_auth(request)
    body = await request.json()
    updates = {}
    if "session_ttl" in body:
        updates["session_ttl"] = _clamped_int(body, "session_ttl", 300, 604800)
    if "auto_renew_enabled" in body:
        updates["auto_renew_enabled"] = bool(body["auto_renew_enabled"])
    if "auto_renew_days" in body:
        updates["auto_renew_days"] = _clamped_int(body, "auto_renew_days", 1, 60)
    if "max_history_days" in body:
        updates["max_history_days"] = _clamped_int(body, "max_history_days", 1, 365)
    if "max_log_mb" in body:
        updates["max_log_mb"] = _clamped_int(body, "max_log_mb", 5, 500)

    def _mutate(d):
        settings = d.setdefault("panel_settings", {})
        settings.update(updates)
        return dict(settings)

    settings = await asyncio.to_thread(update_panel_db, _mutate)
    # Only touch journald/logrotate when the log limit itself was edited — every
    # other setting change should have no side effects on /etc.
    if "max_log_mb" in body:
        await asyncio.to_thread(_apply_log_rotation, settings)
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
