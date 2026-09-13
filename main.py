import signal
import threading

import uvicorn

from config import PANEL_PORT, PANEL_HOST, CERTS_DIR, logger, _shutdown_event
import config
from database import init_stats_db
from collector import collector_loop
from routes import app


def _resolve_bind():
    """Decide host + TLS. Never expose a cleartext login to the internet by accident."""
    cert = CERTS_DIR / "cert.pem"
    key = CERTS_DIR / "key.pem"

    if config.PANEL_TLS in ("off", "0", "false", "no"):
        logger.info("TLS disabled (TT_PANEL_TLS=off): plain HTTP on %s:%d", PANEL_HOST, PANEL_PORT)
        return PANEL_HOST, {}

    if cert.exists() and key.exists():
        config._ssl_configured = True
        logger.info("HTTPS on %s:%d", PANEL_HOST, PANEL_PORT)
        return PANEL_HOST, {"ssl_certfile": str(cert), "ssl_keyfile": str(key)}

    if config.BEHIND_PROXY:
        logger.warning(
            "No certificate found; serving plain HTTP on %s:%d behind a trusted reverse proxy "
            "(TT_BEHIND_PROXY=1).", PANEL_HOST, PANEL_PORT,
        )
        return PANEL_HOST, {}

    if config.ALLOW_INSECURE_HTTP:
        logger.warning(
            "No certificate found and TT_ALLOW_INSECURE_HTTP=1: serving plain HTTP on %s:%d. "
            "The admin password and session cookie travel in cleartext.", PANEL_HOST, PANEL_PORT,
        )
        return PANEL_HOST, {}

    logger.error(
        "No certificate at %s. Refusing to expose a cleartext panel: binding to 127.0.0.1 only. "
        "Install certs, or set TT_BEHIND_PROXY=1 (TLS-terminating proxy) or TT_ALLOW_INSECURE_HTTP=1 to override.",
        CERTS_DIR,
    )
    return "127.0.0.1", {}


def main():
    init_stats_db()
    t = threading.Thread(target=collector_loop, daemon=True)
    t.start()

    def _shutdown(_sig, _frame):
        logger.info("Shutting down...")
        _shutdown_event.set()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    host, ssl_kwargs = _resolve_bind()

    try:
        uvicorn.run(app, host=host, port=PANEL_PORT, log_level="info", **ssl_kwargs)
    finally:
        _shutdown_event.set()


if __name__ == "__main__":
    main()
