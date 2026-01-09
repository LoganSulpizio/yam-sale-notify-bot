from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, BotCommandScopeChat
from telegram.ext import ContextTypes, ConversationHandler
from bot.services.utilities import translations, language_mapping, save_user_languages, send_message
import asyncio

from bot.services.logging_config import get_logger
logger = get_logger(__name__)

# Conversation states
LANGUAGE_SELECTION = 1

# Dictionary to store user language preferences (loaded from file)
user_languages = {}

def initialize_user_languages(loaded_languages):
    global user_languages
    user_languages = loaded_languages

# Getter for user_languages
def get_user_languages():
    return user_languages

# Function to get the correct translation for the user's language with fallback to English
def translate(user_id, key, **kwargs):
    # Get the user's selected language or default to English
    language = user_languages.get(user_id, 'EN')
    
    # Try to get the translation in the user's language
    translation = translations.get(language, {}).get(key)
    
    if translation is None:
        # If not found, fallback to English
        translation = translations['EN'].get(key, '')

    # Return the translation with formatted values if any are provided
    return translation.format(**kwargs)

async def setlanguage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    # Inline keyboard buttons for language selection
    keyboard = [
        [InlineKeyboardButton("English", callback_data='1')],
        [InlineKeyboardButton("Français", callback_data='2')],
        [InlineKeyboardButton("Español", callback_data='3')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    select_language_message = translate(user_id, 'select_language_prompt')
    
    # Send the message with the inline keyboard attached
    await update.message.reply_text(select_language_message, reply_markup=reply_markup)
    
    return LANGUAGE_SELECTION  # Move to LANGUAGE_SELECTION state

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    text = query.data  # Get the data from the callback

    if text in language_mapping:
        user_languages[user_id] = language_mapping[text]
        logger.info(f"user {user_id} has set its language to {language_mapping[text]}")
        save_user_languages(user_languages)  # Save the updated preferences
        language_set_message = translate(user_id, 'language_set')
        await query.answer()  # Acknowledge the callback

        # Update the bot commands for this user, with await
        await update_bot_commands(user_id, context)

        await send_message(user_id, context, language_set_message)

        return ConversationHandler.END  # End the conversation
    else:
        invalid_selection_message = translate(user_id, 'invalid_selection')
        await send_message(user_id, context, invalid_selection_message)
        return LANGUAGE_SELECTION  # Stay in the same state

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id  # Extract the user ID
    await send_message(user_id, context, "Operation cancelled.")  # Use the user ID as chat_id
    return ConversationHandler.END  # End the conversation

async def update_bot_commands(user_id, context):
    # Retrieve translated commands based on user's language
    commands = [
        BotCommand("setwallet", translate(user_id, 'menu_setwallet')),
        BotCommand("getcurrentoffers", translate(user_id, 'menu_getcurrentoffers')),
        BotCommand("checkinfo", translate(user_id, 'menu_checkinfo')),
        BotCommand("setlanguage", translate(user_id, 'menu_setlanguage')),
        BotCommand("about", translate(user_id, 'menu_about'))
    ]

    # Update the bot commands dynamically for the specific user
    await context.bot.set_my_commands(commands, scope=BotCommandScopeChat(user_id))

def reinitialize_user_commands(context):
    loop = asyncio.get_event_loop()  # Get the existing event loop

    for user_id, language in user_languages.items():
        commands = [
            BotCommand("setwallet", translate(user_id, 'menu_setwallet')),
            BotCommand("getcurrentoffers", translate(user_id, 'menu_getcurrentoffers')),
            BotCommand("checkinfo", translate(user_id, 'menu_checkinfo')),
            BotCommand("setlanguage", translate(user_id, 'menu_setlanguage')),
            BotCommand("about", translate(user_id, 'menu_about'))
        ]

        try:
            # Use loop.run_until_complete to run the async set_my_commands in sync context
            loop.run_until_complete(context.bot.set_my_commands(commands, scope=BotCommandScopeChat(user_id)))
        except Exception as e:
            # Log the exception (you can customize this to your logging system)
            logger.error(f"Failed to initialize commands for user {user_id}: {e}")
            # Skip to the next user if an error occurs
            continue