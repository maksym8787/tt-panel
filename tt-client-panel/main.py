import signal
import sys

import config
from config import PANEL_PORT, logger, _shutdown_event


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

    start_health_thread()
    logger.info("Starting TrustTunnel Client Panel on port %d", PANEL_PORT)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PANEL_PORT,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
