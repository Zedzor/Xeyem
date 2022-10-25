from app.models import Address, Entity
import csv

def save_Mining():
    with open('data/Mining_parsed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header
        #list of mining
        tag = 'Mining'
        name_list = []
        mining = []

        for row in reader:
            name = row[0]

            if name not in name_list:
                name_list.append(name)

        for name in name_list:
            mine = Entity(entity_name=name, entity_tag=tag)
            mining.append(mine)

        Entity.objects.bulk_create(mining)
        mining = []

def save_Addresses():
    with open('data/Mining_parsed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header
        #list of mining
        addresses = {}
        address_objects = []

        for row in reader:
            name = row[0]
            address = row[1]

            if name not in addresses.keys():
                addresses[name] = [address]
            else:
                addresses[name].append(address)
                
        print("Creating address objects...")
        for name, address_list in addresses.items():
            entity = Entity.objects.get(entity_name=name)
            for addr in address_list:
                new_address = Address(entity_id=entity, address=addr)
                address_objects.append(new_address)

        print("Saving address objects...")
        Address.objects.bulk_create(address_objects)
        addresses = {}
        address_objects = []

def run():
    # Entity.objects.all().delete()
    print('Saving Mining entities...')
    save_Mining()
    print('Saving Mining addresses...')
    save_Addresses()

if __name__ == '__main__':
    run()
    