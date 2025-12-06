# plugins/loto.py
import os
import json
import random
from telebot.types import Message

DATA_FILE = "plugins/loto_data.json"

# загрузка данных
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# сохранение данных
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# добавить оплату в банк
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

# отправка подарка 50⭐ рандомному донатеру
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
    # списываем 50 звезд из банка (реально)
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

# обработка сообщений
def handle(bot, message: Message):
    text = (message.text or "").strip().lower()
    chat_id = message.chat.id
    user_id = message.from_user.id
    data = load_data()
    chat_s = str(chat_id)

    if chat_s not in data:
        data[chat_s] = {"bank": 0, "users": {}}
        save_data(data)

    # команда /loto — показать банк
    if text.startswith("/loto"):
        bank = data[chat_s]["bank"]
        users_count = len(data[chat_s]["users"])
        bot.reply_to(
            message,
            f"🎰 Лото:\nБанк: {bank}/100 ⭐\nУчастников: {users_count}"
        )
        return

    # команда /gift — тестовая отправка 50⭐ подарка
    if text.startswith("/gift"):
        send_gift(bot, chat_id, forced=True)
        bot.reply_to(message, "✅ Тестовый подарок 50⭐ отправлен!")
        return

# вызывается из main при успешной оплате
def handle_successful(bot, message):
    if not hasattr(message, "successful_payment") or not message.successful_payment:
        return

    # количество звезд — берем сумму из успешной оплаты
    stars = getattr(message.successful_payment, "total_amount", 0)
    # у XTR суммы обычно в копейках (целое число), делим на 100 для звезд
    stars = max(int(stars / 100), 1)

    chat_id = message.chat.id
    user_id = message.from_user.id

    bank = add_payment(chat_id, user_id, stars)

    bot.send_message(
        chat_id,
        f"💫 Получено `{stars}` ⭐. Банк: {bank}/100 ⭐"
    )

    # проверка — если банк >= 100, автоматически дарим подарок
    if bank >= 100:
        send_gift(bot, chat_id)