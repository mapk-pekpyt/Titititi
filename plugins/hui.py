import os
import telebot
from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from plugins.bust_price import load_price
from plugins.bust_command import handle_bustprice


def handle(bot, message):
    if message.text.startswith("/bustprice"):
        return handle_bustprice(bot, message)

    if message.text.startswith("/busth"):
        return bust(bot, message)

    user = message.from_user
    name = get_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)

    if was_today(chat, user, "last_hui"):
        current = data[str(chat)][str(user.id)]["hui"]
        return bot.reply_to(message, f"{name}, сегодня уже играла, размер {current} 🍆")

    delta = weighted_random()
    new_val = max(0, data[str(chat)][str(user.id)]["hui"] + delta)

    update_stat(chat, user, "hui", delta)
    update_date(chat, user, "last_hui")

    bot.reply_to(message, f"{name}, хуй вырос на {delta:+}, теперь {new_val} 🍆🔥")


def bust(bot, message):
    user = message.from_user
    chat = message.chat.id

    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Использование: /busth 5")

    try:
        amount = int(parts[1])
    except:
        return bot.reply_to(message, "Нужно число: /busth 5")

    if amount <= 0:
        return bot.reply_to(message, "Буст должен быть положительным!")

    price = load_price()["price"]

    invoice = telebot.types.LabeledPrice(
        label=f"Буст хуя +{amount}",
        amount=price * 100
    )

    bot.send_invoice(
        chat_id=chat,
        title="Буст хуя",
        description=f"Увеличение на +{amount}",
        provider_token=os.environ.get("PAY_TOKEN"),
        currency="EUR",
        prices=[invoice],
        payload=f"bust_hui:{amount}"
    )


def after_payment(bot, message, amount):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    data = ensure_user(chat, user)
    current = data[str(chat)][str(user.id)]["hui"]

    new_val = max(0, current + amount)
    update_stat(chat, user, "hui", amount)

    bot.send_message(chat, f"✨ {name}, буст хую +{amount}! Теперь {new_val} 🍆🔥")