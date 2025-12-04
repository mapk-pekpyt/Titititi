import os
import json
from telebot.types import LabeledPrice
from common import weighted_random, german_date, get_name

DATA_FILE = "data/klitor.json"
BOOST_PRICE_FILE = "data/boostprice.json"
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"


def load_price():
    try:
        with open(BOOST_PRICE_FILE, "r") as f:
            return int(json.load(f).get("price", 0))
    except:
        return 0


def mm_to_cm(mm):
    return round(mm / 10, 1)


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)


def handle_successful(bot, message):
    payload = message.successful_payment.invoice_payload
    if not payload.startswith("klitor:"):
        return

    _, uid_s = payload.split(":")
    uid = int(uid_s)

    data = load_data()
    user = data.get(str(uid), {"mm": 0, "date": "2000-01-01"})

    grow = weighted_random()
    user["mm"] = max(0, user["mm"] + grow)

    data[str(uid)] = user
    save_data(data)

    bot.send_message(
        message.chat.id,
        f"💦 Буст клитора: +{grow} мм → {mm_to_cm(user['mm'])} см"
    )


def handle(bot, message):
    text = message.text.lower()

    if text.startswith("/klitor"):
        uid = message.from_user.id
        d = load_data()
        today = str(german_date())
        user = d.get(str(uid), {"mm": 0, "date": "2000-01-01"})

        if user["date"] == today:
            bot.reply_to(message, f"⏳ Уже рос сегодня! Сейчас: {mm_to_cm(user['mm'])} см")
            return

        grow = weighted_random()
        user["mm"] = max(0, user["mm"] + grow)
        user["date"] = today

        d[str(uid)] = user
        save_data(d)

        bot.reply_to(message, f"📈 Рост клитора +{grow} мм → {mm_to_cm(user['mm'])} см")
        return

    if text.startswith("/boostk"):
        price = load_price()
        uid = message.from_user.id

        if price <= 0:
            bot.reply_to(message, "Буст бесплатный. Жми /klitor")
            return

        bot.send_invoice(
            chat_id=message.chat.id,
            title="Boost Klitor",
            description="Увеличение размера клитора",
            invoice_payload=f"klitor:{uid}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=[LabeledPrice("Boost", price)]
        )