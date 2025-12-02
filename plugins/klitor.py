import json
import os
from datetime import datetime
from utils import get_display_name

FILE = "data/klitor.json"


def load():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)


def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def handle(bot, message):
    if message.text.lower() != "/klitor":
        return

    user_id = str(message.from_user.id)
    name = get_display_name(message.from_user)

    data = load()

    if user_id not in data:
        data[user_id] = {
            "size_mm": 0,
            "last_play": "2000-01-01"
        }

    last_play = datetime.fromisoformat(data[user_id]["last_play"])
    now = datetime.now()

    if last_play.date() == now.date():
        bot.send_message(
            message.chat.id,
            f"{name} 💎, ты уже играла сегодня!\n"
            f"Текущий размер — {data[user_id]['size_mm']} мм"
        )
        return

    import random
    change = random.randint(-10, 10)

    new_size = max(0, data[user_id]["size_mm"] + change)
    data[user_id]["size_mm"] = new_size
    data[user_id]["last_play"] = now.isoformat()

    save(data)

    if change >= 0:
        bot.send_message(
            message.chat.id,
            f"{name} 💎, твой клитор вырос на {change} мм!\n"
            f"Теперь размер — {new_size} мм"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"{name} 💎, твой клитор уменьшился на {abs(change)} мм...\n"
            f"Теперь размер — {new_size} мм"
        )