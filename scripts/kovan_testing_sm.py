# deploying parent NFT and some children to test with
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
)
from brownie import testChildNFT, ParentNFT, interface, network, config
from PIL import Image
from pathlib import Path
import requests
import math
import io

# import numpy as np #note numpy is too big and docker takes forever


def deploy():
    account = get_account()
    parent_nft = ParentNFT.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    creating_tx = parent_nft.makeNewGroup({"from": account})
    creating_tx.wait(1)
    print("New parent token has been created!")
    return parent_nft


def deploy_child(ipfs_loc=None, index=None):
    account = get_account(index)
    # We want to be able to use the deployed contracts if we are on a testnet
    # Otherwise, we want to deploy some mocks and use those
    # Rinkeby
    child_nft = testChildNFT.deploy(
        ipfs_loc,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print(f"New child nft address created @address {child_nft.address}")
    return child_nft


def createChild(child_nft, index=None):
    account = get_account(index)
    tx = child_nft.createNew({"from": account})
    tx.wait(1)
    print(f"New child token(s) created by {account}")


def open_parent_and_add(
    parent_nft, parent_token_id, child_nft, child_token_id, index=None
):
    account = get_account(index)
    print(f"The parent currently has {parent_nft.tokenCounter()} tokens")
    print(f"parent token status is {parent_nft.tokenStatusMap(parent_token_id)}")
    tx = parent_nft.addMyToken(
        parent_token_id, child_nft.address, child_token_id, {"from": account}
    )
    tx.wait(1)
    print(
        f"parent nft children are {parent_nft.tokenMapping(parent_token_id,child_token_id)}"  # child_token_id being place in array Child struct array?
    )
    # print(f"parent nft children are {parent_nft.tokenMapping(parent_token_id).length}")


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
    parent_nft = deploy()
    child_nft = deploy_child(
        "https://ipfs.io/ipfs/QmRp7XDAybaQSKf9BXCZn4VVyMgF6kfVBCB3LtWBuZdRYE?filename=test2ipfs.png"
    )
    createChild(child_nft)
    createChild(child_nft)
    """child_nft2 = deploy_child(
        "https://ipfs.io/ipfs/QmQ9jJ3AjjmPPvNGwBUCbrLvr85ZeBHJ6N4Rv6EaUW2wGL?filename=test3impfs.png"
    )
    
    createChild(child_nft)
    createChild(child_nft, accSwitch)
    createChild(child_nft2, accSwitch)
    createChild(child_nft2, accSwitch)
    """

    open_parent_and_add(parent_nft, 0, child_nft, 0)
    open_parent_and_add(parent_nft, 0, child_nft, 1)
    """child_token_id = 1
    open_parent_and_add(parent_nft, parent_token_id, child_nft, child_token_id)
    child_token_id = 2
    open_parent_and_add(
        parent_nft, parent_token_id, child_nft, child_token_id, accSwitch
    )  # from different account
    child_token_id = 0
    open_parent_and_add(
        parent_nft, parent_token_id, child_nft2, child_token_id, accSwitch
    )
    child_token_id = 1
    open_parent_and_add(
        parent_nft, parent_token_id, child_nft2, child_token_id, accSwitch
    )"""
    # local_path_array = pull_images(parent_token_id, parent_nft)
    # print_test_info(parent_token_id, parent_nft)
    # for testing, transfer a child NFT here
    """account1 = get_account()
    account2 = get_account(accSwitch)
    tx = child_nft.safeTransferFrom(account1, account2, 0, {"from": account1})
    print(f"sending token from {account1} to {account2}")
    tx.wait(1)
    tx2 = child_nft2.safeTransferFrom(account2, account1, 0, {"from": account2})
    print(f"sending token from {account2} to {account1}")
    tx2.wait(1)"""

    # stop here so i can interact via kovan etherscan
