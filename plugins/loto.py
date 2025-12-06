import os
import json
import random

FILE = "/app/data/loto.json"

# -------------------------------
# Работа с файлом
# -------------------------------
def load():
    if not os.path.exists(FILE):
        return {}
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_chat(chat_id):
    chat_id = str(chat_id)
    data = load()

    if chat_id not in data:
        data[chat_id] = {}

    if "bank" not in data[chat_id]:
        data[chat_id]["bank"] = 0

    if "users" not in data[chat_id] or not isinstance(data[chat_id]["users"], dict):
        data[chat_id]["users"] = {}

    if "lotoprice" not in data[chat_id]:
        data[chat_id]["lotoprice"] = 100  # стандартная цена лото

    save(data)
    return data

# -------------------------------
# Добавление звезд в банк
# -------------------------------
def add_stars(chat_id, user_id, stars):
    data = ensure_chat(chat_id)
    chat = str(chat_id)

    data[chat]["bank"] += stars
    if str(user_id) not in data[chat]["users"]:
        data[chat]["users"][str(user_id)] = 0
    data[chat]["users"][str(user_id)] += stars

    save(data)
    return data[chat]["bank"], data[chat]["lotoprice"]

# -------------------------------
# Проверка лото
# -------------------------------
def check_loto(bot, chat_id):
    data = ensure_chat(chat_id)
    chat = str(chat_id)
    bank = data[chat]["bank"]
    lotoprice = data[chat]["lotoprice"]

    if bank >= lotoprice and data[chat]["users"]:
        winner_id = int(random.choice(list(data[chat]["users"].keys())))
        send_gift(bot, winner_id, 50)
        bot.send_message(chat_id, f"🎉 Лото! Победитель — <a href='tg://user?id={winner_id}'>твой счастливчик</a>! Получает 50⭐", parse_mode="HTML")
        data[chat]["bank"] = 0
        data[chat]["users"] = {}
        save(data)

# -------------------------------
# Отправка подарка
# -------------------------------
def send_gift(bot, user_id, amount):
    bot.send_message(user_id, f"🎁 Ты получил {amount}⭐ подарком!")

# -------------------------------
# Команды
# -------------------------------
def handle(bot, message):
    chat_id = message.chat.id
    chat = str(chat_id)
    data = ensure_chat(chat_id)
    text = message.text.split()

    if text[0] == "/lotoprice":
        if len(text) == 2 and text[1].isdigit():
            data[chat]["lotoprice"] = int(text[1])
            save(data)
            bot.reply_to(message, f"Цена лото установлена: {text[1]} ⭐")
        else:
            bot.reply_to(message, "Используй: /lotoprice 100")
        return

    if text[0] == "/loto":
        bot.reply_to(message, f"🎰 Лото:\nБанк: {data[chat]['bank']}/{data[chat]['lotoprice']} ⭐\nУчастников: {len(data[chat]['users'])}")
        return

    if text[0] == "/gift":
        # тестовая кнопка подарка
        kb = None
        winner_id = message.from_user.id
        send_gift(bot, winner_id, 50)
        bot.reply_to(message, f"🎁 Тестовый подарок 50⭐ отправлен тебе!")
        return