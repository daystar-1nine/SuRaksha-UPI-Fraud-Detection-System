import requests

url = "http://127.0.0.1:5000/analyze/qr"

files = {
    "image": open(r"S:\Hackathon\Usefull Stuff\SuRaksha Demo\reward_qr.png", "rb")
}

data = {
    "intent": "receive"
}

response = requests.post(url, files=files, data=data)

import json

print(json.dumps(response.json(), indent=4))