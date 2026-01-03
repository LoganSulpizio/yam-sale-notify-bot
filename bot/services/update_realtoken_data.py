from typing import Dict, Any
from telegram.ext import ContextTypes
from bot.config.settings import REALTOKENS_LIST_URL
from bot.services.fetch_json import fetch_json
from bot.services.utilities import list_to_dict_by_uuid
from bot.services.send_telegram_alert import send_telegram_alert

import logging
logger = logging.getLogger(__name__)


async def job_update_realtoken_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Periodic Telegram job that fetches the latest RealToken list and stores it
    in the bot's shared application data.

    The data is fetched from REALTOKENS_LIST_URL, transformed into a dictionary
    indexed by token uuid, and stored under:

        context.application.bot_data["realtokens"]

    This allows all handlers and jobs to access up-to-date RealToken metadata
    without refetching it on every request.
    """
    try:
        # Fetch raw JSON data from the RealTokens API
        raw_data: Any = fetch_json(REALTOKENS_LIST_URL)

        # Convert list response to a dict indexed by uuid
        realtoken_data: Dict[str, Dict[str, Any]] = list_to_dict_by_uuid(raw_data)

        if not realtoken_data:
            logger.error("unexpected issue in RealToken update: update skipped")
            return

        # Store data in shared bot application state
        context.application.bot_data["realtokens"] = realtoken_data

        logger.info("RealToken data successfully updated (%d tokens)", len(realtoken_data))

    except Exception as e:
        logger.exception("Failed to update RealToken data")
        send_telegram_alert(f"Failed to update RealToken data: {e}")

