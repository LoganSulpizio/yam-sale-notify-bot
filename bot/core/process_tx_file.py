import os

if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram.ext import ContextTypes
from bot.bot_handlers.language_handlers import translate
from bot.services.utilities import send_message, load_blockchain_ressources
import json

from bot.services.logging_config import get_logger
logger = get_logger(__name__)

contract_data = load_blockchain_ressources()


# Read the tx json files
def process_tx_file(path_file_event: str, user_wallets: dict, realtoken_data: dict):
    
    with open(path_file_event, 'r') as file:
        data = json.load(file)

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

        if buyerToken in stablecoin_YAM:
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

    logger.info(f"{tx_hash} has been processed")
    
    # delete file when it has been processed
    #os.remove(path_file_event)

    # Check if the destination file exists
    #destination = os.path.join('logfile', os.path.basename(path_file_event))
    #if os.path.exists(destination):
    #    os.remove(destination)  # Remove the existing file
    #shutil.move(path_file_event, 'logfile')
            
    if len(user_id_list) > 0:
        return user_id_list, message_list
    else:
        return None, None

        

# Asynchronous function to send the messages
async def handle_tx_and_send_messages(path_file_event: str, user_wallets: dict, context: ContextTypes.DEFAULT_TYPE):

    # load from application realtoken data
    realtoken_data = context.application.bot_data["realtokens"]
    
    user_id_list, message_list = process_tx_file(path_file_event, user_wallets, realtoken_data)

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
    path_transaction_queue_folder = context.job.data['path_transaction_queue_folder']
    
    # Get the list of files in the specified folder
    try:
        with os.scandir(path_transaction_queue_folder) as entries:
            json_files = [entry.name for entry in entries if entry.name.endswith('.json')]
        
        if json_files:
            for file in json_files:
                path_file_event = os.path.join(path_transaction_queue_folder, file)
                # Trigger the asynchronous function to process the file and send messages
                await handle_tx_and_send_messages(path_file_event, user_wallets, context)
    
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError: {e}")
        raise FileNotFoundError(f"The folder '{path_transaction_queue_folder}' does not exist.")