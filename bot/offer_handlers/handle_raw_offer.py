from bot.services.utilities import load_blockchain_ressources
contract_data = load_blockchain_ressources()

def handle_raw_offer(raw_offer: list, DataProperty: dict):

    if raw_offer[0] is None:
        return raw_offer

    offer = {}

    offer['id'] = raw_offer[6]
    offer['seller_address'] = raw_offer[2]
    offer['buyer_address'] = raw_offer[3]

    ### Sale offer ###
    if raw_offer[1] in [contract['address'] for contract in contract_data.values() if 'address' in contract]:
        buyer_token = next((key for key, contract in contract_data.items() if contract.get('address') == raw_offer[1]), None)

        offer['offer_token'] = DataProperty[raw_offer[0]]['shortName']
        offer['buyer_token'] = buyer_token

        decimals_realtoken = 18
        if raw_offer[0] == '0x0675e8F4A52eA6c845CB6427Af03616a2af42170': decimals_realtoken = 9 # RWA has 9 decimals and not 18

        offer['price'] = raw_offer[4] / 10 ** contract_data.get(buyer_token, {}).get('decimals', 18)
        offer['remaining_amount'] = raw_offer[5] / 10 ** decimals_realtoken
    else:
        return None

    return offer


### test case ###
if __name__ == '__main__':

    import json
    from web3 import Web3
    from web3.exceptions import Web3RPCError
    from YAM_DB_handlers.get_all_offer_ids_by_seller import get_all_offer_ids_by_seller
    from bot._contract_data import contract_data
    from w3_interaction.get_offer import get_multiple_offers
    import asyncio
    
    with open('config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
        db_path = config["db_path"]
        w3_url = config["w3_url_1"]
    
    w3 = Web3(Web3.HTTPProvider(w3_url))
    
    offer_ids = get_all_offer_ids_by_seller(db_path, "0xA99e07efB152321117653a16727BF6Bc02106892", ['InProgress'])
    # Run the get_multiple_offers function
    results = asyncio.run(get_multiple_offers(w3, offer_ids))

    with open("D:\DeFi\RealtEcosystem\DataProperty.json", 'r', encoding='utf-8') as file:
        DataProperty = json.load(file)

    for raw_offer in results:
        offer = handle_raw_offer(raw_offer, DataProperty)
        from pprint import pprint
        pprint(offer)