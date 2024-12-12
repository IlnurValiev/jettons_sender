import requests
from os import getenv
from dotenv import load_dotenv

load_dotenv()

endpoint = f"{getenv("WEB_ENDPOINT")}/payment_data"
jetton_master_address = getenv("JETTON_MASTER_ADDRESS")

id = 11

data_ton = {
    "payload_text":f"giveaway_id:{id}:ton",
    "amount":1,
    "type":"TON",
    "sender":jetton_master_address,
}

data_jetton = {
    "payload_text":f"giveaway_id::jetton",
    "amount":2,
    "type":"JETTON",
    "sender":"EQAgamQ0FD-cx45wDuIyOuKrJwTngL0detHEjRVo2YaAvJxZ",
    "jetton_metadata":{
        "symbol":"LIFEYT"
    },
    "jetton_master_address":jetton_master_address
}

requests.post(endpoint, json=data_ton)

requests.post(endpoint, json=data_jetton)