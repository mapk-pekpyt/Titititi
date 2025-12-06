# plugins/loto.py
import os
import json
import random
from telebot.types import Message

DATA_FILE = "plugins/loto_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_payment(chat_id, user_id, stars):
    data = load_data()
    chat_s = str(chat_id)
    if chat_s not in data:
        data[chat_s] = {"bank": 0, "users": {}}

    data[chat_s]["bank"] += stars
    if str(user_id) not in data[chat_s]["users"]:
        data[chat_s]["users"][str(user_id)] = 0
    data[chat_s]["users"][str(user_id)] += stars

    save_data(data)
    return data[chat_s]["bank"]

def send_gift(bot, chat_id, forced=False):
    data = load_data()
    chat_s = str(chat_id)
    if chat_s not in data:
        return

    bank = data[chat_s]["bank"]
    if bank < 100 and not forced:
        return

    users = list(data[chat_s]["users"].keys())
    if not users:
        return

    winner_id = int(random.choice(users))
    data[chat_s]["bank"] -= 50
    save_data(data)

    bot.send_message(
        winner_id,
        "🎁 Поздравляем! Ты получил **50 Stars Gift** от бота! ⭐"
    )
    bot.send_message(
        chat_id,
        f"🎉 В чате {chat_id} подарок 50⭐ отправлен случайному донатеру!"
    )

def handle(bot, message: Message):
    text = (message.text or "").strip().lower()
    chat_id = message.chat.id
    user_id = message.from_user.id

    data = load_data()
    chat_s = str(chat_id)

    if chat_s not in data:
        data[chat_s] = {"bank": 0, "users": {}}
        save_data(data)

    # команда /loto — показать банк и участников текущего чата
    if text.startswith("/loto"):
        bank = data[chat_s]["bank"]
        users_count = len(data[chat_s]["users"])
        bot.reply_to(
            message,
            f"🎰 Лото:\nБанк: {bank}/100 ⭐\nУчастников: {users_count}"
        )
        return

    # команда /gift — тестовая отправка 50⭐ подарка в этом чате
    if text.startswith("/gift"):
        send_gift(bot, chat_id, forced=True)
        bot.reply_to(message, "✅ Тестовый подарок 50⭐ отправлен!")
        return

def handle_successful(bot, message):
    if not hasattr(message, "successful_payment") or not message.successful_payment:
        return

    stars = getattr(message.successful_payment, "total_amount", 0)
    stars = max(int(stars / 100), 1)

    chat_id = message.chat.id
    user_id = message.from_user.id

    bank = add_payment(chat_id, user_id, stars)

    # сообщение в чат, где была оплата
    bot.send_message(
        chat_id,
        f"💫 Получено `{stars}` ⭐. Банк: {bank}/100 ⭐"
    )

    # проверка для розыгрыша в этом чате
    if bank >= 100:
        send_gift(bot, chat_id)