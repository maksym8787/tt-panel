import signal
import sys

import config
from config import PANEL_PORT, PANEL_HOST, CERTS_DIR, logger, _shutdown_event


def _resolve_bind():
    """Decide host + TLS. Never serve a cleartext login on a public interface."""
    cert = CERTS_DIR / "cert.pem"
    key = CERTS_DIR / "key.pem"

    if cert.exists() and key.exists():
        config._ssl_configured = True
        logger.info("HTTPS on %s:%d", PANEL_HOST, PANEL_PORT)
        return PANEL_HOST, {"ssl_certfile": str(cert), "ssl_keyfile": str(key)}

    if PANEL_HOST in ("127.0.0.1", "::1", "localhost"):
        logger.info("HTTP on %s:%d (loopback only)", PANEL_HOST, PANEL_PORT)
        return PANEL_HOST, {}

    if config.BEHIND_PROXY:
        logger.warning("No certificate; serving plain HTTP on %s:%d behind a trusted proxy.",
                       PANEL_HOST, PANEL_PORT)
        return PANEL_HOST, {}

    if config.ALLOW_INSECURE_HTTP:
        logger.warning("No certificate and TT_ALLOW_INSECURE_HTTP=1: serving plain HTTP on %s:%d. "
                       "The admin password and session cookie travel in cleartext.",
                       PANEL_HOST, PANEL_PORT)
        return PANEL_HOST, {}

    logger.error("No certificate at %s and TT_CLIENT_PANEL_HOST=%s is not loopback. "
                 "Binding to 127.0.0.1 instead. Install certs, or set TT_BEHIND_PROXY=1 / "
                 "TT_ALLOW_INSECURE_HTTP=1 to override.", CERTS_DIR, PANEL_HOST)
    return "127.0.0.1", {}


def main():
    import uvicorn
    from routes import app
    from health import start_health_thread

    def shutdown_handler(sig, frame):
        logger.info("Shutting down...")
        _shutdown_event.set()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    from servers import import_existing_configs
    import_existing_configs()

    start_health_thread()

    host, ssl_kwargs = _resolve_bind()
    logger.info("Starting TrustTunnel Client Panel on %s:%d", host, PANEL_PORT)

    uvicorn.run(app, host=host, port=PANEL_PORT, log_level="warning", **ssl_kwargs)


if __name__ == "__main__":
    main()
