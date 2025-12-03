# plugins/top_plugin.py
import os
import json
from plugins.common import get_name, german_date

FILE = "data/users.json"
os.makedirs("data", exist_ok=True)


# ------------------------ БАЗОВЫЕ ФУНКЦИИ ------------------------

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
    chat = str(chat_id)
    uid = str(user.id)
    name = get_name(user)

    if chat not in data:
        data[chat] = {}

    if uid not in data[chat]:
        data[chat][uid] = {
            "name": name,
            "sisi": 0,
            "hui": 0,
            "klitor": 0,          # храним в мм
            "last_sisi": None,
            "last_hui": None,
            "last_klitor": None
        }
    else:
        # обновим имя при каждом вызове
        data[chat][uid]["name"] = name

    save(data)
    return data


def update_stat(chat_id, user, key, delta):
    data = load()
    chat = str(chat_id)
    uid = str(user.id)

    data[chat][uid][key] += delta
    save(data)


def update_date(chat_id, user, key):
    data = load()
    chat = str(chat_id)
    uid = str(user.id)

    data[chat][uid][key] = german_date().isoformat()
    save(data)


def was_today(chat_id, user, key):
    data = load()
    chat = str(chat_id)
    uid = str(user.id)

    today = german_date().isoformat()
    return data.get(chat, {}).get(uid, {}).get(key) == today


# ------------------------ ВСПОМОГАТЕЛЬНЫЕ ------------------------

def _format_klitor(mm: int):
    """Преобразуем мм → см с 1 знаком."""
    return f"{mm / 10:.1f}"


# ------------------------ ОСНОВНАЯ ЛОГИКА TOP ------------------------

def handle_top(bot, message):
    chat = str(message.chat.id)
    data = load()

    if chat not in data or len(data[chat]) == 0:
        return bot.reply_to(message, "Никто ещё не играл 😿")

    users = data[chat]

    # 1. Топ сисек
    sisi_list = sorted(
        users.values(),
        key=lambda x: x["sisi"],
        reverse=True
    )
    txt1 = "🏆 Топ сисечек:\n"
    for i, u in enumerate(sisi_list, 1):
        txt1 += f"{i}. {u['name']} — {u['sisi']} размера 🍒\n"

    # 2. Топ хуёв
    hui_list = sorted(
        users.values(),
        key=lambda x: x["hui"],
        reverse=True
    )
    txt2 = "🍌 Топ достоинств:\n"
    for i, u in enumerate(hui_list, 1):
        txt2 += f"{i}. {u['name']} — {u['hui']} см 🍌\n"

    # 3. Топ клиторов (в см)
    klit_list = sorted(
        users.values(),
        key=lambda x: x["klitor"],
        reverse=True
    )
    txt3 = "🍑 Топ клиторов:\n"
    for i, u in enumerate(klit_list, 1):
        txt3 += f"{i}. {u['name']} — {_format_klitor(u['klitor'])} см 🍑\n"

    bot.reply_to(message, txt1)
    bot.reply_to(message, txt2)
    bot.reply_to(message, txt3)


# ------------------------ /my ------------------------

def handle_my(bot, message):
    chat = str(message.chat.id)
    user = message.from_user
    uid = str(user.id)

    data = load()

    if chat not in data or uid not in data[chat]:
        return bot.reply_to(message, "Ты ещё не играл ничего 😿")

    u = data[chat][uid]

    txt = (
        f"📊 {u['name']}, твои размеры:\n\n"
        f"🍒 Сисечки: {u['sisi']} размера\n"
        f"🍌 Хуй: {u['hui']} см\n"
        f"🍑 Клитор: {_format_klitor(u['klitor'])} см"
    )

    bot.reply_to(message, txt)


# ------------------------ HANDLER ------------------------

def handle(bot, message):
    text = message.text.lower()

    if text.startswith("/top"):
        return handle_top(bot, message)

    if text.startswith("/my"):
        return handle_my(bot, message)