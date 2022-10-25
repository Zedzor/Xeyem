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

def save_Exchanges():
    with open('data/Exchanges_parsed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header
        #list of exchanges
        tag = 'Exchange'
        name_list = []
        exchanges = []

        for row in reader:
            name = row[0]

            if name not in name_list:
                name_list.append(name)

        for name in name_list:
            exchange = Entity(entity_name=name, entity_tag=tag)
            exchanges.append(exchange)

        Entity.objects.bulk_create(exchanges)
        exchanges = []


def save_Addresses():
    with open('data/Exchanges_parsed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header
        # list of addresses
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
    print('Saving Exchanges entities...')
    save_Exchanges()
    print('Saving Exchanges addresses...')
    save_Addresses()

if __name__ == '__main__':
    run()
    