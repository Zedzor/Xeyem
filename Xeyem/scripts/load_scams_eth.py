from app.models import Address, Entity
import json

def save_Scams():
    with open('data/scams_ETH.json') as file:
        data = json.load(file)
        addresses = data['scams']
        tag = 'Scam'
        addresses_objects = []
        for address in addresses:
            new_entity = Entity.objects.create(entity_name='', entity_tag=tag)
            new_address = Address(entity_id=new_entity, address=address.lower())
            addresses_objects.append(new_address)
        Address.objects.bulk_create(addresses_objects)
        addresses_objects = []

def run():
    print('Saving Scams entities and addresses...')
    save_Scams()