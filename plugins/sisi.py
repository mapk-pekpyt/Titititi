from plugins.common import weighted_random, get_name, ensure_user, update_stat, update_date, was_today
from plugins.bust_price import get_price
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def handle(bot, message):
    user = message.from_user
    chat = message.chat.id
    data = ensure_user(chat, user)

    # Ежедневный рост
    if message.text.startswith("/sisi"):
        if was_today(chat, user, "last_sisi"):
            current = data[str(chat)][str(user.id)]["sisi"]
            return bot.reply_to(
                message,
                f"{get_name(user)}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твои вишенки сейчас {current} размера 😳🍒"
            )

        delta = weighted_random()
        update_stat(chat, user, "sisi", delta)
        update_date(chat, user, "last_sisi")
        new_size = data[str(chat)][str(user.id)]["sisi"]
        return bot.reply_to(
            message,
            f"{get_name(user)}, твои сисечки выросли на {delta:+}, "
            f"теперь твоя грудь {new_size} размера 😳🍒"
        )

    # Платный буст
    if message.text.startswith("/boosts"):
        price = get_price()
        parts = message.text.split()
        if len(parts) < 2:
            return bot.reply_to(message, f"Укажи количество для буста: /boosts 5 (цена {price}⭐)")
        try:
            boost = int(parts[1])
            if boost <= 0:
                raise ValueError
        except:
            return bot.reply_to(message, "Укажи корректное положительное число для буста.")
        
        total = price * boost
        payer_name = get_name(user)
        # Здесь создаём кнопку для оплаты через Stars
        markup = InlineKeyboardMarkup()
        cb = f"payboost:sisi:{user.id}:{boost}"
        markup.add(InlineKeyboardButton(f"💫 Оплатить {total} ⭐", callback_data=cb))
        bot.send_message(chat,
            f"{payer_name} хочет увеличить грудь на {boost}. Цена: {total} ⭐",
            reply_markup=markup
        )