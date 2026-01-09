
"""Application configuration and constants"""
from pathlib import Path

# RealToken public endpoints
REALTOKENS_LIST_URL = "https://api.realtoken.community/v1/token"

FRENQUENCY_UPDATING_REALTOKEN_DATA = 2 # in days

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRANSLATIONS_PATH = PROJECT_ROOT / "translations" / "translations.json"
USER_DATA_PATH = PROJECT_ROOT / "user_configurations" / "user_configurations.json"
LOG_DIR = PROJECT_ROOT / "logs"

# File path to store user language preferences and wallet set up
USER_PREF_LANGUAGE_FILE = PROJECT_ROOT / "user_configurations" / "user_languages.json"
USER_WALLET_FILE = PROJECT_ROOT / "user_configurations" / "user_wallet.json"

BLOCKCHAIN_RESSOURCES = PROJECT_ROOT / "ressources" / "blockchain_contract_data.json"


MULTICALLV3_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"