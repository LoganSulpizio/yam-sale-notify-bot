import sqlite3
from typing import List, Dict, Any, Optional

def get_all_events_by_offer_id(db_path: str, offer_id: int) -> List[Optional[Dict[str, Any]]]:
    
    # Connect to the SQLite database (it will create the database file if it doesn't exist)
    conn = sqlite3.connect(db_path)

    # Set the row factory to sqlite3.Row
    conn.row_factory = sqlite3.Row

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Query to get the offer from the offers table
    cursor.execute("SELECT * FROM offers WHERE offer_id = ?", (offer_id,))
    offer_base = cursor.fetchone()
    
    # Convert the Row object to a dictionary for the offer
    offer_base_dict = dict(offer_base) if offer_base else None

    # Query to get all events related to the offer_id from the offer_events table
    cursor.execute("SELECT * FROM offer_events WHERE offer_id = ?", (offer_id,))
    offer_events = cursor.fetchall()

    # Convert the Row objects to dictionaries for the events
    offer_event_dicts = [dict(row) for row in offer_events]

    # Close the connection
    conn.close()

    # Combine the offer dictionary and the list of event dictionaries
    result = [offer_base_dict] + offer_event_dicts if offer_base_dict else offer_event_dicts

    return result