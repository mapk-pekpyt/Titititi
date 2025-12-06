# plugins/loto.py

import random
import json
import os

FILE = "/app/loto_data.json"

# -----------------------------------------
# Загрузка / сохранение
# -----------------------------------------

def load():
    if not os.path.exists(FILE):
        return {}
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


# -----------------------------------------
# ИНИЦИАЛИЗАЦИЯ ЧАТА
# -----------------------------------------

def ensure_chat(data, chat_id):
    if str(chat_id) not in data:
        data[str(chat_id)] = {
            "bank": 0,           # накопленные звезды
            "users": {},         # {user_id: donated}
        }
    return data


# -----------------------------------------
# ОБРАБОТКА УСПЕШНОЙ ОПЛАТЫ
# -----------------------------------------

def handle_successful(bot, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    amount = message.successful_payment.total_amount // 100  # stars

    data = load()
    data = ensure_chat(data, chat_id)

    # увеличить банк
    data[str(chat_id)]["bank"] += amount

    # добавить пользователя
    users = data[str(chat_id)]["users"]
    users[str(user_id)] = users.get(str(user_id), 0) + amount

    save(data)

    bot.send_message(chat_id, f"💫 Получено `{amount}` ⭐. Банк: {data[str(chat_id)]['bank']}/100 ⭐")

    # если набралось 100 — запускаем автоматический розыгрыш
    if data[str(chat_id)]["bank"] >= 100:
        send_gift(bot, chat_id, data)


# -----------------------------------------
# РОЗЫГРЫШ ПОДАРКА 50 STARS
# -----------------------------------------

def send_gift(bot, chat_id, data, forced=False):
    chat = data[str(chat_id)]
    users = chat["users"]

    if not users:
        return bot.send_message(chat_id, "❌ Нет участников.")

    # список [(user_id, сумма), ...]
    arr = list(users.items())

    # выбираем случайного
    winner_id, donated = random.choice(arr)

    bot.send_message(
        chat_id,
        f"🎁 Победитель: <a href='tg://user?id={winner_id}'>пользователь</a>\n"
        f"Он получает подарок 50 ⭐!",
        parse_mode="HTML"
    )

    # обнуляем банк
    chat["bank"] = 0
    chat["users"] = {}

    save(data)


# -----------------------------------------
# ОБРАБОТЧИК КОМАНД
# -----------------------------------------

def handle(bot, message):
    chat_id = message.chat.id
    text = message.text.lower()

    data = load()
    data = ensure_chat(data, chat_id)

    # команда /loto
    if text.startswith("/loto"):
        bank = data[str(chat_id)]["bank"]
        bot.reply_to(message, f"🎰 Лото банк: {bank}/100 ⭐")
        return

    # команда /gift — тестовая
    if text.startswith("/gift"):
        send_gift(bot, chat_id, data, forced=True)
        return