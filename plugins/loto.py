import os
import json
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

FILE = "/app/data/loto.json"

# ---------------------------------------------------
#   СИСТЕМА ЧТЕНИЯ/СОЗДАНИЯ БАЗЫ
# ---------------------------------------------------

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
        data[chat_id]["lotoprice"] = 100  # стандарт

    save(data)
    return data


# ---------------------------------------------------
#  ОБРАБОТЧИК УСПЕШНЫХ ОПЛАТ (все покупки)
# ---------------------------------------------------

def handle_successful(bot, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    amount = message.successful_payment.total_amount // 100  # stars

    data = ensure_chat(chat_id)
    chat = str(chat_id)

    data[chat]["bank"] += amount

    if str(user_id) not in data[chat]["users"]:
        data[chat]["users"][str(user_id)] = 0

    data[chat]["users"][str(user_id)] += amount

    save(data)

    bot.send_message(
        user_id,
        f"💫 Получено `{amount}` ⭐.\n"
        f"Банк: {data[chat]['bank']}/{data[chat]['lotoprice']} ⭐."
    )

    check_loto(bot, chat_id)



# ---------------------------------------------------
# СЧЁТЧИК ДЛЯ КОМАНД /boosts и /mute
# ---------------------------------------------------

def register_manual_payment(bot, chat_id, user_id, stars):
    data = ensure_chat(chat_id)
    chat = str(chat_id)

    data[chat]["bank"] += stars

    if str(user_id) not in data[chat]["users"]:
        data[chat]["users"][str(user_id)] = 0

    data[chat]["users"][str(user_id)] += stars

    save(data)

    check_loto(bot, chat_id)


# ---------------------------------------------------
#   ПРОВЕРКА РОЗЫГРЫША
# ---------------------------------------------------

def check_loto(bot, chat_id):
    data = ensure_chat(chat_id)
    chat = str(chat_id)

    bank = data[chat]["bank"]
    price = data[chat]["lotoprice"]
    users = data[chat]["users"]

    if bank < price:
        return

    if not users:
        return

    winner = random.choice(list(users.keys()))
    winner = int(winner)

    # отправка подарка
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎁 Забрать подарок (50⭐)", callback_data="gift50"))

    bot.send_message(chat_id, f"🎉 ЛОТО! Победитель — <a href='tg://user?id={winner}'>ты</a>!", parse_mode="HTML")
    bot.send_message(winner, "🎁 Ты выиграл 50⭐ подарком!", reply_markup=kb)

    # сброс банка
    data[chat]["bank"] = 0
    save(data)



# ---------------------------------------------------
#   КНОПКА ПОДАРКА 50⭐
# ---------------------------------------------------

def init(bot):
    @bot.callback_query_handler(func=lambda c: c.data == "gift50")
    def gift_press(c):
        bot.answer_callback_query(c.id, "Подарок отправлен!")



# ---------------------------------------------------
#   КОМАНДЫ
# ---------------------------------------------------

def handle(bot, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.split()

    data = ensure_chat(chat_id)
    chat = str(chat_id)

    # /lotoprice X
    if text[0] == "/lotoprice":
        if len(text) == 2 and text[1].isdigit():
            data[chat]["lotoprice"] = int(text[1])
            save(data)
            bot.reply_to(message, f"Цена лото установлена: {text[1]} ⭐")
        else:
            bot.reply_to(message, "Используй: /lotoprice 100")
        return

    # /loto – показать состояние
    if text[0] == "/loto":
        bot.reply_to(
            message,
            f"🎰 Лото:\n"
            f"Банк: {data[chat]['bank']}/{data[chat]['lotoprice']} ⭐\n"
            f"Участников: {len(data[chat]['users'])}"
        )
        return

    # /gift — принудительный тестовый подарок
    if text[0] == "/gift":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎁 Забрать подарок (50⭐)", callback_data="gift50"))
        bot.send_message(chat_id, "ТЕСТОВЫЙ ПОДАРОК", reply_markup=kb)
        return


# ---------------------------------------------------
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ MUT/BOOST
# ---------------------------------------------------

def add_stars(bot, chat_id, user_id, stars):
    register_manual_payment(bot, chat_id, user_id, stars)