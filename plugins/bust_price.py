# plugins/bust_price.py
import json
import os

PRICE_FILE = "data/bust_global_price.json"
DEFAULT_PRICE = 5

def ensure_dir():
    d = os.path.dirname(PRICE_FILE)
    if d:
        os.makedirs(d, exist_ok=True)

def load_price():
    ensure_dir()
    try:
        with open(PRICE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return int(data.get("price", DEFAULT_PRICE))
    except:
        return DEFAULT_PRICE

def save_price(v:int):
    ensure_dir()
    with open(PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump({"price": int(v)}, f)

# convenience variable (plugins can call load_price() each time)