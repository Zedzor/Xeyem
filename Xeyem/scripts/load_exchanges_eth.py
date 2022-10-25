from app.models import Address, Entity
import json

def save_Exchanges():
    with open('data/Exchanges_ETH.json') as file:
        data = json.load(file)
        exchanges = data['exchanges']
        tag = 'Exchange'
        exchanges_objects = []
        for exchange in exchanges:
            name = exchange['name']
            if not Entity.objects.filter(entity_name=name).exists():
                new_exchange = Entity(entity_name=name, entity_tag=tag)
                exchanges_objects.append(new_exchange)
        Entity.objects.bulk_create(exchanges_objects)
        exchanges_objects = []

def save_Addresses():
    with open('data/Exchanges_ETH.json') as file:
        data = json.load(file)
        exchanges = data['exchanges']
        address_objects = []
        for exchange in exchanges:
            name = exchange['name']
            addresses = exchange['addresses']
            entity = Entity.objects.get(entity_name=name)
            for addr in addresses:
                new_address = Address(entity_id=entity, address=addr.lower())
                address_objects.append(new_address)
        Address.objects.bulk_create(address_objects)
        address_objects = []

def run():
    print('Saving Exchanges entities...')
    save_Exchanges()
    print('Saving Exchanges addresses...')
    save_Addresses()