from typing import final
from requests import get

SATOSHI_DIVISOR = 100000000

def __blockchain_info_parser(json_response: dict, address: str) -> dict:
    aux_list = []
    # Parsing transaction list
    for tx in json_response['txs']:
        is_in_tx = False
        for entry in tx['inputs']:
            if entry['prev_out']['addr'] == address:
                is_in_tx = True
        tx['is_in_tx'] = is_in_tx
        aux_list.append(tx)
    json_response['txs'] = sorted(aux_list, key=lambda d: d['time'])
    return  json_response

def get_common_info(address: str) -> dict:
    res = get(f'https://blockchain.info/rawaddr/{address}')
    if res.ok:
        json_response = res.json()
        # txs_n = len(json_response['txs'])
        # while txs_n == 100:
        #     res2 = get(f'https://blockchain.info/rawaddr/{address}?offset=100')
        #     if res2.ok:
        #         json_response['txs'] += res2.json()['txs']
        #         txs_n = len(res2.json()['txs'])
        #     else:
        #         break
        return __blockchain_info_parser(json_response, address)

def balance(info: dict) -> dict:   
    final_balance = info['final_balance'] / SATOSHI_DIVISOR if info is not None else 'Error al obtener balance'
    return {
        'balance': final_balance,
    }