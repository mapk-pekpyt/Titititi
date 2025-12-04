# plugins/hui.py
from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_date, was_today
from plugins.bust_price import load_price, save_price

ADMIN_ID = 5791171535

def handle(bot, message):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    data = ensure_user(chat, user)
    user_data = data[str(chat)].get(str(user.id))
    if user_data is None:
        user_data = {"sisi":0,"hui":0,"klit":0,"stars":0}
        data[str(chat)][str(user.id)] = user_data

    if was_today(chat, user, "last_hui"):
        cur = user_data.get("hui", 0)
        if cur < 0:
            user_data["hui"] = 0
            cur = 0
        return bot.reply_to(message, f"{name}, шалунишка ты мой, ты уже играл сегодня. Твой болт сейчас {cur} см 🍆")

    delta = weighted_random()
    old = user_data.get("hui",0)
    new = old + delta
    if new < 0:
        delta = -old
        new = 0
    user_data["hui"] = new
    update_date(chat, user, "last_hui")
    bot.reply_to(message, f"{name}, твой болт вырос на {delta:+} см, теперь он {new} см 🍆")

def handle_busth(bot, message):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)
    data = ensure_user(chat, user)
    user_data = data[str(chat)].get(str(user.id))
    if user_data is None:
        user_data = {"sisi":0,"hui":0,"klit":0,"stars":0}
        data[str(chat)][str(user.id)] = user_data

    price = load_price()
    if user_data.get("stars",0) < price:
        return bot.reply_to(message, f"{name}, недостаточно ⭐ (нужно {price})")
    user_data["stars"] -= price
    user_data["hui"] = user_data.get("hui",0) + 1
    bot.reply_to(message, f"{name}, твой болт увеличен на 1 см — теперь {user_data['hui']} см 🍆")