import json, os
from .common import german_time, weighted_random, get_name

TRIGGER = "/hui"
FILE = "data/hui.json"

def load():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def handle(bot, message):
    text = message.text.split("@")[0]  # отрезаем @BotName
if text != TRIGGER:
    return

    user = message.from_user
    uid = str(user.id)
    name = get_name(user)

    today = german_time().strftime("%Y-%m-%d")
    data = load()

    if uid not in data:
        data[uid] = {"size": 0, "last": "2000-01-01", "name": name}

    if data[uid]["last"] != today:
        delta = weighted_random()
        if data[uid]["size"] + delta < 0:
            delta = -data[uid]["size"]

        data[uid]["size"] += delta
        data[uid]["last"] = today
        data[uid]["name"] = name
        save(data)

        bot.reply_to(message,
            f"{name} 🍆\n"
            f"Твой хуй изменился на {delta} см\n"
            f"Теперь размер: {data[uid]['size']} см"
        )
        return

    bot.reply_to(message,
        f"{name} 🍆 ты уже играл сегодня!\n"
        f"Твой текущий размер: {data[uid]['size']} см"
    )