import re
import secrets
import string
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from config import TT_DIR, VPN_TOML, HOSTS_TOML, CREDS_TOML, logger
import config

# Serialises read-modify-write of credentials.toml across request threads.
_creds_lock = threading.RLock()

# TrustTunnel's endpoint only knows these export formats (see `-f` in the binary).
EXPORT_FORMATS = ("toml", "deeplink")

USERNAME_RE = re.compile(r'^[a-zA-Z0-9_\-]{1,64}$')


def _parse_toml_stdlib(path: Path) -> list:
    if sys.version_info < (3, 11):
        return None
    import tomllib
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return data.get("client", [])
    except Exception as e:
        logger.warning("tomllib failed to parse %s: %s, falling back to manual parser", path, e)
        return None


def _toml_escape(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def _normalize_client(c):
    return {
        "username": c.get("username", ""),
        "password": c.get("password", ""),
        "created_at": c.get("created_at", "") or datetime.now().isoformat(timespec="seconds"),
        "enabled": c.get("enabled", True) if isinstance(c.get("enabled"), bool) else str(c.get("enabled", "true")).lower() != "false",
    }


def write_credentials(clients):
    from auth import update_panel_db
    from services.toml_settings import _atomic_write_text, _backup
    with _creds_lock:
        lines = []
        disabled_store = []
        for c in clients:
            if not c.get("username"):
                continue
            created = c.get("created_at", "")
            if c.get("enabled", True):
                lines.append("[[client]]")
                lines.append('username = "%s"' % _toml_escape(c["username"]))
                lines.append('password = "%s"' % _toml_escape(c["password"]))
                if created:
                    lines.append('created_at = "%s"' % _toml_escape(created))
                lines.append("")
            else:
                disabled_store.append({
                    "username": c["username"],
                    "password": c["password"],
                    "created_at": created,
                })
        _backup(CREDS_TOML)
        # 0600: this file holds every VPN password in cleartext.
        _atomic_write_text(CREDS_TOML, "\n".join(lines), mode=0o600)

        def _mutate(panel):
            panel["disabled_users"] = disabled_store

        update_panel_db(_mutate)


def _read_credentials_file():
    if not CREDS_TOML.exists():
        return []
    raw = _parse_toml_stdlib(CREDS_TOML)
    if raw is not None:
        return [_normalize_client(c) for c in raw]
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
    return [_normalize_client(c) for c in raw_clients]


def parse_credentials():
    """Read the client list. Pure read — never writes (GET must stay idempotent)."""
    from auth import load_panel_db
    with _creds_lock:
        clients = _read_credentials_file()
        for c in clients:
            c["enabled"] = True
        panel = load_panel_db()
        for d in panel.get("disabled_users", []):
            clients.append({
                "username": d.get("username", ""),
                "password": d.get("password", ""),
                "created_at": d.get("created_at", ""),
                "enabled": False,
            })
        return clients


def update_credentials(mutator):
    """Atomic read-modify-write of the client list.

    `mutator(clients)` mutates the list in place (use `clients[:] = ...` to
    replace it) and returns whatever the caller needs back.
    """
    with _creds_lock:
        clients = parse_credentials()
        result = mutator(clients)
        write_credentials(clients)
        return result


def backfill_created_at():
    """One-off migration for legacy entries without created_at. Called at startup."""
    try:
        with _creds_lock:
            clients = parse_credentials()
            if not any(not c.get("created_at") for c in clients):
                return
            now = datetime.now().isoformat(timespec="seconds")
            for c in clients:
                if not c.get("created_at"):
                    c["created_at"] = now
            write_credentials(clients)
            logger.info("Backfilled created_at for legacy credentials")
    except Exception as e:
        logger.warning("created_at backfill failed: %s", e)


def get_domain():
    if config.DOMAIN:
        return config.DOMAIN
    if HOSTS_TOML.exists():
        for line in HOSTS_TOML.read_text().splitlines():
            if "hostname" in line and "=" in line:
                config.DOMAIN = line.split("=", 1)[1].strip().strip('"')
                return config.DOMAIN
    return "unknown"


def _clean_export(stdout, fmt):
    """Keep only the configuration itself.

    In deeplink mode the endpoint prints the tt:// URI followed by a blank line
    and a "To connect on mobile, you can scan QR code on the page: https://..."
    hint. Feeding all of that into the QR made phones open the app with a
    payload it could not parse, so nothing was added. The official qr.html
    encodes exactly 'tt://?' + payload and nothing else; so do we.
    """
    if fmt == "deeplink":
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("tt://"):
                return line
        return None
    return stdout.strip()


def export_client_config(username, fmt="toml"):
    if fmt not in EXPORT_FORMATS:
        raise ValueError("unsupported format: %s" % fmt)
    if not USERNAME_RE.match(username or ""):
        raise ValueError("invalid username")
    domain = get_domain()
    cmd = [str(TT_DIR / "trusttunnel_endpoint"), str(VPN_TOML), str(HOSTS_TOML),
           "-c", username, "-a", domain, "-f", fmt]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=str(TT_DIR))
        if r.returncode == 0:
            return _clean_export(r.stdout, fmt)
        logger.error("export_client_config failed (rc=%d): %s", r.returncode, r.stderr.strip()[:300])
    except Exception as e:
        logger.error("export_client_config exception: %s", e)
    return None


def generate_password(length=16):
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
