import secrets
import string
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config import TT_DIR, VPN_TOML, HOSTS_TOML, CREDS_TOML, logger
import config


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
    if CREDS_TOML.exists():
        CREDS_TOML.with_suffix(".toml.bak").write_text(CREDS_TOML.read_text())
    tmp = CREDS_TOML.with_suffix(".tmp")
    tmp.write_text("\n".join(lines))
    tmp.replace(CREDS_TOML)
    panel = load_panel_db()
    panel["disabled_users"] = disabled_store
    save_panel_db(panel)


def parse_credentials():
    from auth import load_panel_db
    clients = []
    if CREDS_TOML.exists():
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


def generate_password(length=10):
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
