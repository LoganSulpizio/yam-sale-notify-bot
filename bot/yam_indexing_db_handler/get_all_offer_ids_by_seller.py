from __future__ import annotations
from typing import List, Sequence, Optional
from psycopg2.extensions import connection as PGConnection


def get_all_offer_ids_by_seller(
    pg_conn: PGConnection,
    seller_address: str,
    status: Optional[Sequence[str]] = ("InProgress", "SoldOut", "Deleted"),
    include_purchase_offer: bool = False,
) -> List[int]:
    """
    Retrieve all offer IDs from a seller with specified statuses (PostgreSQL).

    Args:
        pg_conn: An opened psycopg2 PostgreSQL connection.
        seller_address: Address of the seller.
        status: Statuses to filter by (default: ("InProgress", "SoldOut", "Deleted")).
        include_purchase_offer: If False, excludes purchase offers (default: False).

    Returns:
        List of offer IDs matching the criteria.
    """
    # Keep the same behavior as your SQLite version
    if not status:
        return []

    excluded_tokens = (
        "0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d",  # WXDAI
        "0xDDAfbb505ad214D7b80b1f830fcCc89B60fb7A83",  # USDC
        "0xeD56F76E9cBC6A64b821e9c016eAFbd3db5436D1",  # ARMMV3USDC
        "0x0cA4f5554Dd9Da6217d62D8df2816c82bba4157b",  # ARMMV3WXDAI
        "0x0aa1e96d2a46ec6beb2923de1e61addf5f5f1dce",  # REG
    )

    # In Postgres, it's simplest/cleanest to use = ANY(%s) with a Python list/tuple.
    query = """
        SELECT offer_id
        FROM offers
        WHERE seller_address = %s
          AND status = ANY(%s)
    """
    params: List[object] = [seller_address, list(status)]

    if not include_purchase_offer:
        query += " AND offer_token <> ALL(%s)"
        params.append(list(excluded_tokens))

    with pg_conn.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [row[0] for row in rows]
