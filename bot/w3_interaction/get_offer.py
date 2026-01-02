import sys
import os

import asyncio
import time
from web3 import Web3
from web3.exceptions import Web3RPCError
from typing import List, Optional, Tuple, Any

from bot.services.logging_config import get_logger
logger = get_logger("bot.main")

from bot.services.utilities import load_blockchain_ressources
contract_data = load_blockchain_ressources()
    
def get_offers_multicall(w3: Web3, offer_ids: List[int]) -> List[List[Any]]:
    """
    Fetch multiple offers in a single request using Multicall3 from the YAM contract.
    
    Args:
        w3 (Web3): An instance of the Web3 connection.
        offer_ids (List[int]): List of offer IDs to retrieve.
    
    Returns:
        List[List[Any]]: List of successfully retrieved offers with their data.
            Each offer is returned as a list containing:
            [address, address, address, address, uint256, uint256, offer_id]
            The last element (offer_id) is appended to the original response for reference.
            Only successful calls are included in the returned list.
    """
    # Get the token contract
    token_contract = w3.eth.contract(address=contract_data['YAM']['address'], abi=contract_data['YAM']['abi'])
    
    # Get the Multicall3 contract
    multicall3 = w3.eth.contract(address=contract_data['Multicall3']['address'], abi=contract_data['Multicall3']['abi'])
    
    # Prepare the calls
    calls = []
    for offer_id in offer_ids:
        # Get the encoded function call data
        call_data = token_contract.functions.showOffer(offer_id)._encode_transaction_data()
        calls.append({
            'target': contract_data['YAM']['address'],
            'callData': call_data,
            'allowFailure': True
        })

    # Execute all calls in a single transaction
    raw_offers = multicall3.functions.aggregate3(calls).call()
    offers = []
    for raw_offer, offer_id in zip(raw_offers, offer_ids):
        if raw_offer[0]:
            decoded_offer = decode_multicall3_YAM_show_offer(raw_offer[1])
            offers.append(list(decoded_offer) + [offer_id])
    logger.info(f"multicall fetched for {len(offer_ids)} offer IDs. {len(offers)} offers successfully retrieved")
   
    return offers

def decode_multicall3_YAM_show_offer(binary_data: bytes) -> Tuple[str, str, str, str, int, int]:
    """
    Decode binary data from multicall3 result into:
    - 4 Ethereum addresses (20 bytes each)
    - 2 uint256 values (32 bytes each)
    
    Returns a tuple of (address1, address2, address3, address4, uint256_1, uint256_2)
    """
    # Check if we have enough data (4 addresses = 80 bytes + 2 uint256 = 64 bytes)
    if len(binary_data) < 144:
        raise ValueError(f"Binary data too short: {len(binary_data)} bytes, expected at least 144 bytes")
    
    # Extract addresses (20 bytes each)
    address1 = Web3.to_checksum_address('0x' + binary_data[12:32].hex())
    address2 = Web3.to_checksum_address('0x' + binary_data[44:64].hex())
    address3 = Web3.to_checksum_address('0x' + binary_data[76:96].hex())
    address4 = Web3.to_checksum_address('0x' + binary_data[108:128].hex())
    
    # Extract uint256 values (32 bytes each)
    # Assuming they start after the 4 addresses (which would be at offset 128)
    uint256_1 = int.from_bytes(binary_data[128:160], byteorder='big')
    uint256_2 = int.from_bytes(binary_data[160:192], byteorder='big')
    
    return (address1, address2, address3, address4, uint256_1, uint256_2)