from flask import Flask, render_template, request
from gevent.pywsgi import WSGIServer
import requests, json


    
def getRmmV3Balance(walletAddressList):
    dataRequest = {"operationName":"RmmQuery","variables":{"addressList":[]},"query":"query RmmQuery($addressList: [String]!) {\n  users(where: {id_in: $addressList}) {\n    id\n    balances {\n      token {\n        name\n        address\n        decimals\n        __typename\n      }\n      amount\n      __typename\n    }\n    __typename\n  }\n}"}
    dataRequest['variables']['addressList'] = walletAddressList
    header = {'Content-Type':'application/json'}

    r = requests.post('https://api.thegraph.com/subgraphs/name/realtoken-thegraph/rmm-v3-wrapper-gnosis',data=json.dumps(dataRequest), headers=header)

    if r.status_code == 200:
        try:
            result = []
            balanceData = json.loads(r.content)['data']['users']
            for adresses in balanceData:
                for item in  adresses['balances']:
                    token = item['token']
                    token['walletOwner'] = adresses['id']
                    token['amount'] = float(item['amount']) / (10 ** int(token['decimals']))
                    result.append(token)
        except:
            print(f"Error during decoding RMMv3 balance for wallet: { walletAddressList }: result { r.content }")
    else:
        print("Erreur de recupération de la balance RMM v3")

    # result est un tableau d'objet contenant les infos suivantes
    #{'name': 'RealToken S 13628 Tacoma St Detroit MI', 'walletOwner': '0xaaaaaaaaaaa', 'decimals': 18, '__typename': 'RealToken', 'wallet': '0xccb02e7cbfa20f05391190b219cfdd84a7688d47', 'amount': '5000000000000000000'}

    return result


def getGnosisBalance_v2(walletAddressList):
    
    dataRequest = {"operationName":"RealTokenQuery","variables":{"addressList":[""]},"query":"query RealTokenQuery($addressList: [String]!) {\n  accounts(where: {address_in: $addressList}) {\n    address\n    balances(\n      where: {amount_gt: \"0\"}\n      first: 1000\n      orderBy: amount\n      orderDirection: desc\n    ) {\n      token {\n        address\n        }\n      amount\n      }\n    }\n}"}
    dataRequest['variables']['addressList'] = walletAddressList
    header = {'Content-Type':'application/json'}
    r = requests.post('https://api.thegraph.com/subgraphs/name/realtoken-thegraph/realtoken-xdai',data=json.dumps(dataRequest), headers=header)

    if r.status_code == 200:
        try:
            result = []
            balanceData = json.loads(r.content)['data']['accounts']
            for adresses in balanceData:
                for item in  adresses['balances']:
                    token = item['token']
                    token['wallet'] = adresses['address']
                    token['amount'] = item['amount']
                    result.append(token)
            #GnosisContentAmount = result['data']['accounts'][0]['balances']
            #GnosisContent = [token['token']['address'].upper() for token in result['data']['accounts'][0]['balances']]
        except:
            print(f"Gnosis balance request decoding error for wallet: { walletAddressList }: result { r.content }")
    else:
        print("Erreur de recupération de la liste des tokens RealT")
    
    return result

def getPropertiesList():
    realtTokenList = []
    realTokenDict = dict()
    r = requests.get('https://dashboard.realt.community/api/properties')

    if r.status_code == 200:
        realtTokenList = json.loads(r.content)

        # Remove OLD- tokens
        realtTokenList = [property for property in realtTokenList if property['fullName'].startswith('OLD-') is False]
        for asset in realtTokenList:
            # add icon & icon color info
            asset['icon'] = setIcon(asset)
            asset['iconColorClass'] = setIconColor(asset)
            realTokenDict[asset['gnosisContract'].lower()] = asset
    else:
        print("Erreur de recupération de la liste des tokens RealT")
    return realTokenDict

def setIcon(asset):
    # Compute icon based on type of real estate
    result = 'fa-location-dot' #default color
    if asset['propertyType'] == 1:
        result = 'fa-house'
    if asset['propertyType'] == 2:
        result = 'fa-building'
    if asset['propertyType'] == 3 : #Duplex
        result = 'fa-people-roof'
        # token['icon'] = 'fa-vihara'
    if asset['propertyType'] == 8 : #Quadplex
        result = 'fa-people-roof'
        # token['icon'] = 'fa-vihara'
    if asset['propertyType'] == 4:
        result = 'fa-umbrella-beach'
    if asset['propertyType'] == 10: #Holding
        result = 'fa-house'
    if asset['propertyType'] == 6: #Mixed-use
        result = 'fa-shop'

    return result

def setIconColor(asset):
    result = 'orange-icon' #default color
    if asset['rentedUnits'] == 0:
        result = 'red-icon'
    elif asset['rentedUnits'] == asset['totalUnits']:
        result = 'green-icon'

    return result


def validateWallets(wallet1, wallet2):
    walletList = []
    if len(wallet1.lower()) and wallet1.lower().startswith('0x'):
        walletList.append(wallet1.lower())
    if len(wallet2.lower()) and wallet2.lower().startswith('0x'):
        walletList.append(wallet2.lower())

    return walletList


def displayWalletContent(walletList):
    #get list of realt properties
    realTassets = getPropertiesList()

    if len(walletList) > 0:
        gnosisAssets = getGnosisBalance_v2(walletList)
        rmmAssets = getRmmV3Balance(walletList)
        print(f"Properties in wallet : {len(gnosisAssets)} / Properties in RMM v3 : {len(rmmAssets)}")
        
        ownedProperties = []
        ownedPropertiesDict = dict()
        for gnosisAsset in gnosisAssets:
        # going through the assets present in the wallet list
            try:
                if gnosisAsset['address'].lower() in ownedPropertiesDict.keys():
                    # Case where the same property is present in the different wallet
                    #do not add the property, just increase the ownedAmount
                    addProperty = ownedPropertiesDict[gnosisAsset['address'].lower()]
                    addProperty['ownedAmount'] = float(addProperty['ownedAmount']) + float(gnosisAsset['amount'])
                    addPropertyDict = {gnosisAsset['address'].lower(): addProperty}
                    ownedPropertiesDict.update(addPropertyDict)
                else:                
                    addProperty = realTassets[gnosisAsset['address']]
                    addProperty['ownedAmount'] = float(gnosisAsset['amount'])
                    addPropertyDict = {gnosisAsset['address'].lower(): addProperty}
                    ownedPropertiesDict.update(addPropertyDict)
            except:
                print(f"Asset not found: {gnosisAsset}")
                traceback.print_exc()

        for rmmAsset in rmmAssets:
        # going through the assets present in the RMM
            try:
                # test if rmm asset is already present in owned asset
                if rmmAsset['address'].lower() in ownedPropertiesDict.keys():
                    #do not add the property, just increase the ownedAmount
                    addProperty = ownedPropertiesDict[rmmAsset['address'].lower()]
                    addProperty['ownedAmount'] = float(addProperty['ownedAmount']) + rmmAsset['amount']
                    addPropertyDict = {rmmAsset['address'].lower(): addProperty}
                    ownedPropertiesDict.update(addPropertyDict)

                else: # not present
                    addProperty = realTassets[rmmAsset['address']]
                    addProperty['ownedAmount'] = rmmAsset['amount']
                    
                    #ownedPropertiesDict[gnosisAsset['address'].lower()] = addProperty
                    
                    addPropertyDict = {rmmAsset['address'].lower() : addProperty}
                    ownedPropertiesDict.update(addPropertyDict)
                    #ownedProperties.append(addProperty)
            except:
                print(f"RMM Asset not found: {rmmAsset}")
                traceback.print_exc()
        
    else:
        #No wallet provided. Display the whole realt portfolio
        ownedPropertiesDict = realTassets
    
    print(f"Total unique properties : {len(ownedPropertiesDict.values())}")
    return ownedPropertiesDict.values()


app=Flask(__name__)

@app.route('/', methods=["GET", "POST"])
async def main():

    if request.method == "POST":
        # Get shops data from OpenStreetMap

        wallet01 = request.form["walAddress"]
        wallet02 = request.form["walAddress2"]
        walletList = validateWallets(wallet01, wallet02)
        print(f"Wallet list : {walletList}")

        walletContent = displayWalletContent(walletList)


        return render_template('index.html',ownedAsset=walletContent )

    else:
        # Render the input form
        return render_template('input.html')



if __name__ == '__main__':
    
    #app.run(host="0.0.0.0", port=8080, debug=True)

    http_server = WSGIServer(('', 8080), app)
    http_server.serve_forever()
