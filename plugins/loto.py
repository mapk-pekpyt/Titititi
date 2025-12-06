import json
import os
import random
from telebot.types import Message

DATA_FILE = "loto_data.json"
MIN_GIFT = 50  # размер подарка в звёздах

# --- загрузка и сохранение данных ---
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --- добавление звёзд в банк ---
def add_stars(chat_id, user_id, stars):
    data = load_data()
    chat_id = str(chat_id)
    if chat_id not in data:
        data[chat_id] = {"bank": 0, "users": {}, "lotoprice": 100}

    if "users" not in data[chat_id]:
        data[chat_id]["users"] = {}
    if user_id not in data[chat_id]["users"]:
        data[chat_id]["users"][user_id] = 0

    data[chat_id]["users"][user_id] += stars
    data[chat_id]["bank"] += stars
    save_data(data)

# --- проверка лото ---
def check_loto(bot, chat_id):
    data = load_data()
    chat_id = str(chat_id)
    if chat_id not in data:
        return
    bank = data[chat_id].get("bank", 0)
    price = data[chat_id].get("lotoprice", 100)
    if bank >= price:
        users = [uid for uid, stars in data[chat_id]["users"].items() if stars > 0]
        if not users:
            return
        winner = random.choice(users)
        # 🟢 дарим 50 Stars Gift
        try:
            bot.send_message(winner, f"🎁 Поздравляем! Вы получили Stars Gift на {MIN_GIFT}⭐")
        except:
            pass
        # снимаем 50 звезд с баланса бота (условно)
        # уменьшаем банк на 50
        data[chat_id]["bank"] -= MIN_GIFT
        # обнуляем участников
        data[chat_id]["users"] = {}
        save_data(data)

# --- установка лотопрайса ---
def set_price(chat_id, price):
    data = load_data()
    chat_id = str(chat_id)
    if chat_id not in data:
        data[chat_id] = {"bank": 0, "users": {}, "lotoprice": price}
    else:
        data[chat_id]["lotoprice"] = price
    save_data(data)

# --- обработка команд ---
def handle(bot, message: Message):
    data = load_data()
    chat_id = str(message.chat.id)
    text = message.text.lower()

    if chat_id not in data:
        data[chat_id] = {"bank": 0, "users": {}, "lotoprice": 100}

    # /lotoprice X
    if text.startswith("/lotoprice"):
        try:
            price = int(text.split()[1])
            set_price(chat_id, price)
            bot.reply_to(message, f"💰 Лотопрайс установлен: {price}⭐")
        except:
            bot.reply_to(message, f"❌ Используйте: /lotoprice 100")

    # /loto
    elif text.startswith("/loto"):
        bank = data[chat_id].get("bank", 0)
        price = data[chat_id].get("lotoprice", 100)
        users = len(data[chat_id].get("users", {}))
        bot.reply_to(message, f"🎰 Лото:\nБанк: {bank}/{price} ⭐\nУчастников: {users}")
        save_data(data)

    # /gift - тестовая команда для тебя
    elif text.startswith("/gift"):
        users = list(data[chat_id].get("users", {}).keys())
        if not users:
            bot.reply_to(message, "❌ Нет участников для подарка.")
            return
        winner = random.choice(users)
        try:
            bot.send_message(winner, f"🎁 Вы получили Stars Gift на {MIN_GIFT}⭐ (тестовая команда)")
            bot.reply_to(message, f"✅ Подарок отправлен пользователю {winner}")
            # снимаем 50⭐ с банка бота
            data[chat_id]["bank"] = max(0, data[chat_id]["bank"] - MIN_GIFT)
            save_data(data)
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка при отправке подарка: {e}")