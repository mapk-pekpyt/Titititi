import json
import os
from datetime import datetime, timedelta
from utils import get_display_name

FILE = "data/sisi.json"


def load():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)


def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def handle(bot, message):
    if message.text.lower() != "/sisi":
        return

    user_id = str(message.from_user.id)
    name = get_display_name(message.from_user)

    data = load()

    if user_id not in data:
        data[user_id] = {
            "size": 0,
            "last_play": "2000-01-01"
        }

    last_play = datetime.fromisoformat(data[user_id]["last_play"])
    now = datetime.now()

    # если играли сегодня — отказ
    if last_play.date() == now.date():
        bot.send_message(
            message.chat.id,
            f"{name} 🎀, ты уже играла сегодня!\n"
            f"Текущий размер груди — {data[user_id]['size']}"
        )
        return

    # рост от -10 до +10
    import random
    change = random.randint(-10, 10)

    # отрицательное не меньше нуля
    new_size = max(0, data[user_id]["size"] + change)
    data[user_id]["size"] = new_size
    data[user_id]["last_play"] = now.isoformat()

    save(data)

    if change >= 0:
        bot.send_message(
            message.chat.id,
            f"{name} 🎀, твоя грудь выросла на {change}!\n"
            f"Теперь размер — {new_size}"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"{name} 🎀, твоя грудь уменьшилась на {abs(change)}...\n"
            f"Теперь размер — {new_size}"
        )