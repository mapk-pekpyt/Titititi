import json
import random
from datetime import datetime
from .common import get_name

FILE = "data/sisi.json"
TRIGGER = "/sisi"
EMOJI = "🎀"

def weighted_random():
    roll = random.randint(1, 100)
    if roll <= 60:     # 60%
        return random.randint(1, 5)
    elif roll <= 80:   # 20%
        return random.randint(0, 1)
    else:              # 20%
        return random.randint(6, 10)

def handle(bot, message):
    if not message.text:
        return

    if message.text.split("@")[0] != TRIGGER:
        return

    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    name = get_name(message.from_user)

    try:
        with open(FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}

    if chat_id not in data:
        data[chat_id] = {}

    if user_id not in data[chat_id]:
        data[chat_id][user_id] = {"name": name, "size": 0, "last_day": ""}

    user = data[chat_id][user_id]

    today = datetime.now().strftime("%Y-%m-%d")

    # проверка на 1 раз в сутки
    if user["last_day"] == today:
        bot.send_message(
            message.chat.id,
            f"{EMOJI} {name}, ты уже играла сегодня\nТвой размер груди — {user['size']}"
        )
        return

    # генерируем рост
    increase = weighted_random()

    # прибавляем
    user["size"] += increase
    user["last_day"] = today
    user["name"] = name

    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

    bot.send_message(
        message.chat.id,
        f"{EMOJI} {name}, твой размер груди вырос на {increase}\n"
        f"Теперь он — {user['size']}"
    )