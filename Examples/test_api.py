import hashlib
import random
import time

import requests

pps = requests.get(f"http://0.0.0.0:8000/canvas/pps")
delay = 1 / int(pps.text)
print("Sleeping", delay)

for y in range(20):
    for x in range(20):
        r = requests.put(
            f"http://0.0.0.0:8000/canvas/pixel?x={x+100}&y={y+100}&color={hashlib.sha1(f'{random.randint(0,9187489724)}'.encode()).hexdigest()[:6]}"
        )
        print(r.status_code)
        time.sleep(delay)
