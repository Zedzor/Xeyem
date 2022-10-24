from cProfile import label
from urllib import response
from weakref import proxy
from requests import get
from math import ceil
import pandas as pd
import ssl
from bs4 import BeautifulSoup
import re
import json
import plotly.express as px
from fp.fp import FreeProxy
from googlesearch import search
from datetime import datetime
from io import StringIO
from ..models import Entity, Address, WebAppearance, SuggestedTag, Note


BITCOINABUSE_API_TOKEN = 'xpq3nxlgXOcyafM6QaBCXCu3oKjArNT9Q2bZfzIX'
SATOSHI_DIVISOR = 100000000

def __get_first_last_tx(address: str, n_tx: int, get_first: bool) -> tuple:
    url = f'https://www.walletexplorer.com/address/{address}'
    # To avoid certificate errors
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # We use pandas to get the LAST transaction
    df = pd.read_csv(url+'?format=csv', skiprows=[0])
    # And finally we return the first row from the date column
    last_tx = df['date'].iloc[0]
    
    if get_first:
        # The first transaction is at the last row on the last page
        # the amount of txs for page is 100
        if n_tx > 100: # if there is only 1 page we already have it
            page_n = ceil(n_tx / 100)
            url += f'?page={page_n}'

            df = pd.read_csv(url+'&format=csv', skiprows=[0])

        first_tx = df['date'].iloc[-1]
    else:
        first_tx = None
        
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
        print(res.content)
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
    proxy = FreeProxy(rand=True).get()
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

def __get_tag_and_name(addr: str) -> tuple:
    address = Address.objects.filter(address=addr).first()
    if address is not None:
        entity = address.entity_id
        tag = entity.entity_tag
        name = entity.entity_name if entity.entity_name is not None else ''
    else:
        tag = 'Other'
        name = ''
    return tag,name


def __get_stored_info(addr: str) -> dict:
    """Function to get the stored info for an address"""
    address = Address.objects.filter(address=addr)
    if address.exists():
        entity = Entity.objects.filter(address=addr)
        web_appearances = WebAppearance.objects.filter(address=addr)
        suggested_tags  = SuggestedTag.objects.filter(address=addr)
        notes = Note.objects.filter(address=addr)
        last_search = json.loads(address.first().last_search) if last_search is not None else None
        info = {
            'address': addr,
            'entity': entity.first().address_tag if entity.exists() else None,
            'web_appearances': [ web_appearance.web_address for web_appearance in web_appearances ] if web_appearances.exists() else None,
            'suggested_tags': [{
                'suggested_tag': suggested_tag.tag,
                'suggested_by': suggested_tag.informant.email if suggested_tag.informant else None,
                } for suggested_tag in suggested_tags ] if suggested_tags.exists() else None,
            'notes': [{
                'note': note.note,
                'created_by': note.informant.email if note.informant else None,
                } for note in notes ] if notes.exists() else None,
            'informed_by': address.first().informant.email if address.first().informant else None,
        }
        if last_search is not None:
            info['balance'] = last_search['balance']
            info['n_tx'] = last_search['n_tx']
            info['total_received'] = last_search['total_received']
            info['total_sent'] = last_search['total_sent']
            info['txs'] = last_search['txs']
            info['transactions'] = last_search['transactions']
            info['first_transaction'] = last_search['first_transaction']
            info['last_transaction'] = last_search['last_transaction']                        

    else:
        info = None

    return info

def __get_txs(address: str, json_response: dict) -> dict:
    """Function to get the transactions of an address"""
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
    return json_response

def get_common_info(address: str) -> dict:
    stored_info = __get_stored_info(address)
    res = get(f'https://blockchain.info/rawaddr/{address}')
    if res.ok:
        json_response = res.json()
        #check if the total number of transactions is different from the stored one
        if stored_info:
            if len(stored_info['transactions']) != json_response['n_tx']:
                json_response = __get_txs(address, json_response)
                # Update list of transactions adding the new ones and removing duplicates
                stored_info['transactions'] = list(set(stored_info['transactions'] + json_response['txs']))
                # sort the list of transactions by time
                stored_info['transactions'].sort(key=lambda tx: tx['time'], reverse=True)
                stored_info['balance'] = json_response['final_balance']
                stored_info['n_tx'] = json_response['n_tx']
                stored_info['new_info'] = True
            else:
                stored_info['new_info'] = False

        else:
            stored_info = __get_txs(address, json_response)
            stored_info['new_info'] = True
            stored_info['balance'] = stored_info.pop('final_balance')

    return stored_info

def balance(info: dict) -> tuple:  
    final_balance = info['balance'] / SATOSHI_DIVISOR if info is not None else 'Error al obtener balance'
    return info,{
        'balance': final_balance,
    }
    
def fst_lst_transaction(info: dict) -> tuple:
    if info is not None:
        if not info['new_info']:
            first_transaction = info['first_transaction']
            last_transaction = info['last_transaction']
        elif 'first_transaction' in info:
            first_transaction = info['first_transaction']
            info['last_transaction'] = last_transaction = __get_first_last_tx(info['address'], info['n_tx'], False)[1]
        else:
            first_transaction,last_transaction = __get_first_last_tx(info['address'], info['n_tx'], True)
            info['first_transaction'] = first_transaction
            info['last_transaction'] = last_transaction
    else:
        first_transaction = last_transaction = "Error al obtener fecha"
        
    return info,{
        'first_transaction': first_transaction,
        'last_transaction': last_transaction,
    }
    
def balance_time(info: dict) -> tuple:
    address = info['address']
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
    
    return info,{'balance_time': plt_div}

def transactions(info: dict) -> tuple:
    if info is not None:
        if info['new_info']:
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
            info['transactions'] = transactions   
        else:
            transactions = info['transactions']
    else:
        transactions = 'Error al obtener transacciones'

    return info,{'transactions': transactions,}

def transactions_stats(info: dict) -> tuple:
    if info is not None:
        addresses = __get_address_list(info)
        all_addresses = list(set(addresses['inputs'] + addresses['outputs']))
        addresses_dict = {}
        for address in all_addresses:
            addresses_dict[address] = __get_tag_and_name(address)
        # get how many times a label appears in the inputs
        labels = {
            'inputs': {},
            'outputs': {},
        }
        exchanges = []

        for address in addresses['inputs']:
            label = addresses_dict[address][0]
            if label in labels['inputs']:
                labels['inputs'][label] += 1
            else:
                labels['inputs'][label] = 1
        # get how many times a label appears in the outputs
        for address in addresses['outputs']:
            label = addresses_dict[address][0]
            if label == 'Exchange':
                exchanges.append(addresses_dict[address][1])
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
        exchanges = list(set(exchanges))
    else:
        inputs_div = outputs_div = "Error al obtener estadísticas de transacciones"

    return info,{
        'inputs_stats': inputs_div,
        'outputs_stats': outputs_div,
        'exchanges': exchanges,
    }
        
            
def related_addresses(info: dict) -> tuple: 
    address = Address.objects.filter(address=info['address'])
    if address.exists():
        related = [ addr.address for addr in address ]
    else:    
        address = info['address'] 
        label = __get_label_from_address(address)
        ssl._create_default_https_context = ssl._create_unverified_context
        url = f'https://walletexplorer.com/wallet/{label}/addresses?format=csv'
        proxy = FreeProxy(rand=True).get()
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
    
    return info,related

def illegal_activity(info: dict) -> tuple:
    address = Address.objects.filter(address=info['address']).first()
    if address is not None:
        illegal_activity = address.entity_id.entity_tag
    else:
        illegal_activity = None
        address = info['address']
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
    return info,{
        'illegal_activity': illegal_activity,
    }

def web_appearances(info: dict) -> tuple:
    """Returns a list of urls where the address has been found"""
    address = Address.objects.filter(address=info['address']).first()
    if address is not None:
        web_appearances = WebAppearance.objects.filter(address=address)
        if web_appearances.exists():
            web_appearances = [ web.web_address for web in web_appearances ]
    else:
        web_appearances = []

    address = info['address']
    query = f'"{address}" -site:blockexplorer.one -site:blockcypher.herokuapp.com -site:coin-cap.pro -site:btc.exan.tech -site:blockchain.info -site:btctocad.com -site:esplora.blockstream.com -site:bitcoinblockexplorers.com -site:bitinfocharts.com -site:bitcoinabuse.com -site:walletexplorer.com -site:blockchair.com -site:blockchain.com -site:blockcypher.com -site:blockstream.info -site:tokenscope.com'
    urls = list(search(query, tld="com", num=10, stop=10))
    appearances = list(set(urls+web_appearances))
    return info,{
        'web_appearances': appearances if appearances else "No se han encontrado resultados",
    }