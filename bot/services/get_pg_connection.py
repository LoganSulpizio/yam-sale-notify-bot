from __future__ import annotations
import psycopg2
from psycopg2.extensions import connection as PGConnection
import time
import logging
from bot.services.send_telegram_alert import send_telegram_alert
logger = logging.getLogger(__name__)

def get_pg_connection(pg_host, pg_port, pg_db, pg_user, pg_password) -> PGConnection:
    """
    Create and return a PostgreSQL connection.
    """
    return psycopg2.connect(
        host=pg_host,
        port=pg_port,
        dbname=pg_db,
        user=pg_user,
        password=pg_password,
        connect_timeout=10,
    )

def test_postgres_connection(POSTGRES_DATA) -> bool:
    try:
        conn = get_pg_connection(*POSTGRES_DATA)
        conn.close()
        return True
    except Exception as e:
        send_telegram_alert(f"roi calculator api: Postgres DB connection failed")
        logger.exception(f"Postgres connection failed")
        time.sleep(120)
        return False