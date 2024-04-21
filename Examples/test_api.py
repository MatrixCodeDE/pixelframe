import time

import requests

for y in range(10):
    for x in range(20):
        r = requests.post(f"http://0.0.0.0:8000/canvas/pixel?x={x}&y={y}&color=ffffff")
    time.sleep(2)
