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


def parse_credentials():
    clients = []
    if not CREDS_TOML.exists():
        return clients
    result = _parse_toml_stdlib(CREDS_TOML)
    if result is not None:
        return [{"username": c.get("username", ""), "password": c.get("password", "")} for c in result]
    current = {}
    for line in CREDS_TOML.read_text().splitlines():
        line = line.strip()
        if line == "[[client]]":
            if current:
                clients.append(current)
            current = {}
        elif "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            current[k.strip()] = v.strip().strip('"')
    if current:
        clients.append(current)
    return clients


def write_credentials(clients):
    lines = []
    for c in clients:
        lines.extend(["[[client]]", f'username = "{c["username"]}"', f'password = "{c["password"]}"', ""])
    CREDS_TOML.write_text("\n".join(lines))


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
    info = {"active": False, "uptime": "", "memory": "", "pid": ""}
    try:
        r = subprocess.run(["systemctl", "show", "trusttunnel", "--no-pager",
            "-p", "ActiveState,MainPID,MemoryCurrent,ActiveEnterTimestamp"],
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
            elif line.startswith("ActiveEnterTimestamp="):
                info["uptime"] = line.split("=", 1)[1].strip()
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


def get_vps_resources():
    info = {}
    try:
        r = subprocess.run(
            ["grep", "cpu ", "/proc/stat"], capture_output=True, text=True, timeout=2
        )
        if r.returncode == 0:
            vals1 = list(map(int, r.stdout.strip().split()[1:]))
            time.sleep(0.2)
            r2 = subprocess.run(
                ["grep", "cpu ", "/proc/stat"], capture_output=True, text=True, timeout=2
            )
            if r2.returncode == 0:
                vals2 = list(map(int, r2.stdout.strip().split()[1:]))
                d_idle = vals2[3] - vals1[3]
                d_total = sum(vals2) - sum(vals1)
                info["cpu_pct"] = round(100 * (1 - d_idle / d_total), 1) if d_total > 0 else 0
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
        r = subprocess.run(["df", "-B1", "/"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            parts = r.stdout.strip().splitlines()[-1].split()
            total = int(parts[1])
            used = int(parts[2])
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
