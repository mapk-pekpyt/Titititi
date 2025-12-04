import json
import os

FILE = "bust_price.json"

# если файла нет — создаём с дефолтной ценой 1 евро
if not os.path.exists(FILE):
    with open(FILE, "w") as f:
        json.dump({"price": 1}, f)

def load_price():
    with open(FILE, "r") as f:
        return json.load(f)

def save_price(new_price: int):
    with open(FILE, "w") as f:
        json.dump({"price": new_price}, f)