from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from plugins.bust_price import price_data

def handle(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id
    data = ensure_user(chat, user)

    if was_today(chat, user, "last_hui"):
        current = data[str(chat)][str(user.id)]["hui"]
        return bot.reply_to(
            message,
            f"{name}, мой хорошенький, уже баловался сегодня… "
            f"Твой дружок сейчас {current} см 🍆"
        )

    delta = weighted_random()
    if delta < 0:
        delta = abs(delta)

    update_stat(chat, user, "hui", delta)
    update_date(chat, user, "last_hui")

    new_size = data[str(chat)][str(user.id)]["hui"]

    bot.reply_to(
        message,
        f"{name}, твой хуй вырос на {delta:+}, теперь его длина {new_size} см 🍆🔥"
    )


def handle_bust(bot, message):
    chat = message.chat.id
    user = message.from_user
    name = get_name(user)

    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Укажи, на сколько увеличить. Например:\n/busth 2")

    try:
        amount = float(args[1])
    except:
        return bot.reply_to(message, "Введи число.")

    if amount <= 0:
        return bot.reply_to(message, "Только положительное число!")

    price = price_data.get("bust_price", 50)

    bot.send_invoice(
        chat_id=chat,
        title="Буст хуя",
        description=f"+{amount} см к длине",
        payload=f"bust_hui|{amount}",
        provider_token=None,
        currency="XTR",
        prices=[{"label": "Boost", "amount": int(price)}],
        start_parameter="boost-hui"
    )


def boost_success(chat, user, amount):
    data = ensure_user(chat, user)
    if amount < 0:
        amount = abs(amount)

    data[str(chat)][str(user.id)]["hui"] += amount