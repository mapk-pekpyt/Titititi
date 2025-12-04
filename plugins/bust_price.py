import json
import os

FILE_PATH = "bust_price.json"

# Загружаем / создаём цену буста
if os.path.exists(FILE_PATH):
    try:
        with open(FILE_PATH, "r") as f:
            price_data = json.load(f)
    except:
        price_data = {"bust_price": 50}
else:
    price_data = {"bust_price": 50}


def save_price():
    with open(FILE_PATH, "w") as f:
        json.dump(price_data, f)