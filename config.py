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
# Per-user JSON served on the same listener as /metrics (endpoint 1.1.0+,
# gated by [metrics] per_client_metrics). 404 means the feature is off.
CLIENTS_URL = os.environ.get(
    "TT_CLIENTS_URL",
    METRICS_URL.rsplit("/metrics", 1)[0] + "/clients" if METRICS_URL.endswith("/metrics")
    else "http://127.0.0.1:1987/clients",
)

MAX_HISTORY_DAYS = int(os.environ.get("TT_MAX_HISTORY_DAYS", "30"))
COLLECT_INTERVAL = int(os.environ.get("TT_COLLECT_INTERVAL", "60"))
CERT_AUTO_RENEW_DAYS = int(os.environ.get("TT_CERT_RENEW_DAYS", "10"))

def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# Bind address. Defaults to all interfaces, but when the panel has no TLS of its
# own it refuses to serve publicly unless the operator opts in (see main.py).
PANEL_HOST = os.environ.get("TT_PANEL_HOST", "0.0.0.0")
# Set when a trusted reverse proxy terminates TLS in front of the panel; only
# then is X-Forwarded-Proto believed.
BEHIND_PROXY = _env_flag("TT_BEHIND_PROXY")
# Escape hatch for deliberately running the panel over plaintext HTTP.
ALLOW_INSECURE_HTTP = _env_flag("TT_ALLOW_INSECURE_HTTP")
# auto = TLS when certs exist; off = plain HTTP (the endpoint's reverse proxy
# terminates TLS on 443 and speaks HTTP/1.1 to the origin).
PANEL_TLS = os.environ.get("TT_PANEL_TLS", "auto").strip().lower()
# ip-api.com geolocation for connection logs. Sends client IPs to a third party.
GEO_LOOKUP_ENABLED = _env_flag("TT_GEO_LOOKUP", True)

def _normalize_base_path(raw: str) -> str:
    """'' (served at root) or '/prefix' with no trailing slash."""
    p = (raw or "").strip().strip('"').strip("'")
    if not p or p == "/":
        return ""
    if not p.startswith("/"):
        p = "/" + p
    return p.rstrip("/")


# When set, the panel answers only under this prefix and every other path gets a
# blank page. Used together with the endpoint's [reverse_proxy] so the panel is
# reachable on 443 without looking like a panel.
PANEL_BASE_PATH = _normalize_base_path(os.environ.get("TT_PANEL_PATH", ""))

DOMAIN = None
_ssl_configured = False

_shutdown_event = threading.Event()
