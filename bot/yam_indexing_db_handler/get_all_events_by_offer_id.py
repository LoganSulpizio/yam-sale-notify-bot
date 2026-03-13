from __future__ import annotations

from typing import List, Dict, Any, Optional
from psycopg2.extensions import connection as PGConnection


def get_all_events_by_offer_id(
    pg_conn: PGConnection,
    offer_id: int,
) -> List[Optional[Dict[str, Any]]]:
    """
    Retrieve the base offer row and all related offer_events for a given offer_id (PostgreSQL).

    Args:
        pg_conn: An opened psycopg2 PostgreSQL connection.
        offer_id: The offer ID.

    Returns:
        A list containing:
            - the offer row as a dict (if exists)
            - followed by all related event rows as dicts
        If the offer does not exist, only the event rows are returned.
    """

    with pg_conn.cursor() as cursor:
        # Get column names automatically from cursor.description
        def fetch_one_as_dict() -> Optional[Dict[str, Any]]:
            row = cursor.fetchone()
            if row is None:
                return None
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

        def fetch_all_as_dicts() -> List[Dict[str, Any]]:
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

        # Query base offer
        cursor.execute(
            "SELECT * FROM offers WHERE offer_id = %s",
            (offer_id,),
        )
        offer_base_dict = fetch_one_as_dict()

        # Query related events
        cursor.execute(
            "SELECT * FROM offer_events WHERE offer_id = %s",
            (offer_id,),
        )
        offer_event_dicts = fetch_all_as_dicts()

    # Same behavior as your SQLite version
    return (
        [offer_base_dict] + offer_event_dicts
        if offer_base_dict
        else offer_event_dicts
    )
