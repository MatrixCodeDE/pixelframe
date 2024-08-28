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

image = Image.open(img_source).convert("RGB")

pps = requests.get(f"{uri}/canvas/pps")
delay = 1 / int(pps.text)
print(f"Printing {pps.text} pixel/sec")

for y in range(image.height):
    for x in range(image.width):
        r, g, b = image.getpixel((x, y))
        color = "%02x%02x%02x" % (r, g, b)
        req = requests.put(
            f"{uri}/canvas/pixel?x={x + offset[0]}&y={y + offset[1]}&color={color}"
        )
        if req.status_code != 200:
            print("Failed")
            time.sleep(1)
        time.sleep(delay + 0.0001)
