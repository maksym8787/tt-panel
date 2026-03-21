import contextlib
import sqlite3
import time

from config import STATS_DB, PANEL_DIR, MAX_HISTORY_DAYS, logger

_last_vacuum_ts = 0


@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect(str(STATS_DB), timeout=10)
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_stats_db():
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS metrics_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            sessions INTEGER DEFAULT 0,
            inbound_bytes INTEGER DEFAULT 0,
            outbound_bytes INTEGER DEFAULT 0,
            tcp_sockets INTEGER DEFAULT 0,
            udp_sockets INTEGER DEFAULT 0,
            cpu_seconds REAL DEFAULT 0,
            memory_bytes INTEGER DEFAULT 0,
            open_fds INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            client_ip TEXT,
            user_agent TEXT,
            destination TEXT,
            protocol TEXT,
            event TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS traffic_hourly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hour_ts INTEGER NOT NULL,
            inbound_bytes INTEGER DEFAULT 0,
            outbound_bytes INTEGER DEFAULT 0,
            sessions_max INTEGER DEFAULT 0,
            connections_count INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_metrics_ts ON metrics_snapshots(ts)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_conn_ts ON connections(ts)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_conn_ts_event ON connections(ts, event)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_conn_ts_ip ON connections(ts, client_ip)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_traffic_hour ON traffic_hourly(hour_ts)")
        conn.commit()


def cleanup_old_data():
    global _last_vacuum_ts
    cutoff = int(time.time()) - (MAX_HISTORY_DAYS * 86400)
    with get_db() as conn:
        conn.execute("PRAGMA busy_timeout=5000")
        c = conn.cursor()
        c.execute("DELETE FROM metrics_snapshots WHERE ts < ?", (cutoff,))
        c.execute("DELETE FROM connections WHERE ts < ?", (cutoff,))
        c.execute("DELETE FROM traffic_hourly WHERE hour_ts < ?", (cutoff,))
        conn.commit()
    now = time.time()
    if now - _last_vacuum_ts > 86400:
        conn2 = None
        try:
            conn2 = sqlite3.connect(str(STATS_DB))
            conn2.execute("VACUUM")
            _last_vacuum_ts = now
        except Exception:
            logger.debug("VACUUM failed, will retry next cycle")
        finally:
            if conn2:
                conn2.close()
