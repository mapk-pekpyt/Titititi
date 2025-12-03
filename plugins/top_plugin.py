import json
import os
from plugins.common import get_name

FILE = "top_data.json"


def load():
    if not os.path.exists(FILE):
        return {}
    try:
        with open(FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return {}


def save(data):
    with open(FILE, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_user(chat_id, user):
    data = load()
    chat_id = str(chat_id)
    uid = str(user.id)

    if chat_id not in data:
        data[chat_id] = {}

    if uid not in data[chat_id]:
        data[chat_id][uid] = {
            "name": get_name(user),
            "sisi": 0,
            "hui": 0,
            "klitor": 0.0,
            "last_sisi": None,
            "last_hui": None,
            "last_klitor": None
        }

    data[chat_id][uid]["name"] = get_name(user)

    save(data)
    return data


def update_stat(chat_id, user, field, value):
    data = load()
    chat_id = str(chat_id)
    uid = str(user.id)

    data[chat_id][uid][field] += value
    save(data)


def update_date(chat_id, user, field):
    data = load()
    chat_id = str(chat_id)
    uid = str(user.id)

    data[chat_id][uid][field] = str(__import__("datetime").date.today())
    save(data)


def was_today(chat_id, user, field):
    data = load()
    chat_id = str(chat_id)
    uid = str(user.id)

    last = data[chat_id][uid][field]
    if last is None:
        return False

    from datetime import date
    return last == str(date.today())


def top_for(chat_id, field, title, unit):
    data = load()
    chat_id = str(chat_id)

    if chat_id not in data or not data[chat_id]:
        return "Тут ещё никто не играл 😢"

    users = list(data[chat_id].values())
    users.sort(key=lambda u: u[field], reverse=True)

    msg = f"🏆 *Топ по {title}:*\n\n"

    for i, u in enumerate(users, start=1):
        msg += f"{i}. *{u['name']}* — {u[field]}{unit}\n"

    return msg


def handle_top_sisi(bot, message):
    chat_id = message.chat.id
    bot.reply_to(message, top_for(chat_id, "sisi", "сисечкам", " размера"), parse_mode="Markdown")


def handle_top_hui(bot, message):
    chat_id = message.chat.id
    bot.reply_to(message, top_for(chat_id, "hui", "хуям", " см"), parse_mode="Markdown")


def handle_top_klitor(bot, message):
    chat_id = message.chat.id

    data = load()
    cid = str(chat_id)

    if cid not in data:
        return bot.reply_to(message, "Тут ещё никто не играл 😢")

    # пересчёт мм → см
    top_list = []
    for u in data[cid].values():
        top_list.append((u["name"], u["klitor"] / 10))

    top_list.sort(key=lambda x: x[1], reverse=True)

    msg = "🏆 *Топ по клиторам:*\n\n"
    for i, (name, size) in enumerate(top_list, start=1):
        msg += f"{i}. *{name}* — {size:.1f} см\n"

    bot.reply_to(message, msg, parse_mode="Markdown")