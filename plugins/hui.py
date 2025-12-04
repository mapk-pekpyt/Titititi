from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from plugins.bust_price import price_data, save_price


def handle(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)
    user_data = data[str(chat)][str(user.id)]

    if was_today(chat, user, "last_hui"):
        cur = user_data["hui"]

        if cur < 0:
            cur = 0
            user_data["hui"] = 0

        return bot.reply_to(
            message,
            f"{name}, ты уже играла сегодня 😏\n"
            f"Твой болт: **{cur} см** 🍆"
        )

    delta = weighted_random()
    old = user_data["hui"]
    new_val = max(0, old + delta)
    user_data["hui"] = new_val

    update_date(chat, user, "last_hui")

    bot.reply_to(
        message,
        f"{name}, твой болт изменился на **{delta:+}**, теперь **{new_val} см** 🍆"
    )


def handle_busth(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id
    uid = str(user.id)

    data = ensure_user(chat, user)
    user_data = data[str(chat)][uid]

    cost = price_data["price"]

    if user_data.get("stars", 0) < cost:
        return bot.reply_to(
            message,
            f"{name}, недостаточно ⭐ (нужно {cost})"
        )

    user_data["stars"] -= cost
    user_data["hui"] += 1

    bot.reply_to(
        message,
        f"{name}, твой болт стал больше 😳\n"
        f"Теперь: **{user_data['hui']} см** 🍆"
    )