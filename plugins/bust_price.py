# plugins/bust_price.py
import os
import json

FILE = "data/boostprice.json"
os.makedirs("data", exist_ok=True)

ADMIN_ID = 5791171535


def load_boost_price():
    if not os.path.exists(FILE):
        return 0
    try:
        with open(FILE, "r", encoding="utf8") as f:
            return json.load(f).get("price", 0)
    except:
        return 0


def save_boost_price(v: int):
    with open(FILE, "w", encoding="utf8") as f:
        json.dump({"price": v}, f, ensure_ascii=False, indent=2)


def handle(bot, message):
    text = (message.text or "").strip().lower()

    if not text.startswith("/boostprice"):
        return  # НЕ наша команда — выходим

    parts = text.split()

    # показать цену
    if len(parts) == 1:
        return bot.reply_to(
            message,
            f"💫 Текущая цена буста: {load_boost_price()} ⭐"
        )

    # менять цену может только админ
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только админ может менять цену буста.")

    # изменить цену
    try:
        value = int(parts[1])
        save_boost_price(value)
        return bot.reply_to(message, f"✅ Цена буста обновлена: {value} ⭐")
    except:
        return bot.reply_to(message, "❗ Использование: /boostprice 5")