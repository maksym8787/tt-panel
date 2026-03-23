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

GATEWAY_IF = os.environ.get("TT_GATEWAY_IF", "eth0")
TUN_IF = os.environ.get("TT_TUN_IF", "tun0")
LAN_GATEWAY = os.environ.get("TT_LAN_GATEWAY", "10.10.9.1")
LAN_NETWORK = os.environ.get("TT_LAN_NETWORK", "10.10.0.0/16")

_shutdown_event = threading.Event()
