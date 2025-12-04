import os
import json
from telebot.types import LabeledPrice
from common import weighted_random, german_date, get_name

DATA_FILE = "data/sisi.json"
BOOST_PRICE_FILE = "data/boostprice.json"
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"


def load_price():
    try:
        with open(BOOST_PRICE_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f).get("price", 0))
    except:
        return 0


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def handle_successful(bot, message):
    payload = message.successful_payment.invoice_payload

    if not payload.startswith("sisi:"):
        return

    _, user_id_s = payload.split(":")
    uid = int(user_id_s)

    data = load_data()
    user = data.get(str(uid), {"size": 0, "date": "2000-01-01"})

    grow = weighted_random()
    user["size"] = max(0, user["size"] + grow)

    data[str(uid)] = user
    save_data(data)

    bot.send_message(message.chat.id, f"🔥 Твой буст сисек: +{grow} см! Теперь: {user['size']} см 🍒")


def handle(bot, message):
    text = message.text.lower()

    # daily
    if text.startswith("/sisi"):
        uid = message.from_user.id
        d = load_data()
        today = str(german_date())
        user = d.get(str(uid), {"size": 0, "date": "2000-01-01"})

        if user["date"] == today:
            bot.reply_to(message, f"⏳ Уже росло сегодня! Сейчас: {user['size']} см")
            return

        grow = weighted_random()
        user["size"] = max(0, user["size"] + grow)
        user["date"] = today

        d[str(uid)] = user
        save_data(d)

        bot.reply_to(message, f"🌸 Сегодня рост: +{grow} см\nТвои сиси: {user['size']} см")
        return

    # boost
    if text.startswith("/boosts"):
        price = load_price()
        uid = message.from_user.id

        if price <= 0:
            bot.reply_to(message, "Буст бесплатный. Просто жми /sisi")
            return

        bot.send_invoice(
            chat_id=message.chat.id,
            title="Boost Sisi",
            description="Увеличение размера сисек",
            invoice_payload=f"sisi:{uid}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=[LabeledPrice("Boost", price)]
        )