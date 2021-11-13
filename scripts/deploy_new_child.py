# deploying parent NFT and some children to test with
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
)
from brownie import testChildNFT, network, config

# import numpy as np #note numpy is too big and docker takes forever


def main():
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
    ):  # for testing wtih multiple accounts - Kovan not yet supported by .env
        accSwitch = 1
    if (
        network.show_active() == "kovan"
    ):  # for testing wtih multiple accounts - Kovan not yet supported by .env
        accSwitch = 1
    else:
        accSwitch = None
    """
    https://ipfs.io/ipfs/QmZFjSSiLwrgEqK76uDbiLy9pygkr1M9hJ48MxofwStsux?filename=dona1609.png
    https://ipfs.io/ipfs/QmSMR5FarGx5Pkj9NaAgRNA5TD6nnKiVtAHVsT5D5zFRWD?filename=dona2526.png
    https://ipfs.io/ipfs/QmSk9mEHjGepPRS9aU9q4A5APdrZ38a6R3hkyMjXUqUXhT?filename=crystal5090.jpg

    https://api.ogcrystals.com/api/v1/crystals/meta/5090.json
    {"name":"OG:Crystal 5090","description":"This one-of-a-kind OG:Crystal reflects both the remarkable combinations of natural crystalline structures as well as its journey through the crypto wallets of the community. There is no other like it. Welcome to the REEF.","url":"https://ogcrystals.com","image":"https://api.ogcrystals.com/api/v1/crystals/images/original/5090/7.jpg","original":"https://api.ogcrystals.com/api/v1/crystals/images/original/5090/7.jpg","attributes":[{"trait_type":"Generation","value":"7"},{"trait_type":"Crystallization","value":"Done"},{"trait_type":"BAYC","value":"II"},{"trait_type":"Coral","value":"I"},{"trait_type":"Bright","value":"II"},{"trait_type":"Meebit","value":"I"},{"trait_type":"Fractal","value":"I"},{"trait_type":"Cryptopunk","value":"II"}]}
    ipfs://QmXjYkKEqG11gruTMzXght6FBTKyeu8D7wpkPGW3ZpEfQ4/1818
    {"name":"'Dona VIN#1818","description":"'Dona","image":"ipfs://Qmd3M8pw3NVNZZCYGkhQfvdya54yzAfAgmvwybXojpjiSc","attributes":[{"trait_type":"environment","value":"Internet Blue"},{"trait_type":"towing","value":"UHaul"},{"trait_type":"paint","value":"Just Enough Cream"},{"trait_type":"wheels","value":"Sad"},{"trait_type":"headlights","value":"Classic"},{"trait_type":"windows","value":"Clean"},{"trait_type":"upgrades","value":"New Kayak"}],"external_url":"https://jaypegsautomart.com/dona/1818"}

    https://storage.googleapis.com/hdpunks-cdn/metadata/33 
    hdpunk


    """
    child_nft = deploy_child(
        "ipfs://QmXjYkKEqG11gruTMzXght6FBTKyeu8D7wpkPGW3ZpEfQ4/1818"
    )
    createChild(child_nft)
    createChild(child_nft, accSwitch)


def deploy_child(ipfs_loc=None, index=None):
    account = get_account(index)
    # We want to be able to use the deployed contracts if we are on a testnet
    # Otherwise, we want to deploy some mocks and use those
    # Rinkeby
    child_nft = testChildNFT.deploy(
        ipfs_loc,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get(
            "verify", False
        ),  # to be able to move them in testing on Kovan
    )
    print(f"New child nft address created @address {child_nft.address}")
    return child_nft


def createChild(child_nft, index=None):
    account = get_account(index)
    tx = child_nft.createNew({"from": account})
    tx.wait(1)
    print(f"New child token(s) created by {account}")
