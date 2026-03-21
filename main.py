import threading

import uvicorn

from config import PANEL_PORT, CERTS_DIR, logger, _shutdown_event
import config
from database import init_stats_db
from collector import collector_loop
from routes import app


def main():
    init_stats_db()
    t = threading.Thread(target=collector_loop, daemon=True)
    t.start()

    cert = CERTS_DIR / "cert.pem"
    key = CERTS_DIR / "key.pem"
    ssl_kwargs = {}
    if cert.exists() and key.exists():
        ssl_kwargs = {"ssl_certfile": str(cert), "ssl_keyfile": str(key)}
        config._ssl_configured = True
        logger.info("HTTPS on port %d", PANEL_PORT)
    else:
        logger.info("HTTP on port %d", PANEL_PORT)

    try:
        uvicorn.run(app, host="0.0.0.0", port=PANEL_PORT, log_level="info", **ssl_kwargs)
    finally:
        _shutdown_event.set()


if __name__ == "__main__":
    main()
