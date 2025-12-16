import os
import json
import threading
import datetime
from plugins.common import get_name, german_date
from plugins import beer

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
            "beer": 0,            # алкаш
            "last_sisi": None,
            "last_hui": None,
            "last_klitor": None,
            "last_beer": None
        }
    else:
        data[chat][uid]["name"] = name

    save(data)
    return data


def update_stat(chat_id, user, key, delta):
    data = load()
    chat = str(chat_id)
    uid = str(user.id)

    if chat not in data:
        data[chat] = {}
    if uid not in data[chat]:
        data[chat][uid] = {"name": get_name(user), key: 0}

    data[chat][uid][key] = data[chat][uid].get(key, 0) + delta
    save(data)


def update_date(chat_id, user, key):
    data = load()
    chat = str(chat_id)
    uid = str(user.id)

    if chat not in data:
        data[chat] = {}
    if uid not in data[chat]:
        data[chat][uid] = {"name": get_name(user), key: None}

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
    return f"{mm / 10:.1f}"


# ------------------------ ТОП ------------------------

def handle_top(bot, message):
    chat = str(message.chat.id)
    data = load()
    if chat not in data or len(data[chat]) == 0:
        return bot.reply_to(message, "Никто ещё не играл 😿")

    users = data[chat]

    # 1. Топ сисек
    sisi_list = sorted(users.values(), key=lambda x: x.get("sisi", 0), reverse=True)
    txt1 = "🏆 Топ сисечек:\n"
    for i, u in enumerate(sisi_list[:3], 1):
        txt1 += f"{i}. {u['name']} — {u['sisi']} размер 🍒\n"

    # 2. Топ хуёв
    hui_list = sorted(users.values(), key=lambda x: x.get("hui", 0), reverse=True)
    txt2 = "🍌 Топ достоинств:\n"
    for i, u in enumerate(hui_list[:3], 1):
        txt2 += f"{i}. {u['name']} — {u['hui']} см 🍌\n"

    # 3. Топ клиторов
    klit_list = sorted(users.values(), key=lambda x: x.get("klitor", 0), reverse=True)
    txt3 = "🍑 Топ клиторов:\n"
    for i, u in enumerate(klit_list[:3], 1):
        txt3 += f"{i}. {u['name']} — {_format_klitor(u['klitor'])} см 🍑\n"

    # 4. Топ алкашей (пиво)
    beer_list = sorted(users.values(), key=lambda x: x.get("beer", 0), reverse=True)
    txt4 = "🍺 Топ алкашей:\n"
    for i, u in enumerate(beer_list[:3], 1):
        txt4 += f"{i}. {u['name']} — {u.get('beer',0)} л 🍺\n"

    # Отправка сообщений
    bot.reply_to(message, txt1)
    bot.reply_to(message, txt2)
    bot.reply_to(message, txt3)
    bot.reply_to(message, txt4)


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
        f"🍒 Сисечки: {u.get('sisi',0)} размера\n"
        f"🍌 Хуй: {u.get('hui',0)} см\n"
        f"🍑 Клитор: {_format_klitor(u.get('klitor',0))} см\n"
        f"🍺 Выпито пива: {u.get('beer',0)} мл"
    )

    bot.reply_to(message, txt)


def handle(bot, message):
    text = (message.text or "").lower()

    if text.startswith("/top") or text.startswith("топ") or text.startswith("рейтинг"):
        return handle_top(bot, message)

    if text.startswith("/my") or text.startswith("мои размеры") or text.startswith("мои"):
        return handle_my(bot, message)


# ------------------------ ЕЖЕВЕЧЕРНИЙ ТОП ------------------------

def schedule_daily_top(bot, chat_id):
    def job():
        now = datetime.datetime.now()
        # если текущее время >= 21:00 и < 21:05, отправляем
        if now.hour == 21 and now.minute == 0:
            class Msg:
                chat = type("Chat", (), {"id": chat_id})()
            handle_top(bot, Msg())

        # повторить через 60 секунд
        threading.Timer(60, job).start()

    job()


# ------------------------ Триггеры ------------------------

TRIGGERS = {
    "/top": "top_plugin",
    "/top@sisititibot": "top_plugin",
    "топ": "top_plugin",
    "рейтинг": "top_plugin",
    "/my": "top_plugin",
    "мои размеры": "top_plugin",
    "мои": "top_plugin",
}