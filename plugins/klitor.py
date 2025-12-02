import random
import os
import json

DATA_FILE = "data/klitor.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def handle(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {"size": 0, "last_played": ""}
    from datetime import date
    today = str(date.today())
    if data[user_id]["last_played"] == today:
        bot.send_message(message.chat.id,
                         f"Упс, {message.from_user.first_name}, ты уже играл сегодня 😅\n"
                         f"Твой клитор: {data[user_id]['size']/10:.1f} см")
        return
    delta = random.randint(-10, 10)
    data[user_id]["size"] = max(0, data[user_id]["size"] + delta)
    data[user_id]["last_played"] = today
    save_data(data)
    bot.send_message(message.chat.id,
                     f"{message.from_user.first_name} 💦 твой клитор вырос на {delta} мм, "
                     f"теперь он равен {data[user_id]['size']/10:.1f} см")