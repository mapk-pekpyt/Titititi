from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from plugins.bust_price import price_data

def handle(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)

    # Если уже играли сегодня
    if was_today(chat, user, "last_sisi"):
        current = data[str(chat)][str(user.id)]["sisi"]
        return bot.reply_to(
            message,
            f"{name}, шалунишка ты мой, думал не замечу? "
            f"Ты уже играл сегодня и твои вишенки сейчас {current} размера 😳🍒"
        )

    delta = weighted_random()
    if delta < 0:
        delta = abs(delta)

    update_stat(chat, user, "sisi", delta)
    update_date(chat, user, "last_sisi")

    new_size = data[str(chat)][str(user.id)]["sisi"]

    bot.reply_to(
        message,
        f"{name}, твои сисечки выросли на {delta:+}, "
        f"теперь твоя грудь {new_size} размера 😳🍒"
    )


# ПЛАТНЫЙ БУСТ
def handle_bust(bot, message):
    chat = message.chat.id
    user = message.from_user
    name = get_name(user)

    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Укажи, на сколько увеличить грудь. Например:\n/busts 3")

    try:
        amount = float(args[1])
    except:
        return bot.reply_to(message, "Введи нормальное число.")

    if amount <= 0:
        return bot.reply_to(message, "Буст может быть только положительным!")

    price = price_data.get("bust_price", 50)

    # Создаём счёт
    bot.send_invoice(
        chat_id=chat,
        title="Увеличение груди",
        description=f"Буст груди на {amount}",
        payload=f"bust_sisi|{amount}",
        provider_token=None,  # У ТЕБЯ ОБРАБОТКА УЖЕ В main И plugins/mut — НЕ ТРОГАЮ
        currency="XTR",
        prices=[{"label": "Boost", "amount": int(price)}],
        start_parameter="boost-sisi"
    )


# ПОСЛЕ УСПЕШНОЙ ОПЛАТЫ
def boost_success(chat, user, amount):
    data = ensure_user(chat, user)

    if amount < 0:
        amount = abs(amount)

    data[str(chat)][str(user.id)]["sisi"] += amount