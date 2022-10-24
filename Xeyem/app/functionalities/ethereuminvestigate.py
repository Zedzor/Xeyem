from ..models import Address, WebAppearance, SuggestedTag, Entity
from etherscan import Etherscan
from datetime import datetime
import plotly.express as px
import pandas as pd
import json
from googlesearch import search
from requests import get
from bs4 import BeautifulSoup


ETHERSCAN_API_KEY = 'QDQ1QUX52G7T1RUVZ6X987V6BNTHSFG8SR'
WEI_DIVISOR = 1000000000000000000

def __get_stored_info(addr: str) -> dict:
    """Get stored information about an Ethereum address"""
    address = Address.objects.filter(address=addr).first()
    if address is not None:
        entity = address.entity_id
        web_appearances = WebAppearance.objects.filter(address=addr)
        suggested_tags  = SuggestedTag.objects.filter(wallet_id=entity)
        last_search = json.loads(address.last_search) if address.last_search is not None else None
        info = {
            'address': addr,
            'entity': entity.entity_tag if entity is not None else None,
            'web_appearances': [ web_appearance.web_address for web_appearance in web_appearances ] if web_appearances.exists() else None,
            'suggested_tags': [{
                'suggested_tag': suggested_tag.tag,
                'suggested_by': suggested_tag.informant.email if suggested_tag.informant else None,
                } for suggested_tag in suggested_tags ] if suggested_tags.exists() else None,
            'informed_by': address.informant.email if address.informant else None,
        }
        if last_search is not None:
            info['balance'] = last_search['balance']
            info['n_tx'] = last_search['n_tx']
            info['transactions'] = last_search['transactions']
            info['first_transaction'] = last_search['first_transaction']
            info['last_transaction'] = last_search['last_transaction']   
            info['most_transfered'] = last_search['most_transfered']
            info['txs'] = last_search['txs']

    else:
        info = {}

    return info

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

def __get_total_value(tx: dict) -> float:
    """Get total value of a transaction"""
    value = int(tx['value'])
    gas_price = int(tx['gasPrice'])
    gas_used = int(tx['gasUsed'])
    tx_fee = gas_price * gas_used
    total_value = (value + tx_fee) / WEI_DIVISOR
    return total_value

def get_common_info(addr: str) -> dict:
    """Get common information about an Ethereum address"""
    search_addr = addr.lower()
    stored_info = __get_stored_info(search_addr)
    stored_info['new_info'] = False
    try:
        print('Getting info from Etherscan...')
        eth = Etherscan(ETHERSCAN_API_KEY)
        txs = eth.get_normal_txs_by_address(address=addr, startblock=0, endblock=99999999, sort='desc')  
        if 'n_tx' not in stored_info or len(txs) > stored_info['n_tx']:
            stored_info['transactions'] = txs
            stored_info['txs'] = txs
            stored_info['n_tx'] = len(txs)
            stored_info['first_transaction'] = txs[0]['timeStamp']
            stored_info['last_transaction'] = txs[-1]['timeStamp']
            stored_info['balance'] = eth.get_eth_balance(address=addr)
            stored_info['new_info'] = True
            stored_info['address'] = addr
    except:
        pass

    if 'n_tx' not in stored_info:
        stored_info = None

    return stored_info

def balance(info: dict) -> tuple:
    """Get balance of an Ethereum address"""
    print('Getting balance...')
    balance = int(info['balance']) / WEI_DIVISOR
    return info, {
        'balance': balance,
        'coin': 'ETH',
    }

def fst_lst_transaction(info: dict) -> tuple:
    """Get first and last transaction of an Ethereum address"""
    print('Getting first and last transaction...')
    first_transaction = datetime.fromtimestamp(int(info['first_transaction'])).strftime("%Y-%m-%d")
    last_transaction = datetime.fromtimestamp(int(info['last_transaction'])).strftime("%Y-%m-%d")
    return info, {
        'first_transaction': first_transaction,
        'last_transaction': last_transaction
    }

def balance_time(shared_info: dict) -> tuple:
    """Get balance of an Ethereum address over time.
    From current balance substract or add the value of each 
    transaction until the first transaction."""
    print('Getting balance over time...')
    txs = shared_info['txs']
    balance = int(shared_info['balance']) / WEI_DIVISOR
    balance_time = []
    last_date = int(datetime.now().timestamp())
    balance_time.append({
        'Date': last_date,
        'Balance (ETH)': balance,
    })
    for tx in txs:
        current_date = int(tx['timeStamp'])
        # insert a point in the graph for each week
        week_value = 604800
        last_date -= week_value
        while last_date > current_date:
            balance_time.append({
                'Date': last_date,
                'Balance (ETH)': balance,
            })
            last_date -= 86400
        last_date = current_date
        total_value = __get_total_value(tx)
        from_addr = tx['from'].lower()
        if from_addr == shared_info['address']:
            balance += total_value
        else:
            balance -= int(tx['value']) / WEI_DIVISOR
        balance_time.append({
            'Date': int(tx['timeStamp']),
            'Balance (ETH)': balance
        })

    df = pd.DataFrame(balance_time, columns=['Date', 'Balance (ETH)'])
    df['Date'] = pd.to_datetime(df['Date'], unit='s')
    df['Balance (ETH)'] = pd.to_numeric(df['Balance (ETH)'], errors='coerce')
    fig = px.area(data_frame=df, x='Date', y='Balance (ETH)')
    plt_div = fig.to_html(include_plotlyjs=False, full_html=False, div_id="plt_div")
    
    return shared_info, {'balance_time': plt_div}

def transactions(info: dict) -> tuple:
    """Get transactions of an Ethereum address"""
    print('Getting transactions...')
    if info is None:
        most_transfered = transactions = 'Error al obtener transacciones'
    elif not info['new_info']:
        transactions = info['transactions']
        most_transfered = info['most_transfered']
    else:
        txs = info['txs']
        transactions = []
        most_transfered = { 'in':{}, 'out':{} }
        for tx in txs:
            is_input = tx['from'].lower() != info['address']
            if is_input:
                value = int(tx['value']) / WEI_DIVISOR
                address = tx['from'].lower()
                if address in most_transfered['in']:
                    most_transfered['in'][address]['value'] += value
                else:
                    most_transfered['in'][address] = {
                        'value': value,
                        'tag': __get_tag_and_name(address)[0],
                    }
            else:
                total_value = __get_total_value(tx)
                address = tx['to'].lower()
                if address in most_transfered['out']:
                    most_transfered['out'][address]['value'] += total_value
                else:
                    most_transfered['out'][address] = {
                        'value': total_value,
                        'tag': __get_tag_and_name(address)[0],
                    }
                value = -1 * total_value
            transactions.append({
                'hash': tx['hash'],
                'date': datetime.fromtimestamp(int(tx['timeStamp'])).strftime("%Y-%m-%d %H:%M:%S"),
                'value': value,
                'other_address': address,
                'is_input': is_input,
                'tag': __get_tag_and_name(address)[0],
            })
        most_transfered['in'] = sorted(most_transfered['in'].items(), key=lambda x: x[1]['value'], reverse=True)[:5]
        most_transfered['out'] = sorted(most_transfered['out'].items(), key=lambda x: x[1]['value'], reverse=True)[:5]
        info['transactions'] = transactions
        info['most_transfered'] = most_transfered

    return info, {
        'transactions': transactions,
        'most_transfered': most_transfered
    }

def transactions_stats(info: dict) -> tuple:
    """Get statistics about tagged addresses from the transactions of an Ethereum address"""
    print('Getting transactions stats...')
    if info is None:
        inputs_div = outputs_div = exchanges = 'Error al obtener estadísticas de transacciones'
    else:
        labels = {
            'inputs': {},
            'outputs': {}
        }
        exc = {}
        exchanges = []
        for tx in info['transactions']:
            tag = tx['tag']
            if tag == 'Exchange' and not tx['is_input']:
                name = __get_tag_and_name(tx['other_address'])[1]
                if name in exc:
                    exc[name] += tx['value']
                else:
                    exc[name] = tx['value']
            if tx['is_input']:
                if tx['tag'] in labels['inputs']:
                    labels['inputs'][tx['tag']] += 1
                else:
                    labels['inputs'][tx['tag']] = 1
            else:
                if tx['tag'] in labels['outputs']:
                    labels['outputs'][tx['tag']] += 1
                else:
                    labels['outputs'][tx['tag']] = 1
        for key, value in exc.items():
            exchanges.append({
                'name': key,
                'ammount': -1*value
            })
        exchanges = sorted(exchanges, key=lambda x: x['ammount'], reverse=True)[:4]

        inputs = []
        outputs = []
        for label, count in labels['inputs'].items():
            inputs.append({
                'label': label,
                'count': count
            })
        for label, value in labels['outputs'].items():
            outputs.append({
                'label': label,
                'count': count
            })
        if inputs != []:
            fig = px.pie(data_frame=pd.DataFrame(inputs), names='label', values='count')
            fig = fig.update_traces(textposition='inside', textinfo='percent+label')
            inputs_div = fig.to_html(include_plotlyjs=False, full_html=False, div_id="inputs_div")
        else:
            inputs_div = 'No hay transacciones de entrada'
        if outputs != []:
            fig2 = px.pie(data_frame=pd.DataFrame(outputs), names='label', values='count')
            fig2=fig2.update_traces(textposition='inside', textinfo='percent+label')
            outputs_div = fig2.to_html(include_plotlyjs=False, full_html=False, div_id="outputs_div")
        else:
            outputs_div = 'No hay transacciones de salida'
    
    return info, {
        'inputs_stats': inputs_div,
        'outputs_stats': outputs_div,
        'exchanges': exchanges
    }

def related_addresses(info: dict) -> tuple:
    """Get related addresses from the transactions of an Ethereum address"""
    print('Getting related addresses...')
    if info is None:
        related_addresses = 'Error al obtener direcciones relacionadas'
    else:
        address = Address.objects.filter(address=info['address']).first()
        if address is not None:
            related_addr = Address.objects.filter(entity_id=address.entity_id).exclude(address=info['address'])
            related_addresses = [{
                'address': addr.address,
                'pk': addr.pk,
                'informant': addr.informant if addr.informant is not None else None,
            } for addr in related_addr]
            related = {
                'addresses': related_addresses,
            }
        else:
            related = {
                'addresses': [],
            }
    print(related)
    return info, related

def illegal_activity(info: dict) -> tuple:
    """Get illegal activity from the transactions of an Ethereum address"""
    print('Getting illegal activity...')
    if info is None:
        illegal_activity = 'Error al obtener actividad ilegal'
    else:
        address = Address.objects.filter(address=info['address']).first()
        if address is not None and address.entity_id.entity_tag != 'Other':
            illegal_activity = address.entity_id.entity_tag
            illegal_activity = illegal_activity if illegal_activity != 'Other' else 'Unknown'
        else:
            res = get(f'https://www.cryptoblacklist.io/en/ethereum/{info["address"]}/')
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table')
            if table is not None:
                illegal_activity = table.tbody.tr.td.find_next().text
            else:   
                illegal_activity = 'Unknown'
    info['illegal_activity'] = {
            'is_illegal': illegal_activity not in ['Unknown', 'Other', 'Exchange'],
            'tag': illegal_activity,
    }
    return info, {
        'illegal_activity': info['illegal_activity']
    }

def web_appearances(info: dict) -> tuple:
    """Get web appearances from the transactions of an Ethereum address"""
    print('Getting web appearances...')
    if info is None:
        web_appearances = 'Error al obtener apariciones en la web'
    else:
        address = info['address']
        query = f"{address}"
        urls = list(search(query, tld="com", num=10, stop=10))
        address = Address.objects.filter(address=info['address']).first()
        if address is not None:
            web_appearances_objects = WebAppearance.objects.filter(address=address)
            web_appearances = [{
                'web_address': web.web_address,
                'informant': web.informant,
                'address': web.address
            } for web in web_appearances_objects]
            for url in urls:
                if url not in [web['web_address'] for web in web_appearances]:
                    web_appearances.append({
                        'web_address': url,
                        'informant': None,
                        'address': address
                    })
        else:
            web_appearances = [{
                'web_address': url,
            } for url in urls]
            
    return info, {
        'web_appearances': web_appearances
    }
    

def store_results(info: dict, results: dict) -> bool:
    """Store the results of the analysis in the database"""
    if info is None:
        return False
    addr = info['address'].lower()
    last_search = json.dumps(info)
    illegal = info['illegal_activity']['tag']
    addr_tag = illegal if illegal != 'Unknown' else 'Other'
    address = Address.objects.filter(address=addr).first()
    if address is None:
        entity = Entity.objects.create(entity_tag=addr_tag)
        address = Address.objects.create(address=addr, entity_id=entity, last_search=last_search)
    elif info['new_info']:
        address.last_search = last_search
        address.save()
    if 'web_appearances' in results:
        for appearance in results['web_appearances']:
            WebAppearance.objects.get_or_create(address=address, web_address=appearance['web_address'])
    
    return True
