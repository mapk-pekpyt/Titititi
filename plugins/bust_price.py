# plugins/bust_price.py
import json, os

FILE = "data/bust_price.json"
os.makedirs("data", exist_ok=True)

def get_price():
    if not os.path.exists(FILE):
        return 0
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return int(data.get("price", 0))
    except:
        return 0

def save_price(p):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump({"price": int(p)}, f, indent=2)