from plugins.common import get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from plugins.bust_price import price_data
import random

def weighted_mm():
    # 0.1 - 1.0 мм
    return round(random.uniform(0.1, 1.0), 1)

def handle(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id
    data = ensure_user(chat, user)

    if was_today(chat, user, "last_klitor"):
        current = data[str(chat)][str(user.id)]["klitor"]
        return bot.reply_to(
            message,
            f"{name}, моя сладкая шалунья, ты уже играла сегодня… "
            f"Твой клитор сейчас {current:.1f} мм 😳💦"
        )

    delta = weighted_mm()

    update_stat(chat, user, "klitor", delta)
    update_date(chat, user, "last_klitor")

    new_size = data[str(chat)][str(user.id)]["klitor"]

    bot.reply_to(
        message,
        f"{name}, твой клитор вырос на +{delta:.1f}, теперь он {new_size:.1f} мм 😳💦"
    )


def handle_bust(bot, message):
    chat = message.chat.id
    user = message.from_user
    name = get_name(user)

    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Укажи, на сколько увеличить. Например:\n/bustk 0.5")

    try:
        amount = float(args[1])
    except:
        return bot.reply_to(message, "Введи число.")

    if amount <= 0:
        return bot.reply_to(message, "Только положительное число!")

    price = price_data.get("bust_price", 50)

    bot.send_invoice(
        chat_id=chat,
        title="Буст клитора",
        description=f"+{amount} мм к размеру",
        payload=f"bust_klit|{amount}",
        provider_token=None,
        currency="XTR",
        prices=[{"label": "Boost", "amount": int(price)}],
        start_parameter="boost-klit"
    )


def boost_success(chat, user, amount):
    data = ensure_user(chat, user)
    if amount < 0:
        amount = abs(amount)

    data[str(chat)][str(user.id)]["klitor"] += amount