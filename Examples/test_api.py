import requests

for y in range(50):
    for x in range(50):
        r = requests.post(f"http://0.0.0.0:8000/canvas/pixel?x={x}&y={y}&color=ffffff")

