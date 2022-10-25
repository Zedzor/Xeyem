from app.models import Address, Entity
import csv

MATCHES = {
    'Darknet market': ['market'],
    'Mixing': ['mix', 'laund', 'fog'],
}

INFO = {
'CoinPayments.net': 'Merchant service',
'Xapo.com': 'Banking',
'Cubits.com': 'Exchange',
'Cryptonator.com': 'High risk exchange', 
'BitPay.com': 'Exchange',
'BitoEX.com': 'Exchange',
'HaoBTC.com': 'Exchange',
'Cryptopay.me': 'Exchange',
'AlphaBayMarket': 'Darknet market',
'NucleusMarket': 'Darknet market',
'BitcoinFog': 'Mixing',
'BitcoinWallet.com': 'Unnamed service',
'CoinJar.com': 'Exchange',
'HolyTransaction.com': 'Exchange',
'HelixMixer': 'Mixing',
'BTCJam.com': 'P2P Exchange',
'VIP72.com': 'Other',
'MoonBit.co.in': 'Other',
'CoinKite.com': 'Unnamed service',
'FaucetBOX.com': 'Other',
'OkLink.com': 'Other',
'Purse.io': 'Merchant service',
'ePay.info': 'Other',
'Loanbase.com': 'Merchant service',
'CrimeNetwork.co': 'Darknet market',
'GermanPlazaMarket': 'Darknet market',
'Bitbond.com': 'Merchant service',
'Paymium.com': 'Merchant service',
'StrongCoin.com-fee': 'Exchange',
'CryptoStocks.com': 'Merchant service',
'CoinApult.com': 'Exchange',
'Genesis-Mining.com': 'Mining',
'ChangeTip.com': 'Other',
'DoctorDMarket': 'Darknet market',
'GoCelery.com': 'Exchange',
'BTCPop.co': 'P2P Exchange',
'BTCLend.org': 'Other',
'CoinURL.com': 'Other',
'BitNZ.com': 'Exchange',
'CoinBox.me': 'Other',
'CoinWorker.com': 'Merchant service',
'WatchMyBit.com': 'Other',
'BitLaunder.com': 'Mixing',
'BitClix.com': 'Other',
'Vic-Socks.to': 'Other',
'SecureVPN.to': 'Other',
'Bylls.com': 'Merchant service',
'GreenRoadMarket': 'Darknet market',
}

def identify_service(name: str) -> str:
    for key, value in INFO.items():
        if key in name:
            return value

    for key,value in MATCHES.items():
        if any(match in name.lower() for match in value):
            return key
    return 'Unnamed service'

def save_Services():
    with open('data/Services_parsed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header
        #list of services
        name_list = []
        services = []

        for row in reader:
            name = row[0]
        
            if name not in name_list:
                name_list.append(name)

        for name in name_list:
            tag = identify_service(name)
            serv = Entity(entity_name=name, entity_tag=tag)
            services.append(serv)
        
        Entity.objects.bulk_create(services)
        services = []

def save_Addresses():
    with open('data/Services_parsed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header
        #list of gambling
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
                address_object = Address(entity_id=entity, address=addr)
                address_objects.append(address_object)
        print("Saving address objects...")
        Address.objects.bulk_create(address_objects)
        addresses = {}
        address_objects = []

def run():
    # Entity.objects.all().delete()
    print('Saving Services entities...')
    save_Services()
    print('Saving Services addresses...')
    save_Addresses()

if __name__ == '__main__':
    run()