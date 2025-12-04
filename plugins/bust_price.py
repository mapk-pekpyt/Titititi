import json
import os

FILE = "plugins/bust_price.json"

def get_price():
    if not os.path.exists(FILE):
        return 0
    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return int(data.get("price", 0))

def save_price(price):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump({"price": int(price)}, f, indent=2)