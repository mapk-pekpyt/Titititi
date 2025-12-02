import json
import os

DATA_FILE = "data/hui.json"
EMOJI = "🍆"

def load_data():
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def add_score(user_id, name, score):
    data = load_data()
    data[str(user_id)] = {"name": name, "size": score}
    save_data(data)

def get_top():
    data = load_data()
    sorted_data = sorted(data.items(), key=lambda x: x[1].get("size", 0), reverse=True)
    text = f"🏆 Топ {EMOJI}:\n"
    for i, (user_id, info) in enumerate(sorted_data[:5], 1):
        text += f"{i}. {info.get('name', user_id)} — {info.get('size', 0)}\n"
    return text