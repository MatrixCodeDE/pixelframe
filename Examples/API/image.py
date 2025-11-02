import time

import requests
from PIL import Image

host: str = "0.0.0.0"
enable_https: bool = True
port_api: int = 8443
port_socket: int = 1234

uri = f"http{'s' if enable_https else ''}://{host}:{port_api}"
img_source = "~/Downloads/cmy.png"

offset = (100, 200)  # (x, y)
scale = (1, 1)  # (x, y)

image = Image.open(img_source).convert("RGB")
rsx = image.width // scale[0]
rsy = image.width // scale[0]
image.resize((rsx, rsy))

pps = requests.get(f"{uri}/canvas/pps")

size = requests.get(f"{uri}/canvas/size").json()
sx = size["x"]
sy = size["y"]
if (image.width + offset[0] > sx) or (image.height + offset[1] > sy):
    p = input("[!] Your image goes out of bounds! Continue? (y/n): ")
    if p.lower() != "y":
        exit()

delay = 1 / int(pps.text)
print(f"Printing {pps.text} pixel/sec")


def getpixel(x: int, y: int):
    req = requests.get(
        f"{uri}/canvas/pixel?x={x + offset[0]}&y={y + offset[1]}&color={color}"
    )
    return req.content.json()


def putpixel(x: int, y: int, color: str):
    global pps
    req = requests.put(
        f"{uri}/canvas/pixel?x={x + offset[0]}&y={y + offset[1]}&color={color}"
    )
    if req.status_code != 201:
        print(req.content)
        pps = int(requests.get(f"{uri}/canvas/pps").text)
        print(f"Sleeping for {pps}s")
        time.sleep(1 / pps)
        putpixel(x, y, color)


for y in range(image.height):
    for x in range(image.width):
        if x % 50 == 0:
            pps = requests.get(f"{uri}/canvas/pps")  # detect pps changes

        r, g, b = image.getpixel((x, y))
        color = "%02x%02x%02x" % (r, g, b)

        col = getpixel(x, y)
        if col.text == color:
            continue

        putpixel(x, y, color)
        time.sleep(delay + 0.0001)
