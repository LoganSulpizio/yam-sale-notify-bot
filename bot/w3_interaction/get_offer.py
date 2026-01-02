import sys
import os

import asyncio
import time
from web3 import Web3
from web3.exceptions import Web3RPCError
from typing import List, Optional, Tuple, Any
from bot.services.utilities import send_message, save_user_wallet

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

### test case ###
if __name__ == '__main__':

    import json
    from web3 import Web3
    from web3.exceptions import Web3RPCError
    from YAM_DB_handlers.get_all_offer_ids_by_seller import get_all_offer_ids_by_seller
    from pprint import pprint
    
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
        db_path = config["db_path"]
        w3_url = config["w3_url_3"]
    
    w3 = Web3(Web3.HTTPProvider(w3_url))

    #offer_ids = get_all_offer_ids_by_seller(db_path, "0xA99e07efB152321117653a16727BF6Bc02106892", ['InProgress'])
    offer_ids = get_all_offer_ids_by_seller(db_path, "0xB9F7eCDD3475A7BFE4BEc60BD70A936EbE1299FD", ['InProgress'])
    #offer_ids = [99218, 108281, 64586, 1111]
    print('ready')
    print(offer_ids)
    
    # Run the get_multiple_offers function (one resquet per ID in async mode)
    results = get_offers_multicall(w3, offer_ids)
    pprint(results)


##########################################
######## below code is obsolete ##########
##########################################

async def get_offer(w3: Web3, offer_id: int) -> Optional[List]:
    """
    Fetch an offer based on its ID from the YAM contract.
    The call on the YAM contract is 'showOffer'

    Args:
        w3 (Web3): An instance of the Web3 connection.
        offer_id (int): The ID of the offer to retrieve.

    Returns:
        Optional[List]: The offer data as a list if successful, None if not found or invalid.
    """
    # Instantiate the token contract
    token_contract = w3.eth.contract(address=contract_data['YAM']['address'], abi=contract_data['YAM']['abi'])

    try:
        # Redirect stderr to suppress the error message (Web3RPCError prints at the console an error when there is an Web3RPCError. I didn't manage removing it "nicely" so I do't it the hard way...)
        with open(os.devnull, 'w') as devnull:
            old_stderr = sys.stderr
            sys.stderr = devnull
            try:
                # Call the showOffer function
                offer = token_contract.functions.showOffer(offer_id).call()
                return offer
            finally:
                # Restore stderr
                sys.stderr = old_stderr

    except (ValueError, Web3RPCError) as e:
        logger(f"Exception in get_offer for offer id {offer_id}: {e}")
        return None

async def get_multiple_offers(w3: Web3, offer_ids: List[int]) -> List[Optional[List]]:
    """
    Fetch multiple offers concurrently based on their IDs with rate limiting.

    Args:
        w3 (Web3): An instance of the Web3 connection.
        offer_ids (List[int]): A list of offer IDs to retrieve.

    Returns:
        List[Optional[List]]: A list of offer details with IDs appended.
    """
    # Rate limiting parameters
    max_requests_per_second = 15
    min_interval = 1.0 / max_requests_per_second  # Time between requests in seconds
    
    tasks = []
    
    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_requests_per_second)
    last_request_time = time.time()
    
    async def rate_limited_get_offer(offer_id: int) -> Any:
        nonlocal last_request_time
        
        async with semaphore:
            # Calculate time since last request
            current_time = time.time()
            elapsed = current_time - last_request_time
            
            # If needed, wait to maintain rate limit
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            
            # Update last request time and make the request
            last_request_time = time.time()
            return await get_offer(w3, offer_id)
    
    # Create rate-limited tasks
    for offer_id in offer_ids:
        tasks.append(rate_limited_get_offer(offer_id))
    
    # Await all tasks concurrently and collect results
    results = await asyncio.gather(*tasks)
    
    # Append offer_id to each result
    final_results = []
    for offer_id, offer in zip(offer_ids, results):
        if offer is not None:
            final_results.append(offer + [offer_id])
        else:
            final_results.append([None, offer_id])
    
    logger(f"{len(final_results)} offers retrieved from w3 rpc")
    
    return final_results

### test case ###
if __name__ == '__main__':
    pass
    #w3 = Web3(Web3.HTTPProvider(w3_url))
    #offer_ids = [99218, 108281, 64586, 1111]
    #results = asyncio.run(get_multiple_offers(w3, offer_ids))