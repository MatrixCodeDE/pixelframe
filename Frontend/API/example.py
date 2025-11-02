# I didn't want to include it in the Examples folder so you see this in here :)

import json

import requests
from PIL import Image


def rgb_to_hex(r: int, g: int, b: int, a: int) -> str:
    return "%02x%02x%02x%02x" % (r, g, b, a)


def image_resize(image: Image, factor: float | int = 1) -> Image:
    nh = int(image.height * factor)
    nw = int(image.width * factor)
    return image.resize((nw, nh))


if __name__ == "__main__":

    host: str = "0.0.0.0"
    enable_https: bool = False
    port_api: int = 8443
    port_socket: int = 1234

    username = "admin"
    password = "root123"

    uri = f"http{'s' if enable_https else ''}://{host}:{port_api}"
    img_source = "~/Pictures/test.png"

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"username={username}&password={password}"
    bearer_req = requests.post(f"{uri}/login", data=data, headers=headers)
    auth_header = {"Authorization": "Bearer " + bearer_req.json()["access_token"]}

    image = Image.open(img_source).convert("RGBA")
    # uncomment if you want to resize the picture
    # image = image_resize(image, 0.3)

    offset = (500, 300)

    pixelarray = []
    print(image.height, image.width, image.height * image.width)
    for py in range(image.height):
        for px in range(image.width):
            color = image.getpixel((px, py))
            hex = rgb_to_hex(*color)
            pixelarray.append([px + offset[0], py + offset[1], hex])

    index = 0
    while index < len(pixelarray):
        index += 10000
        data = {"pixels": pixelarray[index - 10000 : index]}
        print(len(pixelarray[index - 10000 : index]))
        pxjson = json.dumps(data)
        print("Sending image request")
        img_req = requests.put(f"{uri}/admin/pixel", data=pxjson, headers=auth_header)
        print(img_req.status_code, img_req.reason)
