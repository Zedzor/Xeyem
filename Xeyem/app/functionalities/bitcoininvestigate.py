from requests import get
from math import ceil
import pandas as pd
import ssl
from bs4 import BeautifulSoup
import re
import plotly.express as px


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
    data = data.reset_index()
    # And finally we return the first row from the date column
    last_tx = f'{data.level_0.iloc[1]}'
    
    # The first transaction is at the last row on the last page
    # the amount of txs for page is 100
    if n_tx > 100: # if there is only 1 page we already have it
        page_n = ceil(n_tx / 100)
        url += f'?page={page_n}'

        data = pd.read_csv(url+'&format=csv')
        data = data.reset_index()

    first_tx = f'{data.level_0.iloc[-1]}'
        
    return (first_tx,last_tx)

def __parse_strlist(sl):
    splitted = re.split(r',(?![^\[\]]*\])',sl)    
    values_list = [ re.split(",", item[1:-1]) for item in splitted ]

    return values_list

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
    
def balance_time(address: str) -> dict:
    url = f'https://bitinfocharts.com/bitcoin/address/{address}'
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
    plt_div = ''
    
    res = get(url=url, headers=headers)
    if res.ok:
        soup = BeautifulSoup(res.text, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if 'd = new Dygraph(document.getElementById("gcontainer")' in script.text:
                StrList = script.text
                StrList = '[[' + StrList.split('[[')[-1]
                StrList = StrList.split(']]')[0] +']]'
                StrList = StrList.replace("new Date(", '').replace(')','')
                StrList = StrList[1:-1]
                dataList = __parse_strlist(StrList)
                df = pd.DataFrame(dataList, columns=['Date','Balance', 'USD', 'Other'])
                df['Date'] = pd.to_datetime(df['Date'], unit='ms')
                df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce')
                df.drop(['USD','Other'], axis=1, inplace=True)
                fig = px.line(data_frame=df, x='Date', y='Balance')
                plt_div = fig.to_html(include_plotlyjs=False, full_html=False, div_id="plt_div")
                
    if not plt_div:
        plt_div = "Couldn't get balance through time"
    
    return {'balance_time': plt_div}
