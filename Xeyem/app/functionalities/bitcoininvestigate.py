from cProfile import label
from urllib import response
from weakref import proxy
from requests import get
from math import ceil
import pandas as pd
import ssl
from bs4 import BeautifulSoup
import re
import plotly.express as px
from fp.fp import FreeProxy
from googlesearch import search
from datetime import datetime
from io import StringIO
from ..models import Entity


BITCOINABUSE_API_TOKEN = 'xpq3nxlgXOcyafM6QaBCXCu3oKjArNT9Q2bZfzIX'
SATOSHI_DIVISOR = 100000000

def __get_first_and_last_tx(address: str, n_tx: int) -> tuple:
    url = f'https://www.walletexplorer.com/address/{address}'
    # To avoid certificate errors
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # We use pandas to get the LAST transaction
    df = pd.read_csv(url+'?format=csv', skiprows=[0])
    # And finally we return the first row from the date column
    last_tx = df['date'].iloc[0]
    
    # The first transaction is at the last row on the last page
    # the amount of txs for page is 100
    if n_tx > 100: # if there is only 1 page we already have it
        page_n = ceil(n_tx / 100)
        url += f'?page={page_n}'

        df = pd.read_csv(url+'&format=csv', skiprows=[0])

    first_tx = df['date'].iloc[-1]
        
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

def __get_address_list(info: dict) -> dict:
    if info is not None:
        txs = info['txs']
        addresses = {'inputs': [], 'outputs': []}
        for tx in txs:
            for inp in tx['inputs']:
                address_in = inp['prev_out']['addr']
                if address_in != info['address'] and address_in not in addresses['inputs']:
                    addresses['inputs'].append(address_in)
            for out in tx['out']:
                address_out = out['addr']
                if address_out != info['address'] and address_out not in addresses['outputs']:
                    addresses['outputs'].append(address_out)
    else:
        addresses = 'Error al obtener direcciones'
        
    return addresses

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
    proxy = FreeProxy(rand=True, elite=True).get()
    url = f'https://www.walletexplorer.com/address/{address}'
    res = get(url=url, proxies={'http': proxy})
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



# def get_labels(addresses: list) -> dict:
#     """Gets the label from walletexplorer.com for the given address"""
#     labels = {}
#     proxy_list = []
#     headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
#     for address in addresses:
#         url = f'https://www.walletexplorer.com/address/{address}'
#         div = label = None
#         steps = 0
#         while div is None or steps > 5:
#             steps += 1 # Avoid infinite loop
#             proxy = __get_different_proxy(proxy_list)
#             proxy_list.append(proxy)
#             response = get(url, headers=headers, proxies={'http': proxy})
#             if response.ok:
#                 soup = BeautifulSoup(response.text, 'html.parser')
#                 div = soup.find('div', {'class': 'walletnote'})
#                 if div is not None:
#                     label = div.find('a')['href'].split('/')[-1]
#                     labels[address] = label
#                 elif steps > 5:
#                     labels[address] = None                  
#     return labels

def __get_address_label(address: str) -> str:
    label = Entity.objects.filter(address=address)
    if label.exists():
        label = label.first().address_tag
    else:
        label = 'Other'
    return label

def get_common_info(address: str) -> dict:
    res = get(f'https://blockchain.info/rawaddr/{address}')
    if res.ok:
        json_response = res.json()
        # Total number of requests needed for getting all transactions
        total_req = ceil(json_response['n_tx'] / 100)
        # Number of requests to be executed (max 5 == 500 txs)
        req_n = total_req if total_req < 5 else 5
        for i in range(1, req_n):
            res_ok = False
            proxy_list = []
            failed_count = 0
            while not res_ok and failed_count < 5:
                proxy = __get_different_proxy(proxy_list)
                proxy_list += proxy
                res = get(f'https://blockchain.info/rawaddr/{address}?offset={i*100}', proxies={'http': proxy})
                if res.ok:
                    json_response['txs'] += res.json()['txs']
                    res_ok = True
                else:
                    failed_count += 1
        json_response['txs'].sort(key=lambda tx: tx['time'], reverse=True)
        return json_response
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
    plt_div = None
    
    res = get(url=url, headers=headers)
    if res.ok:
        soup = BeautifulSoup(res.text, 'html.parser')
        scripts = soup.find_all('script')
        search_text = 'd = new Dygraph(document.getElementById("gcontainer")'
        for script in scripts:
            if script.string is not None and search_text in script.string:
                StrList = script.string
                StrList = '[[' + StrList.split('[[')[-1]
                StrList = StrList.split(']]')[0] +']]'
                StrList = StrList.replace("new Date(", '').replace(')','')
                StrList = StrList[1:-1]
                dataList = __parse_strlist(StrList)
                df = pd.DataFrame(dataList, columns=['Date','Balance (BTC)', 'USD', 'Other'])
                df['Date'] = pd.to_datetime(df['Date'], unit='ms')
                df['Balance (BTC)'] = pd.to_numeric(df['Balance (BTC)'], errors='coerce')
                df.drop(['USD','Other'], axis=1, inplace=True)
                fig = px.area(data_frame=df, x='Date', y='Balance (BTC)')
                plt_div = fig.to_html(include_plotlyjs=False, full_html=False, div_id="plt_div")

    if plt_div is None:
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
                'date' : datetime.fromtimestamp(tx['time']).strftime("%Y-%m-%d %H:%M:%S"),
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

def transactions_stats(info: dict) -> dict:
    if info is not None:
        addresses = __get_address_list(info)
        all_addresses = list(set(addresses['inputs'] + addresses['outputs']))
        proxy_list = []
        addresses_dict = {}
        # label each address using walletexplorer and bitcoinabuse
        for address in all_addresses:
            label = __get_address_label(address)
            addresses_dict[address] = label
        # get how many times a label appears in the inputs
        labels = {
            'inputs': {},
            'outputs': {},
        }
        for address in addresses['inputs']:
            label = addresses_dict[address]
            if label in labels['inputs']:
                labels['inputs'][label] += 1
            else:
                labels['inputs'][label] = 1
        # get how many times a label appears in the outputs
        for address in addresses['outputs']:
            label = addresses_dict[address]
            if label in labels['outputs']:
                labels['outputs'][label] += 1
            else:
                labels['outputs'][label] = 1
        # get the label stats for the inputs
        inputs = []
        for label in labels['inputs']:
            inputs.append({
                'label': label,
                'count': labels['inputs'][label],
            })
        # get the label stats for the outputs
        outputs = []
        for label in labels['outputs']:
            outputs.append({
                'label': label,
                'count': labels['outputs'][label],
            })
        # plot the input stats on a pie chart using plotly
        fig = px.pie(data_frame=pd.DataFrame(inputs), names='label', values='count')
        fig = fig.update_traces(textposition='inside', textinfo='percent+label')
        inputs_div = fig.to_html(include_plotlyjs=False, full_html=False, div_id="inputs_div")
        # plot the output stats on a pie chart using plotly
        fig2 = px.pie(data_frame=pd.DataFrame(outputs), names='label', values='count')
        fig2=fig2.update_traces(textposition='inside', textinfo='percent+label')
        outputs_div = fig2.to_html(include_plotlyjs=False, full_html=False, div_id="outputs_div")
    else:
        inputs_div = outputs_div = "Error al obtener estadísticas de transacciones"

    return {
        'inputs_stats': inputs_div,
        'outputs_stats': outputs_div,
    }
        
            
def related_addresses(address: str) -> dict: 
    label = __get_label_from_address(address)
    ssl._create_default_https_context = ssl._create_unverified_context
    url = f'https://walletexplorer.com/wallet/{label}/addresses?format=csv'
    proxy = FreeProxy(rand=True, elite=True).get()
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
    res = get(url=url, headers=headers, proxies={'http': proxy})
    if res.ok:
        df = pd.read_csv(StringIO(res.text), skiprows=[0])
        addresses = df['address'].to_list()
        related = {
            'addresses': addresses,
        }
        if len(addresses) == 100:
                related['url'] = f'https://walletexplorer.com/wallet/{label}/addresses',
    else:
        related = {
            'addresses': 'Error al obtener direcciones relacionadas.'
            }
    
    return related

    


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

def web_appearances(address: str) -> dict:
    """Returns a list of urls where the address has been found"""
    query = f'"{address}" -site:blockexplorer.one -site:blockcypher.herokuapp.com -site:coin-cap.pro -site:btc.exan.tech -site:blockchain.info -site:btctocad.com -site:esplora.blockstream.com -site:bitcoinblockexplorers.com -site:bitinfocharts.com -site:bitcoinabuse.com -site:walletexplorer.com -site:blockchair.com -site:blockchain.com -site:blockcypher.com -site:blockstream.info -site:tokenscope.com'
    urls = list(search(query, tld="com", num=10, stop=10))
    appearances = urls if urls else "No se han encontrado resultados"
    return {
        'web_appearances': appearances,
    }