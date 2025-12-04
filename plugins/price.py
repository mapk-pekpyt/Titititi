import json
import os

PRICE_FILE = "bust_global_price.json"

def load_price():
    if not os.path.exists(PRICE_FILE):
        return {"price": 5}
    return json.load(open(PRICE_FILE, "r"))

def save_price(price):
    json.dump({"price": price}, open(PRICE_FILE, "w"), indent=4)

# актуальная цена
price_data = load_price()