from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from plugins.bust_price import price_data


def handle(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)
    user_data = data[str(chat)][str(user.id)]

    if was_today(chat, user, "last_klit"):
        cur = user_data["klit"]

        if cur < 0:
            cur = 0
            user_data["klit"] = 0

        return bot.reply_to(
            message,
            f"{name}, сегодня уже играла 😳\n"
            f"Твой клитор сейчас **{cur} мм** 💦"
        )

    delta = weighted_random()
    old = user_data["klit"]
    new_val = max(0, old + delta)
    user_data["klit"] = new_val

    update_date(chat, user, "last_klit")

    bot.reply_to(
        message,
        f"{name}, твой клитор изменился на **{delta:+}**, теперь **{new_val} мм** 💦"
    )


def handle_bustk(bot, message):
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
            f"{name}, тебе нужно ⭐: {cost}"
        )

    user_data["stars"] -= cost
    user_data["klit"] += 1

    bot.reply_to(
        message,
        f"{name}, твой клитор подрос 👉💦\n"
        f"Теперь: **{user_data['klit']} мм**"
    )