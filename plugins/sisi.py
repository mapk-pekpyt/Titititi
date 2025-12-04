import os
import telebot
from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from plugins.bust_price import load_price
from plugins.bust_command import handle_bustprice


def handle(bot, message):
    # /bustprice — отдельная команда!
    if message.text.startswith("/bustprice"):
        return handle_bustprice(bot, message)

    if message.text.startswith("/busts"):
        return bust(bot, message)

    # Обычная игра
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)

    if was_today(chat, user, "last_sisi"):
        current = data[str(chat)][str(user.id)]["sisi"]
        return bot.reply_to(
            message,
            f"{name}, сегодня уже играла, твой размер {current} 😳🍒"
        )

    delta = weighted_random()
    new_val = max(0, data[str(chat)][str(user.id)]["sisi"] + delta)

    update_stat(chat, user, "sisi", delta)
    update_date(chat, user, "last_sisi")

    bot.reply_to(
        message,
        f"{name}, твои сисечки выросли на {delta:+}, теперь размер {new_val} 😳🍒"
    )


def bust(bot, message):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Использование: /busts 5")

    try:
        amount = int(parts[1])
    except:
        return bot.reply_to(message, "Нужно число: /busts 5")

    if amount <= 0:
        return bot.reply_to(message, "Буст должен быть положительным!")

    price = load_price()["price"]

    invoice = telebot.types.LabeledPrice(
        label=f"Буст груди +{amount}",
        amount=price * 100
    )

    bot.send_invoice(
        chat_id=chat,
        title="Буст груди",
        description=f"Увеличение размера груди на +{amount}",
        provider_token=os.environ.get("PAY_TOKEN"),
        currency="EUR",
        prices=[invoice],
        payload=f"bust_sisi:{amount}"
    )


def after_payment(bot, message, amount):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)
    current = data[str(chat)][str(user.id)]["sisi"]

    new_val = max(0, current + amount)
    update_stat(chat, user, "sisi", amount)

    bot.send_message(
        chat,
        f"✨ {name}, буст успешен! +{amount}, теперь размер {new_val} 😳🍒"
    )