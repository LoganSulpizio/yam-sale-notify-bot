import json
import os
import requests
from web3 import Web3
from bot.config.settings import USER_PREF_LANGUAGE_FILE, USER_WALLET_FILE, BLOCKCHAIN_RESSOURCES, TRANSLATIONS_PATH

# Language mapping dictionary
language_mapping = {
    '1': 'EN',
    '2': 'FR',
    '3': 'ES'
}

# Load translations from the JSON file with UTF-8 encoding
def load_translations():
    with open(TRANSLATIONS_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)
translations = load_translations()

# Load blockchain ressources (abi, contract addresses) from the JSON file with UTF-8 encoding
def load_blockchain_ressources():
    with open(BLOCKCHAIN_RESSOURCES, 'r', encoding='utf-8') as file:
        return json.load(file)

#def load_db_path():
#    with open('config.json', 'r', encoding='utf-8') as file:
#        config = json.load(file)
#        return config['db_path']
#
def load_w3():
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
        return Web3(Web3.HTTPProvider(config['w3_url_1']))

def load_user_languages():
    if os.path.exists(USER_PREF_LANGUAGE_FILE):
        with open(USER_PREF_LANGUAGE_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Convert keys from strings back to integers
            return {int(user_id): language for user_id, language in data.items()}
    return {}

# Save user language preferences to the JSON file
def save_user_languages(user_languages):
    with open(USER_PREF_LANGUAGE_FILE, 'w', encoding='utf-8') as file:
        json.dump(user_languages, file, ensure_ascii=False, indent=4)

def load_user_wallet():
    if os.path.exists(USER_WALLET_FILE):
        with open(USER_WALLET_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Convert keys from strings back to integers
            return {int(user_id): wallet for user_id, wallet in data.items()}
    return {}

# Save user wallet to the JSON file
def save_user_wallet(user_wallet):
    with open(USER_WALLET_FILE, 'w', encoding='utf-8') as file:
        json.dump(user_wallet, file, ensure_ascii=False, indent=4)

# Function to send messages with specific parameters
async def send_message(chat_id: int, context, text: str):
    params = {
        'disable_web_page_preview': True,
        'parse_mode': 'Markdown'
    }
    await context.bot.send_message(chat_id=chat_id, text=text, **params)

def compute_path(path_components: list):

    # Get the system drive dynamically
    working_drive = os.path.splitdrive(os.path.abspath(os.sep))[0]

    # Construct the path
    path = os.path.join(working_drive, os.sep, *path_components)

    return path

def load_DataProperty():
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
    path_DataProperty = config['DataProteryPath']
    
    with open(path_DataProperty, 'r') as file:
        data_dict = json.load(file)
    # Iterate through the dictionary and remove the key 'gnosisImplementationContractAbi'
    for key in data_dict:
        if 'gnosisImplementationContractAbi' in data_dict[key]:
            del data_dict[key]['gnosisImplementationContractAbi']
    #write_log("DataProperty loaded successfully", "logfile/logfile_YAMSaleNotifyBot.txt")
    return data_dict

async def reload_DataProperty(context):
    try:
        new_data_property = load_DataProperty()
        
        # Update the DataProperty in the job's context
        context.job.data['DataProperty'].update(new_data_property)

    except Exception as e:
        pass
        # Log any failure during the update
        #write_log(f"Failed to reload DataProperty: {str(e)}", "logfile/logfile_YAMSaleNotifyBot.txt")
