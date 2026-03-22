import shutil
import subprocess
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


def _do_cert_renewal(domain: str) -> dict:
    from services.reload import _log_restart
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
            _log_restart("cert_renewal")
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
