import json
import os
import random
from datetime import datetime
import pytz

TRIGGER = "/sisi"
FILE = "data/sisi.json"

def get_name(user):
    if user.username:
        return "@" + user.username
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    return user.first_name or "Безымянный"

# вероятность: 1–5 — часто, остальные редко
def weighted_random():
    r = random.randint(1, 100)

    if r <= 65:              # 65%
        return random.randint(1, 5)
    elif r <= 80:            # 15%
        return random.randint(6, 10)
    else:                    # 20%
        return random.randint(-10, 0)

def load():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def handle(bot, message):
    if not message.text or not message.text.lower().startswith(TRIGGER):
        return

    user = message.from_user
    uid = str(user.id)
    name = get_name(user)

    tz = pytz.timezone("Europe/Berlin")
    today = datetime.now(tz).strftime("%Y-%m-%d")

    data = load()

    if uid not in data:
        data[uid] = {"size": 0, "last": "2000-01-01", "name": name}

    # ежедневный рост
    if data[uid]["last"] != today:
        delta = weighted_random()

        # не даём уйти в минус
        if data[uid]["size"] + delta < 0:
            delta = -data[uid]["size"]

        data[uid]["size"] += delta
        data[uid]["last"] = today
        data[uid]["name"] = name

        save(data)

        bot.reply_to(message,
            f"{name} 🎀\n"
            f"Твой размер груди изменился на {delta}.\n"
            f"Теперь размер: {data[uid]['size']}"
        )
        return

    # если уже играл сегодня
    bot.reply_to(message,
        f"{name} 🎀 ты уже играла сегодня!\n"
        f"Твой текущий размер груди: {data[uid]['size']}"
    )