from telegram.ext import Application, CommandHandler, CallbackQueryHandler, JobQueue, MessageHandler, filters, ConversationHandler
from bot.config.settings import REALTOKENS_LIST_URL, FRENQUENCY_UPDATING_REALTOKEN_DATA
from bot.services.utilities import load_user_languages, load_user_wallet, list_to_dict_by_uuid
from bot.services.fetch_json import fetch_json
from bot.services.send_telegram_alert import send_telegram_alert
from bot.services.error_handler import global_error_handler
from bot.bot_handlers.language_handlers import setlanguage, handle_language_selection, cancel, LANGUAGE_SELECTION, initialize_user_languages, reinitialize_user_commands
from bot.bot_handlers.handlers import start, about, setwallet, handle_wallet_input, checkinfo, WALLET_INPUT, initialize_user_wallet, getcurrentoffers
from bot.core.process_tx_file import check_for_new_sales_event
from bot.services.on_post_shutdown import on_post_shutdown
from bot.services.update_realtoken_data import job_update_realtoken_data
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
from functools import partial
from datetime import timedelta
import os

from bot.services.logging_config import get_logger
logger = get_logger("bot.main")

from dotenv import load_dotenv
load_dotenv()

# Suppress PTBUserWarning related to CallbackQueryHandler
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

def main() -> None:

    token_yam_sale_notify_bot = os.environ["YAM_SALE_NOTIFY_BOT_TOKEN"]
    RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER") == "1"
    if RUNNING_IN_DOCKER:
         db_path = "yam_indexing_db/yam_events.db"
    else:
         db_path = os.environ["YAM_INDEXING_DB_PATH"]

    # Build the Telegram application
    job_queue = JobQueue()
    application = (
        Application.builder()
        .token(token_yam_sale_notify_bot)
        .job_queue(job_queue)
        .post_shutdown(on_post_shutdown)
        .build()
    )

    # Fetch RealToken data (as-is from the API)
    realtoken_data = list_to_dict_by_uuid(fetch_json(REALTOKENS_LIST_URL))

    # Load user language preferences and initialize in the language_handlers module
    user_languages = load_user_languages()
    initialize_user_languages(user_languages)
    
    # initialize the custom commands according to each user's preferred language
    reinitialize_user_commands(application)
    logger.info("Custom commands according to each user's preferred language have been set")

    # Load user wallet and initialize in the handlers module
    user_wallets = load_user_wallet()
    initialize_user_wallet(user_wallets)

    # Register the global error handler
    application.add_error_handler(global_error_handler)

     # Store services in bot_data so all handlers can access them
    application.bot_data["realtokens"] = realtoken_data
    
    # Register the conversation handler for /setlanguage and /start
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('setlanguage', setlanguage),
            CommandHandler('start', start)  # Start also triggers language selection
        ],
        states={
            LANGUAGE_SELECTION: [CallbackQueryHandler(handle_language_selection)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True,    # Ensures each user has their own conversation
        per_chat=True     # Ensures each chat has its own conversation context
    )
    application.add_handler(conv_handler)
    # Register the /about command handler
    application.add_handler(CommandHandler("about", about))
    # Register the /currentsales command handler
    application.add_handler(CommandHandler("getcurrentoffers", partial(getcurrentoffers, db_path=db_path)))
    # Register the /checkinfo command handler
    application.add_handler(CommandHandler("checkinfo", checkinfo))
    # Register the conversation handler for /setwallet
    wallet_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('setwallet', setwallet)],
        states={
            WALLET_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_input)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True,    # Ensures each user has their own conversation
        per_chat=True     # Ensures each chat has its own conversation context
    )
    application.add_handler(wallet_conv_handler)
    # Schedule the job to run every 8 seconds
    job_queue.run_repeating(
        check_for_new_sales_event,
        interval=10,
        first=10,  # first run after 10 seconds
        name="check for new sales event job",
        data={
            'user_wallets': user_wallets,  # Passes user_wallets to the job's context
            'path_transaction_queue_folder': 'transactions_queue/'  # Passes the folder path to the job's context
        }
    )

    # register job to update realtoken data
    application.job_queue.run_repeating(
        job_update_realtoken_data,
        interval=timedelta(days=FRENQUENCY_UPDATING_REALTOKEN_DATA),
        first=timedelta(days=FRENQUENCY_UPDATING_REALTOKEN_DATA),
        name="update realtoken data job",
    )

    logger.info("Starting bot polling…")
    print("Starting bot polling…")
    send_telegram_alert("Yam sale notify bot: Starting bot polling…")
    application.run_polling()

if __name__ == "__main__":
    main()