import time

import requests
from PIL import Image

host = "0.0.0.0"
port = 8000
img_source = ""

offset = (100, 200)  # (x, y)

image = Image.open(img_source).convert("RGB")

pps = requests.get(f"http://0.0.0.0:8000/canvas/pps")
delay = 1 / int(pps.text)

for y in range(image.height):
    for x in range(image.width):
        r, g, b = image.getpixel((x, y))
        color = "%02x%02x%02x" % (r, g, b)
        req = requests.put(
            f"http://0.0.0.0:8000/canvas/pixel?x={x + offset[0]}&y={y + offset[1]}&color={color}"
        )
        if req.status_code != 200:
            print("Failed")
            time.sleep(1)
        time.sleep(delay + 0.0001)
