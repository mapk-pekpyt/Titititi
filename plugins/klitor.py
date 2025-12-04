# plugins/klitor.py
from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_date, was_today
from plugins.bust_price import load_price, save_price

def handle(bot, message):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    data = ensure_user(chat, user)
    user_data = data[str(chat)].get(str(user.id))
    if user_data is None:
        user_data = {"sisi":0,"hui":0,"klit":0,"stars":0}
        data[str(chat)][str(user.id)] = user_data

    if was_today(chat, user, "last_klit"):
        cur = user_data.get("klit",0)
        if cur < 0:
            user_data["klit"] = 0
            cur = 0
        return bot.reply_to(message, f"{name}, шалунишка — сегодня уже играл. Клитор: {cur} мм 💦")

    delta = weighted_random()
    old = user_data.get("klit",0)
    new = old + delta
    if new < 0:
        delta = -old
        new = 0
    user_data["klit"] = new
    update_date(chat, user, "last_klit")
    bot.reply_to(message, f"{name}, твой клитор изменился на {delta:+} мм, теперь {new} мм 💦")

def handle_bustk(bot, message):
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
    user_data["klit"] = user_data.get("klit",0) + 1
    bot.reply_to(message, f"{name}, клитор увеличен — теперь {user_data['klit']} мм 💦")