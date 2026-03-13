from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import psycopg2
from psycopg2.extensions import connection as PGConnection
from telegram.ext import ContextTypes
from bot.bot_handlers.language_handlers import translate
from bot.services.utilities import send_message, load_blockchain_ressources
from bot.services.get_pg_connection import get_pg_connection
from bot.services.send_telegram_alert import send_telegram_alert

from bot.services.logging_config import get_logger
logger = get_logger(__name__)

contract_data = load_blockchain_ressources()

MAX_EVENTS_PER_RUN = 15


# Read the tx json files
def process_tx_file(data: dict, user_wallets: dict, realtoken_data: dict):

    seller = data['seller']
    offerToken = data['offerToken']
    buyerToken = data['buyerToken']
    price = data['price']
    amount = data['amount']
    tx_hash = data['transactionHash']
    offerId = data['offerId']

    user_id_list = [key for key, value in user_wallets.items() if value == seller]

    if len(user_id_list) > 0:

        # Find all keys where the value is 'seller'
        user_id_list = [key for key, value in user_wallets.items() if value == seller]
        message_list = []

        mode = None
        # mode 1: sale offer
        # mode 2: purchase offer
        
        stablecoin_YAM = [
            '0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d', # WXDAI
            '0xDDAfbb505ad214D7b80b1f830fcCc89B60fb7A83', # USDC
            '0xeD56F76E9cBC6A64b821e9c016eAFbd3db5436D1', # ARMMV3USDC
            '0x0cA4f5554Dd9Da6217d62D8df2816c82bba4157b', # ARMMV3WXDAI
        ]

        if buyerToken in stablecoin_YAM and offerToken in stablecoin_YAM:
            mode = 3 # exchange bewteen two stable (exemple: ARMMV3USDC / USDC)
        elif buyerToken in stablecoin_YAM:
            mode = 1
        elif offerToken in stablecoin_YAM:
            mode = 2

        if mode == 1: # Sale offer

            decimals, token_name_buyer = get_token_decimals(buyerToken)

            decimals_realtoken = 18
            if offerToken == '0x0675e8F4A52eA6c845CB6427Af03616a2af42170': decimals_realtoken = 9 # RWA has 9 decimals and not 18

            amount_dec = amount / 10 ** decimals_realtoken
            price_dec_per_token = price / 10 ** decimals

            price_dec_total = round(price_dec_per_token * amount_dec, 2)
            amount_dec = round(amount_dec, 2)

            property_name = realtoken_data.get(offerToken.lower(), {}).get('shortName', 'unknown token')

            for user_id in user_id_list:
                message = translate(user_id,
                                    'sale_message',
                                    amount_dec = amount_dec,
                                    price_dec_total = price_dec_total,
                                    property_name = property_name,
                                    token_name_buyer = token_name_buyer,
                                    tx_hash = tx_hash,
                                    offerId = offerId
                                    )
                message_list.append(message)

        elif mode == 2: # Purchase offer
            
            decimals, token_name_offer = get_token_decimals(offerToken)

            decimals_realtoken = 18
            if buyerToken == '0x0675e8F4A52eA6c845CB6427Af03616a2af42170': decimals_realtoken = 9 # RWA has 9 decimals and not 18

            price_dec_per_token = 10 ** decimals_realtoken / price
            amount_dec = amount * price / 10 ** (decimals + decimals_realtoken)

            price_dec_per_token = round(price_dec_per_token, 2)
            amount_dec = round(amount_dec, 2)

            property_name = realtoken_data.get(buyerToken.lower(), {}).get('shortName', 'unknown token')

            for user_id in user_id_list:
                message = translate(user_id,
                                    'purchase_message',
                                    amount_dec = amount_dec,
                                    price_dec = price_dec_per_token,
                                    property_name = property_name,
                                    token_name_offer = token_name_offer,
                                    tx_hash = tx_hash,
                                    offerId = offerId
                                    )
                message_list.append(message)

        if mode == 3: # Exchange offer
            token_buyer_decimals, token_buyer_name = get_token_decimals(buyerToken)
            token_offer_decimals, token_offer_name = get_token_decimals(offerToken)

            amount_dec = amount / 10 ** token_buyer_decimals
            price_dec_per_token = price / 10 ** token_offer_decimals

            price_dec_total = round(price_dec_per_token * amount_dec, 2)
            amount_dec = round(amount_dec, 2)


            for user_id in user_id_list:
                message = translate(user_id,
                                    'sale_message',
                                    amount_dec = amount_dec,
                                    price_dec_total = price_dec_total,
                                    property_name = token_offer_name,
                                    token_name_buyer = token_buyer_name,
                                    tx_hash = tx_hash,
                                    offerId = offerId
                                    )
                message_list.append(message)


    logger.info(f"{tx_hash} has been processed")
            
    if len(user_id_list) > 0:
        return user_id_list, message_list
    else:
        return None, None

        

# Asynchronous function to send the messages
async def handle_tx_and_send_messages(json_payload: dict, user_wallets: dict, context: ContextTypes.DEFAULT_TYPE):

    # load from application realtoken data
    realtoken_data = context.application.bot_data["realtokens"]
    
    user_id_list, message_list = process_tx_file(json_payload, user_wallets, realtoken_data)

    # Check if the lists are None
    if user_id_list is None or message_list is None:
        return  # Exit the function early if there's nothing to process
    
    for user_id, message in zip(user_id_list, message_list):
        # Directly use chat_id to send the message
        await send_message(user_id, context, text=message)
        logger.info(f"Sale alert sent to {user_id}")
        
def get_token_decimals(token_address):
        for token_name, data in contract_data.items():
            if data.get('address') == token_address:
                return data.get('decimals', None), (token_name)  # None as default if 'decimals' not found
        return 18, ''  # Return None if no matching address is found



# Updated check_for_new_sales_event function
async def check_for_new_sales_event(context: ContextTypes.DEFAULT_TYPE):
    user_wallets = context.job.data['user_wallets']
    postgres_data = context.bot_data["POSTGRES_DATA"]

    processed_count = 0
    from pprint import pprint

    with get_pg_connection(*postgres_data) as pg_conn:
        
        while processed_count < MAX_EVENTS_PER_RUN:
            row = fetch_one_event_queue_row(pg_conn)
    
            if row is None:
                #if table is empty, we leave
                break
    
            event_id, created_at, json_payload = row
    
            try:
                await handle_tx_and_send_messages(json_payload, user_wallets, context)

                delete_event_by_id(pg_conn, event_id)
                pg_conn.commit()
                processed_count += 1
    
            except Exception as e:
                pg_conn.rollback()
                logger.exception(f"Failed processing event_queue id={event_id}")
                send_telegram_alert(f"Failed processing event_queue id={event_id}")
                break
    
    
def fetch_one_event_queue_row(pg_conn: PGConnection) -> Optional[Tuple[int, Any, Dict[str, Any]]]:
    """
    Fetch (and return) one row from public.event_queue if at least one exists.

    Returns:
        None if the table is empty, otherwise a tuple:
            (id, created_at, payload)

        - id: int
        - created_at: datetime (timezone-aware)
        - payload: dict (decoded from JSONB by psycopg2)

    """
    sql = """
        SELECT id, created_at, payload
        FROM public.event_queue
        ORDER BY id ASC
        LIMIT 1
    """

    # Using a cursor context manager ensures the cursor is closed properly.
    with pg_conn.cursor() as cur:
        cur.execute(sql)
        row = cur.fetchone()

    # row is either None (empty table) or a 3-tuple (id, created_at, payload)
    return row

def delete_event_by_id(pg_conn: PGConnection, event_id: int) -> None:
    """
    Delete one row from public.event_queue by its id.

    Args:
        pg_conn: Active PostgreSQL connection.
        event_id: ID of the event to delete.

    Notes:
        - This function does NOT commit automatically.
        - Caller is responsible for calling pg_conn.commit().
    """
    sql = """
        DELETE FROM public.event_queue
        WHERE id = %s
    """

    with pg_conn.cursor() as cur:
        cur.execute(sql, (event_id,))
