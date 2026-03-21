import os
import re
import secrets
import shutil
import string
import subprocess
import sys
import threading
import time
from pathlib import Path

from config import (
    TT_DIR, VPN_TOML, HOSTS_TOML, CREDS_TOML, CERTS_DIR,
    CERT_AUTO_RENEW_DAYS, logger,
)
import config

_pending_reload = False
_reload_timer = None
_reload_lock = threading.Lock()
RELOAD_DEBOUNCE = 5.0

_last_cert_check = 0


def _parse_toml_stdlib(path: Path) -> list:
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            raise ImportError("tomllib requires 3.11+")
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return data.get("client", [])
    except ImportError:
        return None
    except Exception as e:
        logger.warning("tomllib failed to parse %s: %s, falling back to manual parser", path, e)
        return None


def _toml_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def _normalize_client(c):
    from datetime import datetime
    return {
        "username": c.get("username", ""),
        "password": c.get("password", ""),
        "created_at": c.get("created_at", "") or datetime.now().isoformat(timespec="seconds"),
        "enabled": c.get("enabled", True) if isinstance(c.get("enabled"), bool) else str(c.get("enabled", "true")).lower() != "false",
    }


def write_credentials(clients):
    from auth import load_panel_db, save_panel_db
    lines = []
    disabled_store = []
    for c in clients:
        enabled = c.get("enabled", True)
        created = c.get("created_at", "")
        if enabled:
            lines.append("[[client]]")
            lines.append(f'username = "{_toml_escape(c["username"])}"')
            lines.append(f'password = "{_toml_escape(c["password"])}"')
            if created:
                lines.append(f'created_at = "{created}"')
            lines.append("")
        else:
            disabled_store.append({
                "username": c["username"],
                "password": c["password"],
                "created_at": created,
            })
    CREDS_TOML.write_text("\n".join(lines))
    panel = load_panel_db()
    panel["disabled_users"] = disabled_store
    save_panel_db(panel)


def parse_credentials():
    from auth import load_panel_db
    clients = []
    if not CREDS_TOML.exists():
        pass
    else:
        raw = _parse_toml_stdlib(CREDS_TOML)
        if raw is not None:
            clients = [_normalize_client(c) for c in raw]
        else:
            raw_clients = []
            current = {}
            for line in CREDS_TOML.read_text().splitlines():
                line = line.strip()
                if line == "[[client]]":
                    if current:
                        raw_clients.append(current)
                    current = {}
                elif "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    current[k.strip()] = v.strip().strip('"')
            if current:
                raw_clients.append(current)
            clients = [_normalize_client(c) for c in raw_clients]
    for c in clients:
        c["enabled"] = True
    panel = load_panel_db()
    for d in panel.get("disabled_users", []):
        clients.append({
            "username": d["username"],
            "password": d["password"],
            "created_at": d.get("created_at", ""),
            "enabled": False,
        })
    needs_save = any(not c.get("created_at") for c in clients)
    if needs_save:
        write_credentials(clients)
    return clients


def get_domain():
    if config.DOMAIN:
        return config.DOMAIN
    if HOSTS_TOML.exists():
        for line in HOSTS_TOML.read_text().splitlines():
            if "hostname" in line and "=" in line:
                config.DOMAIN = line.split("=", 1)[1].strip().strip('"')
                return config.DOMAIN
    return "unknown"


def export_client_config(username, fmt="toml"):
    domain = get_domain()
    cmd = [str(TT_DIR / "trusttunnel_endpoint"), str(VPN_TOML), str(HOSTS_TOML), "-c", username, "-a", domain, "-f", fmt]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=str(TT_DIR))
        if r.returncode == 0:
            return r.stdout.strip()
        logger.error("export_client_config failed: %s", r.stderr.strip())
        return "Error: configuration export failed"
    except Exception as e:
        logger.error("export_client_config exception: %s", e)
        return "Error: configuration export failed"


def get_service_status():
    info = {"active": False, "uptime": "", "uptime_seconds": 0, "memory": "", "pid": ""}
    try:
        r = subprocess.run(["systemctl", "show", "trusttunnel", "--no-pager",
            "-p", "ActiveState,MainPID,MemoryCurrent,ActiveEnterTimestampMonotonic"],
            capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            if line.startswith("ActiveState="):
                info["active"] = line.split("=", 1)[1] == "active"
            elif line.startswith("MainPID="):
                info["pid"] = line.split("=", 1)[1]
            elif line.startswith("MemoryCurrent="):
                v = line.split("=", 1)[1]
                if v.isdigit():
                    info["memory"] = f"{int(v)/1024/1024:.1f} MB"
            elif line.startswith("ActiveEnterTimestampMonotonic="):
                v = line.split("=", 1)[1].strip()
                if v.isdigit() and int(v) > 0:
                    mono_now = int(time.monotonic() * 1_000_000)
                    try:
                        with open("/proc/uptime") as f:
                            boot_seconds = float(f.read().split()[0])
                        mono_now = int(boot_seconds * 1_000_000)
                    except Exception:
                        pass
                    elapsed = max(0, mono_now - int(v))
                    info["uptime_seconds"] = elapsed // 1_000_000
    except Exception as e:
        logger.error("Service check error: %s", e)
    return info


def get_cert_days_remaining():
    cert = CERTS_DIR / "cert.pem"
    if not cert.exists():
        return None
    try:
        r = subprocess.run(["openssl", "x509", "-in", str(cert), "-noout", "-enddate"],
            capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            if "notAfter" in line:
                date_str = line.split("=", 1)[1].strip()
                from email.utils import parsedate_to_datetime
                from datetime import datetime
                exp = parsedate_to_datetime(date_str)
                delta = exp - datetime.now(exp.tzinfo)
                return {"days": delta.days, "date": date_str}
    except Exception as e:
        logger.error("Certificate check error: %s", e)
    return None


def get_server_ip():
    try:
        r = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip().split()[0]
    except Exception:
        return "unknown"


def generate_password(length=10):
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))


def _do_cert_renewal(domain: str) -> dict:
    if not shutil.which("certbot"):
        return {"ok": False, "message": "certbot not installed. Run: apt install certbot"}
    try:
        subprocess.run(["systemctl", "stop", "trusttunnel"], timeout=10)
        time.sleep(2)
        r2 = subprocess.run(
            ["certbot", "certonly", "--standalone", "-d", domain, "--non-interactive",
             "--agree-tos", "--register-unsafely-without-email", "--force-renewal"],
            capture_output=True, text=True, timeout=120
        )
        if r2.returncode == 0:
            le_dir = Path(f"/etc/letsencrypt/live/{domain}")
            if le_dir.exists():
                CERTS_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(le_dir / "fullchain.pem"), str(CERTS_DIR / "cert.pem"))
                shutil.copy2(str(le_dir / "privkey.pem"), str(CERTS_DIR / "key.pem"))
                logger.info("Certs copied from %s to %s", le_dir, CERTS_DIR)
            subprocess.run(["systemctl", "start", "trusttunnel"], timeout=10)
            return {"ok": True, "message": "Certificate renewed and installed"}
        subprocess.run(["systemctl", "start", "trusttunnel"], timeout=10)
        logger.error("Certbot failed (rc=%d): %s", r2.returncode, r2.stderr[:500])
        return {"ok": False, "message": "Certbot error (rc=" + str(r2.returncode) + "). Is port 80 free? Is domain pointing to this server?"}
    except FileNotFoundError:
        try:
            subprocess.run(["systemctl", "start", "trusttunnel"], timeout=10)
        except Exception:
            pass
        return {"ok": False, "message": "certbot not found in PATH"}
    except Exception as e:
        try:
            subprocess.run(["systemctl", "start", "trusttunnel"], timeout=10)
        except Exception:
            pass
        logger.error("Certificate renewal error: %s", e)
        return {"ok": False, "message": "Renewal failed: " + str(type(e).__name__)}


def auto_renew_cert_if_needed():
    global _last_cert_check
    now = time.time()
    if now - _last_cert_check < 3600:
        return
    _last_cert_check = now
    cert_info = get_cert_days_remaining()
    if cert_info is None:
        return
    days = cert_info.get("days", 999)
    if days <= CERT_AUTO_RENEW_DAYS:
        local_hour = time.localtime().tm_hour
        if local_hour < 3 or local_hour >= 5:
            logger.info("Cert expires in %d days, will auto-renew at 03:00-05:00", days)
            return
        domain = get_domain()
        logger.info("Auto-renewing certificate (expires in %d days, threshold=%d). VPN will be briefly stopped.", days, CERT_AUTO_RENEW_DAYS)
        result = _do_cert_renewal(domain)
        if result["ok"]:
            logger.info("Auto-renewal succeeded: %s", result["message"])
        else:
            logger.error("Auto-renewal failed: %s", result["message"])
    else:
        logger.debug("Certificate OK: %d days remaining", days)


def _do_deferred_reload():
    global _pending_reload
    with _reload_lock:
        _pending_reload = False
    try:
        subprocess.run(["systemctl", "reload-or-restart", "trusttunnel"], timeout=10)
        logger.info("Service reloaded (debounced)")
    except Exception as e:
        logger.error("Service reload error: %s", e)


def kill_client_sessions(client_ips):
    if not client_ips:
        return
    for ip in client_ips:
        try:
            subprocess.run(
                ["ss", "--kill", "state", "established",
                 f"src {ip}"],
                capture_output=True, timeout=5
            )
            logger.info("Killed sessions from IP %s", ip)
        except Exception as e:
            logger.warning("Failed to kill session for %s: %s", ip, e)


def get_active_ips_for_user(username):
    from database import get_db
    since = int(time.time()) - 3600
    ips = set()
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""SELECT DISTINCT client_ip FROM connections
                WHERE ts > ? AND client_ip IS NOT NULL AND event='connect'""",
                (since,))
            for row in c.fetchall():
                if row[0]:
                    ips.add(row[0])
    except Exception:
        pass
    return list(ips)


def schedule_reload():
    global _pending_reload, _reload_timer
    with _reload_lock:
        _pending_reload = True
        if _reload_timer is not None:
            _reload_timer.cancel()
        _reload_timer = threading.Timer(RELOAD_DEBOUNCE, _do_deferred_reload)
        _reload_timer.daemon = True
        _reload_timer.start()


def apply_reload_now():
    global _pending_reload, _reload_timer
    with _reload_lock:
        if _reload_timer is not None:
            _reload_timer.cancel()
            _reload_timer = None
        _pending_reload = False
    try:
        subprocess.run(["systemctl", "reload-or-restart", "trusttunnel"], timeout=10)
        logger.info("Service reloaded (immediate)")
    except Exception as e:
        logger.error("Service reload error: %s", e)


def is_reload_pending():
    return _pending_reload


_prev_cpu = None
_prev_cpu_ts = 0

def _read_cpu_stat():
    with open("/proc/stat") as f:
        for line in f:
            if line.startswith("cpu "):
                return list(map(int, line.split()[1:]))
    return None

def get_vps_resources():
    global _prev_cpu, _prev_cpu_ts
    info = {}
    try:
        cur = _read_cpu_stat()
        now = time.monotonic()
        if cur and _prev_cpu and (now - _prev_cpu_ts) > 1:
            d_idle = cur[3] - _prev_cpu[3]
            d_total = sum(cur) - sum(_prev_cpu)
            info["cpu_pct"] = round(100 * (1 - d_idle / d_total), 1) if d_total > 0 else 0
        else:
            info["cpu_pct"] = 0
        if cur:
            _prev_cpu = cur
            _prev_cpu_ts = now
    except Exception:
        info["cpu_pct"] = 0
    try:
        with open("/proc/meminfo") as f:
            mem = {}
            for line in f:
                parts = line.split()
                if parts[0] in ("MemTotal:", "MemAvailable:", "MemFree:", "Buffers:", "Cached:"):
                    mem[parts[0].rstrip(":")] = int(parts[1])
            total = mem.get("MemTotal", 1)
            avail = mem.get("MemAvailable", mem.get("MemFree", 0) + mem.get("Buffers", 0) + mem.get("Cached", 0))
            info["ram_total_mb"] = round(total / 1024)
            info["ram_used_mb"] = round((total - avail) / 1024)
            info["ram_pct"] = round(100 * (total - avail) / total, 1) if total > 0 else 0
    except Exception:
        info["ram_total_mb"] = 0
        info["ram_used_mb"] = 0
        info["ram_pct"] = 0
    try:
        st = os.statvfs("/")
        total = st.f_frsize * st.f_blocks
        used = total - st.f_frsize * st.f_bfree
        info["disk_total_gb"] = round(total / 1073741824, 1)
        info["disk_used_gb"] = round(used / 1073741824, 1)
        info["disk_pct"] = round(100 * used / total, 1) if total > 0 else 0
    except Exception:
        info["disk_total_gb"] = 0
        info["disk_used_gb"] = 0
        info["disk_pct"] = 0
    try:
        with open("/proc/uptime") as f:
            info["uptime_seconds"] = int(float(f.read().split()[0]))
    except Exception:
        info["uptime_seconds"] = 0
    return info
