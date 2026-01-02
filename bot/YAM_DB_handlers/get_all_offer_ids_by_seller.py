from typing import List
import sqlite3

def get_all_offer_ids_by_seller(db_path: str, seller_address: str, status: List[str] = ['InProgress', 'SoldOut', 'Deleted'], include_purchase_offer: bool = False) -> List[int]:
    """
    Retrieve all offer IDs from a seller with specified statuses.
    
    Args:
        db_path: Path to the SQLite database file
        seller_address: Address of the seller
        status: List of statuses to filter by (default: ['InProgress', 'SoldOut', 'Deleted'])
        include_purchase_offer: If False, excludes offers purchase offers (default: False)
    
    Returns:
        List of offer IDs matching the criteria
    """
    # Check if status list is empty
    if not status:
        return []
    
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    
    try:
        cursor = conn.cursor()

        # Base query
        query = "SELECT offer_id FROM offers WHERE seller_address = ? AND status IN ({0})"
        
        # Add token exclusion if include_purchase_offer is False
        excluded_tokens = [
            '0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d', # WXDAI
            '0xDDAfbb505ad214D7b80b1f830fcCc89B60fb7A83', # USDC
            '0xeD56F76E9cBC6A64b821e9c016eAFbd3db5436D1', # ARMMV3USDC
            '0x0cA4f5554Dd9Da6217d62D8df2816c82bba4157b', # ARMMV3WXDAI
            '0x0aa1e96d2a46ec6beb2923de1e61addf5f5f1dce'  # REG
        ]
        
        # Create placeholders for the status list
        status_placeholders = ','.join(['?' for _ in status])
        
        # Set up parameters for the query
        params = [seller_address] + status
        
        if not include_purchase_offer:
            token_placeholders = ','.join(['?' for _ in excluded_tokens])
            query = query.format(status_placeholders) + f" AND offer_token NOT IN ({token_placeholders})"
            params.extend(excluded_tokens)
        else:
            query = query.format(status_placeholders)
        
        # Execute the query with parameters
        cursor.execute(query, params)
        offer_ids = cursor.fetchall()

        # Extract the offer_id from each row
        offer_id_list = [row[0] for row in offer_ids]
        
        return offer_id_list
    
    finally:
        # Ensure connection is closed even if an exception occurs
        conn.close()