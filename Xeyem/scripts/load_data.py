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
    with open('app/EntitiesAddressesBTC/data/Exchanges_full_detailed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header

        for row in reader:
            address = row[5]
            name = row[4]
            tag = 'Exchange'
            # country = row[2]

            # Check if entity already exists
            if not Entity.objects.filter(entity_name=name).exists():
                entity = Entity(entity_name=name, entity_tag=tag)
                entity.save()
            entity = Entity.objects.get(entity_name=name)
            address = Address(entity_id=entity, address=address)
            address.save()

def save_Mining():
    with open('app/EntitiesAddressesBTC/data/Mining_full_detailed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header

        for row in reader:
            address = row[4]
            name = row[2]
            tag = 'Mining'

            if not Entity.objects.filter(entity_name=name).exists():
                entity = Entity(entity_name=name, entity_tag=tag)
                entity.save()
            entity = Entity.objects.get(entity_name=name)
            address = Address(entity_id=entity, address=address)
            address.save()

def save_Gambling():
    with open('app/EntitiesAddressesBTC/data/Gambling_full_detailed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header

        for row in reader:
            address = row[4]
            name = row[2]
            tag = 'Gambling'

            if not Entity.objects.filter(entity_name=name).exists():
                entity = Entity(entity_name=name, entity_tag=tag)
                entity.save()
            entity = Entity.objects.get(entity_name=name)
            address = Address(entity_id=entity, address=address)
            address.save()

def identify_service(name: str) -> str:
    for key, value in INFO.items():
        if key in name:
            return value

    for key,value in MATCHES.items():
        if any(match in name.lower() for match in value):
            return key
    return 'Unnamed service'

def save_Services():
    with open('app/EntitiesAddressesBTC/data/Services_full_detailed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header

        for row in reader:
            address = row[4]
            name = row[2]
            tag = identify_service(name)

            if not Entity.objects.filter(entity_name=name).exists():
                entity = Entity(entity_name=name, entity_tag=tag)
                entity.save()
            entity = Entity.objects.get(entity_name=name)
            address = Address(entity_id=entity, address=address)
            address.save()

def save_Historic():
    with open('app/EntitiesAddressesBTC/data/Historic_full_detailed.csv') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header

        for row in reader:
            address = row[4]
            name = row[2]
            tag = identify_service(name)

            if not Entity.objects.filter(entity_name=name).exists():
                entity = Entity(entity_name=name, entity_tag=tag)
                entity.save()
            entity = Entity.objects.get(entity_name=name)
            address = Address(entity_id=entity, address=address)
            address.save()

def run():
    # Entity.objects.all().delete()
    print('Saving Exchanges...')
    save_Exchanges()
    print('Saving Mining...')
    save_Mining()
    print('Saving Gambling...')
    save_Gambling()
    print('Saving Services...')
    save_Services()
    print('Saving Historic...')
    save_Historic()

if __name__ == '__main__':
    pass
    