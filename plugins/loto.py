import json
import os
import random
from telebot.types import LabeledPrice, Invoice

DATA_FILE = "loto_data.json"

def load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Инициализация данных чата
def ensure_chat(data, chat_id):
    chat_id = str(chat_id)
    if chat_id not in data:
        data[chat_id] = {
            "bank": 0,            # накопленные звезды
            "users": {},          # user_id: звезды
        }
    return data


# ===================================================================
# 🎁 ВЫДАЧА ПОДАРКА
# ===================================================================
def send_gift(bot, chat_id, data, forced=False):
    chat_id = str(chat_id)

    if len(data[chat_id]["users"]) == 0:
        bot.send_message(chat_id, "⚠ Некому выдавать подарок — нет донатеров.")
        return

    # Выбираем случайного среди донатеров
    users = list(data[chat_id]["users"].keys())
    winner = random.choice(users)

    bot.send_message(
        chat_id,
        f"🎉 Победитель розыгрыша: <a href='tg://user?id={winner}'>этот человек</a>!\n"
        f"🎁 Ему отправлен подарок 50 ⭐",
        parse_mode="HTML"
    )

    # Отправляем GIFT
    try:
        bot.send_invoice(
            winner,
            title="🎁 Подарок от бота",
            description="50 Stars Gift",
            provider_token="",        # ПУСТО — для Telegram Stars
            currency="XTR",
            prices=[LabeledPrice("Gift", 0)],
            start_parameter="gift",
            payload="gift_50_stars"
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при отправке подарка: {e}")

    # Сбросить банк и донатеров
    data[chat_id]["bank"] = 0
    data[chat_id]["users"] = {}
    save(data)


# ===================================================================
# 💳 УСПЕШНАЯ ОПЛАТА
# ===================================================================
def handle_successful(bot, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    raw = message.successful_payment.total_amount  # например 100
    amount = int(raw / 100)                       # 100 → 1 ⭐

    data = load()
    data = ensure_chat(data, chat_id)

    # увеличить банк
    data[str(chat_id)]["bank"] += amount

    # добавить пользователя
    users = data[str(chat_id)]["users"]
    users[str(user_id)] = users.get(str(user_id), 0) + amount

    save(data)

    bot.send_message(
        chat_id,
        f"💫 Получено {amount} ⭐. Банк: {data[str(chat_id)]['bank']}/100 ⭐"
    )

    # Авто-розыгрыш
    if data[str(chat_id)]["bank"] >= 100:
        send_gift(bot, chat_id, data)


# ===================================================================
# 💬 КОМАНДЫ
# ===================================================================
def handle(bot, message):
    chat_id = message.chat.id
    text = message.text.strip().lower()

    data = load()
    data = ensure_chat(data, chat_id)
    chat = data[str(chat_id)]

    # ---------------------------------------------
    # /loto — показываем текущий банк
    # ---------------------------------------------
    if text.startswith("/loto"):
        bank = chat["bank"]
        bot.reply_to(message, f"🎯 Банк: {bank}/100 ⭐")
        return

    # ---------------------------------------------
    # /gift — принудительно подарить 50⭐
    # ---------------------------------------------
    if text.startswith("/gift"):
        send_gift(bot, chat_id, data, forced=True)
        return