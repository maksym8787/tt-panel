import logging
import os
import threading
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tt-admin")

TT_DIR = Path(os.environ.get("TT_DIR", "/opt/trusttunnel"))
VPN_TOML = TT_DIR / "vpn.toml"
HOSTS_TOML = TT_DIR / "hosts.toml"
CREDS_TOML = TT_DIR / "credentials.toml"
RULES_TOML = TT_DIR / "rules.toml"
CERTS_DIR = TT_DIR / "certs"
LOG_FILE = Path(os.environ.get("TT_LOG_FILE", "/var/log/trusttunnel.log"))

PANEL_DIR = Path(os.environ.get("TT_PANEL_DIR", "/opt/trusttunnel-panel"))
PANEL_DB = PANEL_DIR / "panel.json"
STATS_DB = PANEL_DIR / "stats.db"
PANEL_PORT = int(os.environ.get("TT_PANEL_PORT", "8443"))
METRICS_URL = os.environ.get("TT_METRICS_URL", "http://127.0.0.1:1987/metrics")

MAX_HISTORY_DAYS = int(os.environ.get("TT_MAX_HISTORY_DAYS", "30"))
COLLECT_INTERVAL = int(os.environ.get("TT_COLLECT_INTERVAL", "60"))
CERT_AUTO_RENEW_DAYS = int(os.environ.get("TT_CERT_RENEW_DAYS", "10"))

DOMAIN = None
_ssl_configured = False

_shutdown_event = threading.Event()
