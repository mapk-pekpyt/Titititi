# plugins/bust_price.py
import os
import json

DATA_FILE = "data/boostprice.json"
ADMIN_ID = 5791171535  # твой id — при необходимости поменяй

os.makedirs("data", exist_ok=True)

def load_price():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f).get("price", 0))
    except:
        return 0

def save_price(v: int):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"price": int(v)}, f)
        return True
    except:
        return False

def handle(bot, message):
    text = (message.text or "").strip()
    if not text:
        return
    cmd_raw = text.split()[0].lower()
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw

    if cmd != "/boostprice":
        return

    parts = text.split()
    if len(parts) == 1:
        p = load_price()
        bot.reply_to(message, f"💰 Текущая цена буста: {p} ⭐")
        return

    # change price: only admin
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Только админ может менять цену.")
        return

    try:
        newp = int(parts[1])
    except:
        bot.reply_to(message, "❗ Используй: /boostprice 5")
        return

    save_price(newp)
    bot.reply_to(message, f"✅ Цена буста обновлена: {newp} ⭐")