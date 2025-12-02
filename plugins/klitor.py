import json
import os

DATA_FILE = "data/klitor.json"
EMOJI = "💎"

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

def handle(bot, message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    data = load_data()
    current = data.get(str(user_id), {}).get("size_mm", 0) + 5  # мм
    data[str(user_id)] = {"name": name, "size_mm": current}
    save_data(data)
    bot.reply_to(message, f"{EMOJI} {name}, ваш клитор теперь {current/10:.1f} см!")