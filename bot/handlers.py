from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from eth_utils import is_address, to_checksum_address
from bot.YAM_DB_handlers.get_all_offer_ids_by_seller import get_all_offer_ids_by_seller
from bot.w3_interaction.get_offer import get_offers_multicall
from bot.offer_handlers.handle_raw_offer import handle_raw_offer
from bot.language_handlers import translate, get_user_languages, setlanguage
from bot.services.utilities import send_message, save_user_wallet

from bot.services.logging_config import get_logger
logger = get_logger("bot.main")

# Conversation states
WALLET_INPUT = 2

# Dictionaries to store user data (initialized from file)
user_wallets = {}

def initialize_user_wallet(loaded_wallets):
    global user_wallets
    user_wallets = loaded_wallets


# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    about_message = (
        f'\\[_EN_] *Welcome!*\n' +
        f'\\[_FR_] *Bienvenue!*\n' + 
        f'\\[_ES_] *¡Bienvenido!*'
        )
    await send_message(user_id, context, about_message)
    # Call the setlanguage function to start the language selection process
    return await setlanguage(update, context)

# Function to handle the /about command
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    about_message = translate(user_id, 'about') + "[Github](https://github.com/LoganSulpizio/YAMSaleNotifyBot)"
    await send_message(user_id, context, about_message)

# Function to handle the /getcurrentoffers command
async def getcurrentoffers(update: Update, context: ContextTypes.DEFAULT_TYPE, DataProperty: dict, db_path:str, w3) -> None:
    user_id = update.effective_user.id
    user_wallet = user_wallets.get(user_id, None)

    logger.info(f"getcurrentoffers used by user {user_id}")

    offer_ids = get_all_offer_ids_by_seller(db_path, user_wallet, ['InProgress'])
    raw_offers = get_offers_multicall(w3, offer_ids)

    message = '*' + translate(user_id, 'current_listed_offer') + '*'
    
    total_at_sale = 0
    total_number_of_token_at_sale = 0

    for raw_offer in raw_offers:
        offer = handle_raw_offer(raw_offer, DataProperty)
        if isinstance(offer, dict) and offer['remaining_amount'] != 0:
            line = (
                translate(user_id, 'id_icon') + f" [{offer['id']}](https://yambyofferid.netlify.app/?offerId={offer['id']}) " +
                translate(user_id, 'house_icon') + f" *{offer['offer_token']}*\n" +
                translate(user_id, 'money_icon') + f" *{round(offer['price'], 2)}* {offer['buyer_token']} - *{round(offer['remaining_amount'], 2)}* token(s)\n\n"
            )
        else:
            line = ''
        message += line
        total_at_sale += offer['price'] * offer['remaining_amount']
        total_number_of_token_at_sale += offer['remaining_amount']

    # case if no current sales:
    if message == '*' + translate(user_id, 'current_listed_offer') + '*':
        message += translate(user_id, 'no_listed_offers')
    else:
        message += translate(user_id,
                            'total_current_sales',
                            total_number_of_token_at_sale = round(total_number_of_token_at_sale, 2),
                            total_at_sale = round(total_at_sale, 2),
                            )

    await send_message(user_id, context, message)

# Function to handle the /setwallet command
async def setwallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    wallet_prompt_message = translate(user_id, 'set_your_wallet')
    await send_message(user_id, context, wallet_prompt_message)
    return WALLET_INPUT  # Move to WALLET_INPUT state

# Function to handle wallet input
async def handle_wallet_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    wallet_address = update.message.text.strip()

    # Check if the wallet address is valid
    if is_address(wallet_address):
        # Convert to checksummed address
        checksummed_address = to_checksum_address(wallet_address)
        
        # Store the checksummed wallet address in the dictionary
        user_wallets[user_id] = checksummed_address
        logger.info(f"user {user_id} has set its wallet to {checksummed_address}")
        save_user_wallet(user_wallets)

        wallet_set_message = translate(user_id, 'wallet_has_been_set')
        await send_message(user_id, context, wallet_set_message)
    else:
        # If the address is invalid, send an error message
        invalid_wallet_message = translate(user_id, 'invalid_wallet_format')
        await send_message(user_id, context, invalid_wallet_message)

        return WALLET_INPUT  # Stay in the WALLET_INPUT state for re-entry

    return ConversationHandler.END  # End the conversation

# Function to handle the /checkinfo command
async def checkinfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    # Retrieve user's language and wallet information
    user_languages = get_user_languages()
    user_language = user_languages.get(user_id, None)
    user_wallet = user_wallets.get(user_id, None)

    if user_language is not None:
        language_message = translate(user_id, 'check_language', user_language=user_language) + '\n'
    else:
        language_message = translate(user_id, 'check_language_none') + '\n'
    
    if user_wallet is not None:
        wallet_message = translate(user_id, 'check_wallet', user_wallet=user_wallet)
    else:
        wallet_message = translate(user_id, 'check_wallet_none')

    await send_message(user_id, context, language_message + wallet_message)

# You can add more command handlers here as you expand your bot's functionality
