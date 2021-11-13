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
    else:
        accSwitch = None
    parent_nft = deploy()
    child_nft = deploy_child(
        "https://ipfs.io/ipfs/QmRp7XDAybaQSKf9BXCZn4VVyMgF6kfVBCB3LtWBuZdRYE?filename=test2ipfs.png"
    )
    child_nft2 = deploy_child(
        "https://ipfs.io/ipfs/QmQ9jJ3AjjmPPvNGwBUCbrLvr85ZeBHJ6N4Rv6EaUW2wGL?filename=test3impfs.png"
    )
    child_nft3 = deploy_child(
        "https://ipfs.io/ipfs/QmSfR9ZNQ8gDkS7xdRahqLkZkFPD1qUfW7j8Jsx7bCAs7H?filename=sunCL.png"
    )
    createChild(child_nft)
    createChild(child_nft)
    createChild(child_nft, accSwitch)
    createChild(child_nft2, accSwitch)
    createChild(child_nft2, accSwitch)
    createChild(child_nft3)
    createChild(child_nft3, accSwitch)

    parent_token_id = 0  # for testing
    open_parent_and_add(
        parent_nft,
        parent_token_id,
        child_nft3,
        0,
    )
    open_parent_and_add(parent_nft, parent_token_id, child_nft, 0)
    open_parent_and_add(parent_nft, parent_token_id, child_nft, 1)
    open_parent_and_add(parent_nft, parent_token_id, child_nft, 2, accSwitch)
    open_parent_and_add(parent_nft, parent_token_id, child_nft2, 0, accSwitch)
    open_parent_and_add(parent_nft, parent_token_id, child_nft2, 1, accSwitch)
    open_parent_and_add(parent_nft, parent_token_id, child_nft3, 1, accSwitch)
    # local_path_array = pull_images(parent_token_id, parent_nft)
    # print_test_info(parent_token_id, parent_nft)
    # for testing, transfer a child NFT here
    account1 = get_account()
    account2 = get_account(1)
    tx = child_nft.safeTransferFrom(account1, account2, 0, {"from": account1})
    print(f"sending token from {account1} to {account2}")
    tx.wait(1)
    tx2 = child_nft2.safeTransferFrom(account2, account1, 0, {"from": account2})
    print(f"sending token from {account2} to {account1}")
    tx2.wait(1)

    # print_test_info(parent_token_id, parent_nft)
    # print(f"owner of token 0...{child_nft.ownerOf(0)}")
    check_img_and_push_uri(parent_token_id, parent_nft)


def check_img_and_push_uri(parent_token_id, parent_nft):
    # simulate what the keeper/EA is doing - do the check/verify/republish
    account = get_account()
    # tx = parent_nft.checkActiveStatusesAndGenerateImg({"from": account})
    print("pulling images...")
    img_data_array = pull_images(parent_token_id, parent_nft)
    print("images pulled")
    print("combining images...")
    ipfs_loc = combine_images(parent_token_id, parent_nft, img_data_array)
    print("images combined and uploaded, setting token uri")
    set_tokenURI(parent_token_id, parent_nft, ipfs_loc)


def combine_images(parent_token_id, parent_nft, img_data_array):
    # iterate through local path array to pull those images into PIL Image of the right size
    # then save combined image to ipfs
    imgs = [
        # loading png from ipfs to memory (as bytes) then reading it back into Image
        # https://stackoverflow.com/questions/18491416/pil-convert-bytearray-to-image
        Image.open(io.BytesIO(child_struct_id))
        for child_struct_id in img_data_array
    ]
    for child_struct_id in range(len(imgs)):
        # check nft statuses here
        child_nft_status = parent_nft.activeMapping(parent_token_id, child_struct_id)
        print(f"status of token id {child_struct_id} is {child_nft_status}")
        if child_nft_status == False:
            print(f"killing NFT for {child_struct_id}")
            imgs[child_struct_id] = kill_nft_img(imgs[child_struct_id])

    # for each child token, pull image into a binary
    # image manipulation from https://stackoverflow.com/questions/30227466/combine-several-images-horizontally-with-python
    # local_img.show()
    # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)

    ####min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
    # imgs_comb = np.hstack((np.asarray(i.resize(min_shape)) for i in imgs))
    ####imgs_comb = np.hstack((np.asarray(i.resize(min_shape)) for i in imgs))

    img_tile_width = math.ceil(math.sqrt(len(imgs)))
    print(math.floor(math.sqrt(len(imgs))))  # to height
    img_tile_height = math.floor(math.sqrt(len(imgs)))

    widths, heights = zip(*(i.size for i in imgs))

    min_width = min(widths)
    min_height = min(heights)
    total_width = img_tile_width * min_width
    total_height = img_tile_height * min_width

    new_im = Image.new(
        "RGB", (total_width, total_height), (255, 255, 255)
    )  # initialize a white bg

    newsize = min_width, min_height
    x_offset = 0
    y_offset = 0
    img_counter = 0
    for im in imgs:
        new_im.paste(im.resize(newsize), (x_offset, y_offset))
        x_offset += min_width
        img_counter = img_counter + 1
        if (img_counter % img_tile_width) == 0:
            print("next row")
            y_offset += min_height
            x_offset = 0

    # save that beautiful picture
    ###imgs_comb = Image.fromarray(imgs_comb)
    # file_path = f"./img/parentimg-{parent_token_id}+{parent_nft}.png"  # .png vs .jpg -> can just change extension but .jpg loses img quality.
    # imgs_comb.save(file_path)
    ipfs_loc = upload_to_ipfs(new_im, parent_nft.address, parent_token_id)
    return ipfs_loc


def kill_nft_img(original_image):
    # from https://stackoverflow.com/questions/6161219/brightening-or-darkening-images-in-pil-without-built-in-functions
    # load the original image into a pixels list as param
    pixels = original_image.getdata()
    # initialise the new image
    new_image = Image.new("RGB", original_image.size)
    new_image_list = []
    brightness_multiplier = 1.0  # for testing
    extent = (
        85  # in percent, an int between 0 and 100. as extent increases, img gets darker
    )
    brightness_multiplier -= float(extent / 100)

    # for each pixel, append the brightened or darkened version to the new image list
    for pixel in pixels:
        new_pixel = (
            int(pixel[0] * brightness_multiplier),
            int(pixel[1] * brightness_multiplier),
            int(pixel[2] * brightness_multiplier),
        )

        # check the new pixel values are within rgb range
        for pixel in new_pixel:
            if pixel > 255:
                pixel = 255
            elif pixel < 0:
                pixel = 0

        new_image_list.append(new_pixel)

    # save the new image
    original_image.putdata(new_image_list)
    return original_image


def pull_images(parent_token_id, parent_nft):
    data = ""
    img_data_array = []
    for child_struct_id in range(parent_nft.childTokenCount(parent_token_id)):
        # this for loop goes through child tokens of a given parent to pull info about each
        # data = f"{data} + {parent_nft.tokenMapping(parent_token_id,ctoken_id)}"
        # grabbing token at location "child_struct_id" in the structure array related to the mapping
        child_address = parent_nft.tokenMapping(parent_token_id, child_struct_id)[1]
        child_token_id = parent_nft.tokenMapping(parent_token_id, child_struct_id)[2]
        child_nft = interface.IERC721Metadata(child_address)
        img = child_nft.tokenURI(child_token_id)
        print(
            f"this nft is from {child_address} of token id {child_token_id} with img location = {img}"
        )
        # pull ipfs image down locally to do action on
        img_data = pull_from_ipfs(img)
        print(f"img_data bytes is {img_data}")
        if img_data != 0:
            img_data_array.append(img_data)
            print(
                f"image for child_struct_id {child_struct_id} is {img_data_array[child_struct_id]}"
            )
    return img_data_array


def set_tokenURI(token_id, nft_contract, tokenURI):
    account = get_account()
    tx = nft_contract.setTokenURI(token_id, tokenURI, {"from": account})
    tx.wait(1)
    print(
        f"Awesome! Token URI of NFT contract {nft_contract} and token ID {token_id} set to {tokenURI}"
    )


def pull_from_ipfs(ipfs_address):
    # ipfs_url = "http://127.0.0.1:5001"
    # endpoint = "/api/v0/get" #alternate way of doing this? IDK
    request = requests.get(
        ipfs_address
    )  # not sure on formatting here. https://stackoverflow.com/questions/30229231/python-save-image-from-url. Postman had alternate
    # print(f"request is {requests} with response {response}")
    if request.status_code == 200:
        print("Call succeeded")
        return (
            request.content
        )  # return img content that we'd otherwise write to a file.
    else:
        print("Call didnt succeed")
        return 0
    # "./img/0-PUG.png" -> "0-PUG.png"


def upload_to_ipfs(imgs_comb: Image, parent_address, parent_token_id):
    # back to byte array https://stackoverflow.com/questions/33101935/convert-pil-image-to-byte-array
    image_binary = io.BytesIO()
    imgs_comb.save(image_binary, format="PNG")  # maybe can assume PNG here?
    image_binary = image_binary.getvalue()
    ipfs_url = "https://ipfs.infura.io:5001"
    endpoint = "/api/v0/add"
    response = requests.post(ipfs_url + endpoint, files={"file": image_binary})
    ipfs_hash = response.json()["Hash"]
    # "./img/0-PUG.png" -> "0-PUG.png"
    filename = f"fam_foto_{parent_address}_{parent_token_id}.png"
    image_uri = f"https://ipfs.io/ipfs/{ipfs_hash}?filename={filename}"
    print(f"parent URI in ipfs is at {image_uri}")
    return image_uri


def print_test_info(parent_token_id, parent_nft):
    for child_struct_id in range(parent_nft.childTokenCount(parent_token_id)):
        # this for loop goes through child tokens of a given parent to pull info about each
        # data = f"{data} + {parent_nft.tokenMapping(parent_token_id,ctoken_id)}"
        # grabbing token at location "child_struct_id" in the structure array related to the mapping
        print(f"DEBUG: {parent_nft.tokenMapping(parent_token_id, child_struct_id)}")
    # print(f"for loop - {data}") #for checking the mapping and array of ChildNFT structs
