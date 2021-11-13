from scripts import deploy
from PIL import Image
import math


def main():
    # f = r"./img/parentimg-0+0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87.png"
    # img = Image.open(f)
    ipfs_address = "ipfs://QmXjYkKEqG11gruTMzXght6FBTKyeu8D7wpkPGW3ZpEfQ4/1818"
    if ipfs_address.startswith("ipfs://"):
        ipfs_hash = ipfs_address.partition("ipfs://")[2]
        ipfs_address = f"https://ipfs.io/ipfs/{ipfs_hash}"

    print(ipfs_address)
    """
    images = [
        Image.open(x)
        for x in [
            "./img/test2ipfs.png",
            "./img/test2ipfs.png",
            "./img/test2ipfs.png",
        ]
    ]
    print(len(images))
    print(math.sqrt(len(images)))
    print(math.ceil(math.sqrt(len(images))))  # to width.
    img_tile_width = math.ceil(math.sqrt(len(images)))
    print(f"sqrt floor ht: {math.floor(math.sqrt(len(images)))}")  # to height
    print(f"div,ceil floor ht: {math.ceil(len(images)/img_tile_width)}")
    img_tile_height = math.ceil(len(images) / img_tile_width)

    widths, heights = zip(*(i.size for i in images))

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
    for im in images:
        new_im.paste(im.resize(newsize), (x_offset, y_offset))
        x_offset += min_width
        img_counter = img_counter + 1
        if (img_counter % img_tile_width) == 0:
            print("next row")
            y_offset += min_height
            x_offset = 0

    print(f"img width {total_width}")
    print(f"img height {total_height}")
    new_im.save("./img/new_tileimg.png")
    new_im.show()
    """
