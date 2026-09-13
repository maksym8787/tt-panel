import logging
import os
import threading
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tt-client")

TT_CLIENT_DIR = Path(os.environ.get("TT_CLIENT_DIR", "/opt/trusttunnel_client"))
TT_CONFIG_DIR = Path(os.environ.get("TT_CONFIG_DIR", "/etc/trusttunnel"))
TT_CONFIGS_DIR = TT_CONFIG_DIR / "configs"
TT_ACTIVE_LINK = TT_CONFIG_DIR / "active-config.toml"
TT_CLIENT_BIN = TT_CLIENT_DIR / "trusttunnel_client"
SETUP_ROUTES_SH = TT_CLIENT_DIR / "setup-routes.sh"
SERVICE_NAME = "trusttunnel-client"

PANEL_DIR = Path(os.environ.get("TT_CLIENT_PANEL_DIR", "/opt/tt-client-panel"))
PANEL_DB = PANEL_DIR / "panel.json"
NET_HISTORY_FILE = PANEL_DIR / "net_history.json"
PANEL_PORT = int(os.environ.get("TT_CLIENT_PANEL_PORT", "8443"))

import re as _re

def _validate_iface(v):
    if not _re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
        raise ValueError(f"Invalid interface name: {v}")
    return v

def _validate_ip_net(v):
    if not _re.match(r'^[0-9a-fA-F:\.\/]+$', v):
        raise ValueError(f"Invalid IP/network: {v}")
    return v

GATEWAY_IF = _validate_iface(os.environ.get("TT_GATEWAY_IF", "eth0"))
TUN_IF = _validate_iface(os.environ.get("TT_TUN_IF", "tun0"))
LAN_GATEWAY = _validate_ip_net(os.environ.get("TT_LAN_GATEWAY", "10.10.9.1"))
LAN_NETWORK = _validate_ip_net(os.environ.get("TT_LAN_NETWORK", "10.10.0.0/16"))

CERTS_DIR = Path(os.environ.get("TT_CLIENT_CERTS_DIR", str(PANEL_DIR / "certs")))


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# Defaults to loopback: this panel usually runs on a LAN gateway, and without TLS
# a public bind would put the admin password on the wire in cleartext.
PANEL_HOST = os.environ.get("TT_CLIENT_PANEL_HOST", "127.0.0.1")
BEHIND_PROXY = _env_flag("TT_BEHIND_PROXY")
ALLOW_INSECURE_HTTP = _env_flag("TT_ALLOW_INSECURE_HTTP")

_ssl_configured = False
_shutdown_event = threading.Event()
