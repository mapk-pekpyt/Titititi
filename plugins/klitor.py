import json, os
from .common import german_time, weighted_random, get_name

TRIGGER = "/klitor"
FILE = "data/klitor.json"

def load():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def handle(bot, message):
    if not message.text or not message.text.startswith(TRIGGER):
        return

    user = message.from_user
    uid = str(user.id)
    name = get_name(user)

    today = german_time().strftime("%Y-%m-%d")
    data = load()

    if uid not in data:
        data[uid] = {"size_mm": 0, "last": "2000-01-01", "name": name}

    if data[uid]["last"] != today:
        delta = weighted_random() * 1  # в мм
        if data[uid]["size_mm"] + delta < 0:
            delta = -data[uid]["size_mm"]

        data[uid]["size_mm"] += delta
        data[uid]["last"] = today
        data[uid]["name"] = name
        save(data)

        bot.reply_to(message,
            f"{name} 💎\n"
            f"Твой клитор изменился на {delta} мм\n"
            f"Теперь размер: {data[uid]['size_mm']} мм"
        )
        return

    bot.reply_to(message,
        f"{name} 💎 ты уже играла сегодня!\n"
        f"Твой текущий размер: {data[uid]['size_mm']} мм"
    )