from bot.services.utilities import load_blockchain_ressources
contract_data = load_blockchain_ressources()

def handle_raw_offer(raw_offer: list, realtoken_data: dict):

    if raw_offer[0] is None:
        return raw_offer

    offer = {}

    offer['id'] = raw_offer[6]
    offer['seller_address'] = raw_offer[2]
    offer['buyer_address'] = raw_offer[3]

    ### Sale offer ###
    if raw_offer[1] in [contract['address'] for contract in contract_data.values() if 'address' in contract]:
        buyer_token = next((key for key, contract in contract_data.items() if contract.get('address') == raw_offer[1]), None)

        offer['offer_token'] = realtoken_data[raw_offer[0].lower()]['shortName']
        offer['buyer_token'] = buyer_token

        decimals_realtoken = 18
        if raw_offer[0] == '0x0675e8F4A52eA6c845CB6427Af03616a2af42170': decimals_realtoken = 9 # RWA has 9 decimals and not 18

        offer['price'] = raw_offer[4] / 10 ** contract_data.get(buyer_token, {}).get('decimals', 18)
        offer['remaining_amount'] = raw_offer[5] / 10 ** decimals_realtoken
    else:
        return None

    return offer