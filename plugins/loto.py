# plugins/loto.py
import os
import json
import random
from telebot.types import User

FILE = "data/loto.json"
os.makedirs("data", exist_ok=True)

# ------------------ ФУНКЦИИ ДЛЯ ХРАНЕНИЯ ------------------

def load():
    if not os.path.exists(FILE):
        return {}
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ------------------ ДОБАВЛЕНИЕ ЗВЁЗД В БАНК ------------------

def handle_payment(bot, message, stars):
    data = load()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)

    if chat_id not in data:
        data[chat_id] = {
            "total": 0,     # накопленные звёзды
            "users": {},    # донатившие пользователи
            "lotoprice": 100  # дефолтная цель
        }

    data[chat_id]["total"] += stars
    data[chat_id]["users"].setdefault(user_id, 0)
    data[chat_id]["users"][user_id] += stars

    save(data)

# ------------------ КОМАНДЫ ------------------

def handle(bot, message):
    text = (message.text or "").strip()
    if not text:
        return

    cmd_raw = text.split()[0].lower()
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw
    chat_id = str(message.chat.id)

    data = load()
    if chat_id not in data:
        data[chat_id] = {"total":0, "users":{}, "lotoprice": 100}

    # ------------------ /lotoprice ------------------
    if cmd == "/lotoprice":
        if message.from_user.id not in get_chat_admin_ids(bot, message.chat.id):
            bot.reply_to(message, "⛔ Только админы могут менять цену лото.")
            return

        parts = text.split()
        if len(parts) < 2:
            bot.reply_to(message, f"💰 Текущий лото-прайс: {data[chat_id]['lotoprice']} ⭐")
            return

        try:
            new_price = int(parts[1])
            data[chat_id]["lotoprice"] = new_price
            save(data)
            bot.reply_to(message, f"✅ Лото-прайс обновлён: {new_price} ⭐")
        except:
            bot.reply_to(message, "❗ Используй: /lotoprice 150")
        return

    # ------------------ /loto ------------------
    if cmd == "/loto":
        total = data[chat_id]["total"]
        price = data[chat_id]["lotoprice"]

        if total < price:
            bot.reply_to(message, f"🕐 Ещё не набрано {price} ⭐, собрано {total} ⭐")
            return

        # выбираем победителя
        users = list(data[chat_id]["users"].items())
        total_stars = sum(s for _, s in users)

        winner_id, _ = random.choice(users)
        winner_name = get_user_name(bot, chat_id, int(winner_id))

        reward = total_stars // 2  # 50% отдаём победителю
        bot.send_message(message.chat.id, f"🎉 Поздравляем {winner_name}! Ты выиграл {reward} ⭐!")

        # остаток остаётся в боте, чистим накопления
        data[chat_id]["total"] = 0
        data[chat_id]["users"] = {}
        save(data)
        return

# ------------------ ВСПОМОГАТЕЛЬНЫЕ ------------------

def get_chat_admin_ids(bot, chat_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return [a.user.id for a in admins]
    except:
        return []

def get_user_name(bot, chat_id, user_id):
    try:
        return bot.get_chat_member(chat_id, user_id).user.first_name
    except:
        return "Пользователь"