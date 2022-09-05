from urllib import response
from requests import get
from math import ceil
import pandas as pd
import ssl
from bs4 import BeautifulSoup
import re
import plotly.express as px
from fp.fp import FreeProxy
from datetime import datetime


BITCOINABUSE_API_TOKEN = 'xpq3nxlgXOcyafM6QaBCXCu3oKjArNT9Q2bZfzIX'
SATOSHI_DIVISOR = 100000000

def __blockchain_info_parser(json_response: dict, address: str) -> dict:
    aux_list = []
    # We sort the list by time
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

def __get_different_proxy(proxies: list) -> str:
    """Function to get a different proxy from the list avoiding proxy repetition"""
    proxy = FreeProxy(rand=True).get()
    while proxy in proxies:
        proxy = FreeProxy(rand=True).get()
    return proxy

def __get_wallets_from_walletexplorer():
    url = 'https://www.walletexplorer.com'
    proxy = __get_different_proxy([])
    res = get(url=url, proxies={'http': proxy})
    if res.ok:
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'class': 'serviceslist'})
        table = table.tr 
        wallets = {}
        for services in table.children:
            service_type = re.sub(r'/\w+$', '', services.h3.string.replace(':', '').lower())
            for service in services.ul.children:
                if service.name == 'li':
                    urls = [url + a['href'] for a in service.find_all('a')]
                    wallets[service.a.string] = {
                        'type': service_type,
                        'urls': urls
                    }
        return wallets 
    else:
        return None

def __get_label_from_address(address: str) -> str:
    res = get(f'https://www.walletexplorer.com/address/{address}')
    if res.ok:
        soup = BeautifulSoup(res.text, 'html.parser')
        div = soup.find('div', {'class': 'walletnote'})
        wallet =  div.find('a')['href'].split('/')[-1]
        return wallet
    else:
        return None

def __get_report_from_bitcoinabuse(address: str) -> str:
    abuse = None
    res = get(f'https://www.bitcoinabuse.com/api/reports/check?address={address}&api_token={BITCOINABUSE_API_TOKEN}')
    if res.ok:
        if res.json()['count'] > 0:
            abuse_types = get('https://www.bitcoinabuse.com/api/abuse-types').json()
            abuse_types = {abuse_type['id']: abuse_type['label'] for abuse_type in abuse_types}
            abuse_reports = res.json()['recent']
            # count the number of reports for each abuse type and return the most common
            for report in abuse_reports:
                report['abuse_type_label'] = abuse_types[report['abuse_type_id']]
            abuse_reports = pd.DataFrame(abuse_reports)
            abuse_reports = abuse_reports.groupby('abuse_type_id').count().sort_values(by=['abuse_type_label','abuse_type_id'], ascending=[False,True])
            abuse_reports = abuse_reports.reset_index()
            abuse_reports = abuse_reports.iloc[0]
            abuse = abuse_types[abuse_reports['abuse_type_id']]
    
    if abuse is None:
        abuse = "No se ha encontrado actividad ilegal"
    
    return abuse

def get_common_info(address: str) -> dict:
    res = get(f'https://blockchain.info/rawaddr/{address}')
    if res.ok:
        json_response = res.json()
        # Total number of requests needed for getting all transactions
        total_req = ceil(json_response['n_tx'] / 100)
        # Number of requests to be executed (max 10 == 1000 txs)
        req_n = total_req if total_req < 10 else 10
        for i in range(1, req_n):
            res_ok = False
            proxy_list = []
            failed_count = 0
            while not res_ok and failed_count < 5:
                proxy = __get_different_proxy(proxy_list)
                proxy_list += proxy
                res = get(f'https://blockchain.info/rawaddr/{address}?offset={i * 100}', proxies={'http': proxy})
                if res.ok:
                    json_response['txs'] += res.json()['txs']
                    res_ok = True
                else:
                    failed_count += 1
                    
        return __blockchain_info_parser(json_response, address)
    else:
        return None

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

def transactions(info: dict) -> dict:
    if info is not None:
        txs = info['txs']
        transactions = []
        for tx in txs:
            inputs = []
            for inp in tx['inputs']:
                inputs.append({
                    'address': inp['prev_out']['addr'],
                    'value': inp['prev_out']['value'] / SATOSHI_DIVISOR,
                })
            outputs = []
            for out in tx['out']:
                outputs.append({
                    'address': out['addr'],
                    'value': out['value'] / SATOSHI_DIVISOR,
                })
            custom_tx = {
                'hash' : tx['hash'],
                'date' : datetime.fromtimestamp(tx['time']),
                'inputs': inputs,
                'outputs': outputs,
                'is_input': tx['result'] < 0,
                'value': tx['result'] / SATOSHI_DIVISOR,
            }
            transactions.append(custom_tx)       
    else:
        transactions = 'Error al obtener transacciones'
        
    return {
        'transactions': transactions,
    }


def illegal_activity(address: str) -> dict:
    illegal_activity = None
    label = __get_label_from_address(address)
    # Exclude addresses with label 'Exchange' or 'Pool'
    if label is not None:
        wallets = __get_wallets_from_walletexplorer()
        if wallets is not None:
            for key in wallets:
                if key in label:
                    if wallets[key]['type'] in ['exchanges', 'pools']:
                        illegal_activity = "No se ha encontrado actividad ilegal"
                        break
                    else:
                        illegal_activity = wallets[key]['type']
                        break
    if illegal_activity is None:
        illegal_activity =__get_report_from_bitcoinabuse(address)
    return {
        'illegal_activity': illegal_activity,
    }