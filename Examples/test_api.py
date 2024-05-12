import time

import requests

for y in range(20):
    for x in range(20):
        r = requests.post(
            f"http://0.0.0.0:8000/canvas/pixel?x={x+100}&y={y+100}&color=ff00ff"
        )
        time.sleep(1)
