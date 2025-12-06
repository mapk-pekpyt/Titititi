# plugins/loto.py
import os
import json
import random
from telebot.types import LabeledPrice

PROVIDER_TOKEN = os.environ.get("PROVIDER_TOKEN")  # токен для платежей Telegram
DATA_FILE = "loto_data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def ensure_chat(data, chat_id):
    chat_id = str(chat_id)
    if chat_id not in data:
        data[chat_id] = {
            "bank": 0,
            "lotoprice": 100,
            "participants": []
        }
    return data[chat_id]

def add_payment(chat_id, user_id, amount):
    data = load_data()
    chat_data = ensure_chat(data, chat_id)
    chat_data["bank"] += amount
    if user_id not in chat_data["participants"]:
        chat_data["participants"].append(user_id)
    save_data(data)
    return chat_data["bank"]

def send_gift(bot, chat_id, forced=False):
    data = load_data()
    chat_data = ensure_chat(data, chat_id)

    if chat_data["bank"] < 100 and not forced:
        return None

    if not chat_data["participants"]:
        return None

    winner_id = random.choice(chat_data["participants"])

    try:
        price = [LabeledPrice(label="Stars Gift 50", amount=50)]
        bot.send_invoice(
            chat_id=winner_id,
            title="🎁 Stars Gift",
            description="Поздравляем! Вы получаете 50 ⭐",
            payload=f"gift:{chat_id}:{winner_id}:50",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=price
        )
    except Exception as e:
        print("Ошибка при отправке подарка:", e)
        return None

    # списываем 50⭐ с банка
    chat_data["bank"] -= 50
    if chat_data["bank"] < 0:
        chat_data["bank"] = 0

    chat_data["participants"] = []
    save_data(data)
    return winner_id

def handle(bot, message):
    data = load_data()
    chat_id = message.chat.id
    chat_data = ensure_chat(data, chat_id)
    text = (message.text or "").strip().lower()

    # установить лотопрайс (только админы)
    if text.startswith("/lotoprice"):
        parts = text.split()
        if len(parts) >= 2:
            try:
                value = int(parts[1])
                chat_data["lotoprice"] = value
                save_data(data)
                bot.reply_to(message, f"✅ Лото-прайс установлен: {value} ⭐")
            except:
                bot.reply_to(message, "❌ Неверное число")
        else:
            bot.reply_to(message, f"💰 Текущий лото-прайс: {chat_data['lotoprice']} ⭐")
        return

    # показать статус лото
    if text.startswith("/loto"):
        bot.reply_to(
            message,
            f"🎰 Лото:\nБанк: {chat_data['bank']}/{chat_data['lotoprice']} ⭐\n"
            f"Участников: {len(chat_data['participants'])}"
        )
        return

    # вручить подарок вручную (только для тебя)
    if text.startswith("/gift"):
        winner = send_gift(bot, chat_id, forced=True)
        if winner:
            bot.reply_to(message, f"🎁 Подарок отправлен пользователю {winner}")
        else:
            bot.reply_to(message, "❌ Нет участников или недостаточно средств")
        return

def handle_successful(bot, message):
    if not hasattr(message, "successful_payment") or not message.successful_payment:
        return

    payload = getattr(message.successful_payment, "invoice_payload", "") or \
              getattr(message.successful_payment, "payload", "")

    # проверяем платеж для лото
    if payload.startswith("gift:"):
        # это ручной подарок, обработка не нужна здесь
        return

    # если payload начинается с boost:xxx — значит это был буст
    if payload.startswith("boost:"):
        parts = payload.split(":")
        if len(parts) != 5:
            return
        _, chat_s, payer_s, stat, n_s = parts
        try:
            chat_id = int(chat_s)
            payer_id = int(payer_s)
            amount = int(n_s)
        except:
            return

        add_payment(chat_id, payer_id, amount)
        chat_data = ensure_chat(load_data(), chat_id)
        if chat_data["bank"] >= chat_data["lotoprice"]:
            send_gift(bot, chat_id)