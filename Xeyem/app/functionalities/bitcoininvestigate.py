from requests import get
from math import ceil
import pandas as pd
import ssl

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

def __get_first_and_last_tx(address: str, n_tx: int) -> tuple:
    url = f'https://www.walletexplorer.com/address/{address}'
    # To avoid certificate errors
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # We use pandas to get the LAST transaction
    data = pd.read_csv(url+'?format=csv')
    data = data.reset_index() # we reset the index
    # And finally we return the first row from the date column
    last_tx = f'{data.level_0.iloc[1]}'
    
    # The first transaction is at the last row on the last page
    # the amount of txs for page is 100
    if n_tx <= 100: # if there is only 1 page we already have it
        first_tx = f'{data.level_0.iloc[-1]}'
    else:
        page_n = ceil(n_tx / 100)
        url += f'?page={page_n}'

        data = pd.read_csv(url+'&format=csv')
        data = data.reset_index()

        first_tx = f'{data.level_0.iloc[-1]}'
        
    return (first_tx,last_tx)

def get_common_info(address: str) -> dict:
    res = get(f'https://blockchain.info/rawaddr/{address}')
    if res.ok:
        json_response = res.json()
        txs_n = len(json_response['txs'])
        # if txs_n == 100:
        #     res2 = get(f'https://blockchain.info/rawaddr/{address}?offset=100')
        #     if res2.ok:
        #         json_response['txs'] += res2.json()['txs']
        #         txs_n = len(res2.json()['txs'])

        return __blockchain_info_parser(json_response, address)

def balance(info: dict) -> dict:   
    final_balance = info['final_balance'] / SATOSHI_DIVISOR if info is not None else 'Error al obtener balance'
    return {
        'balance': final_balance,
    }
    
def fst_lst_transaction(info: dict) -> dict:
    if info is not None:
        first_transaction,last_transaction = __get_first_and_last_tx(info['address'], info['n_tx'])
    else:
        first_transaction = last_transaction = "Error al obtener fecha"
        
    return {
        'first_transaction': first_transaction,
        'last_transaction': last_transaction,
    }