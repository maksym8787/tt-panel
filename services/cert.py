import os
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from config import CERTS_DIR, CERT_AUTO_RENEW_DAYS, logger
from services.credentials import get_domain


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
                exp = parsedate_to_datetime(date_str)
                delta = exp - datetime.now(exp.tzinfo)
                return {"days": delta.days, "date": date_str}
    except Exception as e:
        logger.error("Certificate check error: %s", e)
    return None


# Renewal stops the VPN and binds :80 — only one may run at a time, whether it
# was triggered by the collector thread or by an operator hitting the button.
_renew_lock = threading.Lock()

_DOMAIN_RE = re.compile(r'^(?=.{1,253}$)[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?'
                        r'(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$')


def _install_cert_files(le_dir: Path) -> bool:
    if not le_dir.exists():
        return False
    CERTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(CERTS_DIR), 0o700)
    except OSError:
        pass
    shutil.copy2(str(le_dir / "fullchain.pem"), str(CERTS_DIR / "cert.pem"))
    shutil.copy2(str(le_dir / "privkey.pem"), str(CERTS_DIR / "key.pem"))
    try:
        os.chmod(str(CERTS_DIR / "cert.pem"), 0o644)
        os.chmod(str(CERTS_DIR / "key.pem"), 0o600)
    except OSError:
        pass
    logger.info("Certs copied from %s to %s", le_dir, CERTS_DIR)
    return True


def _restart_panel_later():
    """uvicorn loads the cert once at boot, so the panel must restart to serve the new one."""
    def _later():
        time.sleep(3)
        try:
            subprocess.run(["systemctl", "restart", "tt-admin"], timeout=30, capture_output=True)
        except Exception as e:
            logger.error("Failed to restart panel after cert renewal: %s", e)

    threading.Thread(target=_later, daemon=True).start()


def _do_cert_renewal(domain: str) -> dict:
    from services.reload import _log_restart
    if not _DOMAIN_RE.match(domain or ""):
        return {"ok": False, "message": "Invalid domain: %r" % domain}
    if not shutil.which("certbot"):
        return {"ok": False, "message": "certbot not installed. Run: apt install certbot"}
    if not _renew_lock.acquire(blocking=False):
        return {"ok": False, "message": "A certificate renewal is already running"}

    result = {"ok": False, "message": "Unknown error"}
    try:
        subprocess.run(["systemctl", "stop", "trusttunnel"], timeout=30, capture_output=True)
        time.sleep(2)
        # No --force-renewal: certbot skips certs that are still fresh, which keeps
        # us well clear of Let's Encrypt's duplicate-certificate rate limit.
        r2 = subprocess.run(
            ["certbot", "certonly", "--standalone", "-d", domain, "--non-interactive",
             "--agree-tos", "--register-unsafely-without-email", "--keep-until-expiring"],
            capture_output=True, text=True, timeout=180
        )
        if r2.returncode == 0:
            installed = _install_cert_files(Path("/etc/letsencrypt/live/%s" % domain))
            _log_restart("cert_renewal")
            result = {"ok": True, "message": "Certificate renewed and installed"
                      if installed else "Certbot succeeded, but no certificate directory was found"}
        else:
            logger.error("Certbot failed (rc=%d): %s", r2.returncode, (r2.stderr or "")[:500])
            result = {"ok": False, "message": "Certbot error (rc=%d)" % r2.returncode}
    except subprocess.TimeoutExpired:
        result = {"ok": False, "message": "Certbot timed out"}
    except FileNotFoundError:
        result = {"ok": False, "message": "certbot not found in PATH"}
    except Exception as e:
        logger.error("Certificate renewal error: %s", e)
        result = {"ok": False, "message": "Renewal failed: " + type(e).__name__}
    finally:
        try:
            subprocess.run(["systemctl", "start", "trusttunnel"], timeout=30, capture_output=True)
            logger.info("TrustTunnel restarted after cert renewal")
        except Exception as e:
            logger.error("CRITICAL: Failed to restart TrustTunnel after cert renewal: %s", e)
        _renew_lock.release()
    if result["ok"]:
        _restart_panel_later()
    return result


_last_cert_check = 0


def auto_renew_cert_if_needed():
    global _last_cert_check
    now = time.time()
    if now - _last_cert_check < 3600:
        return
    _last_cert_check = now
    from auth import load_panel_db
    panel = load_panel_db()
    ps = panel.get("panel_settings", {})
    if not ps.get("auto_renew_enabled", True):
        return
    renew_days = ps.get("auto_renew_days", CERT_AUTO_RENEW_DAYS)
    cert_info = get_cert_days_remaining()
    if cert_info is None:
        return
    days = cert_info.get("days", 999)
    if days <= renew_days:
        local_hour = time.localtime().tm_hour
        if local_hour < 3 or local_hour >= 5:
            logger.info("Cert expires in %d days, will auto-renew at 03:00-05:00", days)
            return
        domain = get_domain()
        logger.info("Auto-renewing certificate (expires in %d days, threshold=%d). VPN will be briefly stopped.", days, renew_days)
        result = _do_cert_renewal(domain)
        if result["ok"]:
            logger.info("Auto-renewal succeeded: %s", result["message"])
        else:
            logger.error("Auto-renewal failed: %s", result["message"])
    else:
        logger.debug("Certificate OK: %d days remaining", days)
