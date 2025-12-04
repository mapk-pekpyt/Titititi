# plugins/sisi.py
import json
from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_date, was_today
from plugins.bust_price import load_price, save_price
from telebot.types import LabeledPrice

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"
ADMIN_ID = 5791171535

# ---- Helpers ----
def safe_get_user_data(data, chat, user):
    chat_s = str(chat)
    uid = str(user.id)
    if chat_s not in data:
        data[chat_s] = {}
    if uid not in data[chat_s]:
        # seed fields expected by top_plugin structure
        data[chat_s][uid] = {"sisi": 0, "hui": 0, "klit": 0, "stars": 0}
    return data[chat_s][uid]

# ---- Main game handler (/sisi) ----
def handle(bot, message):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    data = ensure_user(chat, user)  # expected to return the whole structure
    user_data = safe_get_user_data(data, chat, user)

    if was_today(chat, user, "last_sisi"):
        cur = user_data.get("sisi", 0)
        if cur < 0:
            user_data["sisi"] = 0
            cur = 0
        return bot.reply_to(message, f"{name}, шалунишка ты мой, думал не замечу? Ты уже играл сегодня и твои вишенки сейчас {cur} размера 😳🍒")

    delta = weighted_random()
    old = user_data.get("sisi", 0)
    new = old + delta
    if new < 0:
        delta = -old
        new = 0
    user_data["sisi"] = new
    update_date(chat, user, "last_sisi")
    bot.reply_to(message, f"{name}, твои сисечки выросли на {delta:+}, теперь твоя грудь {new} размера 😳🍒")

# ---- /busts (buy boost with stars) ----
def handle_busts(bot, message):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    data = ensure_user(chat, user)
    user_data = safe_get_user_data(data, chat, user)

    price = load_price()
    if user_data.get("stars", 0) < price:
        return bot.reply_to(message, f"{name}, у тебя недостаточно ⭐ — нужно {price}")
    user_data["stars"] = user_data.get("stars", 0) - price
    user_data["sisi"] = user_data.get("sisi", 0) + 1
    bot.reply_to(message, f"{name}, ✨ буст применён — теперь твоя грудь {user_data['sisi']} размера 🍒")

# ---- /bustprice (global price change) ----
def handle_bustprice(bot, message):
    parts = (message.text or "").split()
    if len(parts) == 1:
        bot.reply_to(message, f"Текущая цена буста: {load_price()} ⭐")
        return
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Только админ может менять цену.")
        return
    try:
        v = int(parts[1])
    except:
        return bot.reply_to(message, "Использование: /bustprice 5")
    save_price(v)
    bot.reply_to(message, f"✅ Глобальная цена буста установлена: {v} ⭐")