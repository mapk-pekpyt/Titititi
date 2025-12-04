from plugins.common import weighted_random, get_name, ensure_user, update_stat, update_date, was_today
from plugins.bust_price import get_price
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def handle(bot, message):
    user = message.from_user
    chat = message.chat.id
    data = ensure_user(chat, user)

    if message.text.startswith("/klitor"):
        if was_today(chat, user, "last_klitor"):
            current = data[str(chat)][str(user.id)]["klitor"]
            return bot.reply_to(
                message,
                f"{get_name(user)}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твой клитор сейчас {current:.1f} мм 😳🍑"
            )

        delta = weighted_random() / 10  # клитор в мм, дробное
        update_stat(chat, user, "klitor", delta)
        update_date(chat, user, "last_klitor")
        new_size = data[str(chat)][str(user.id)]["klitor"]
        return bot.reply_to(
            message,
            f"{get_name(user)}, твой клитор вырос на {delta:+.1f} мм, "
            f"теперь он {new_size:.1f} мм 😳🍑"
        )

    if message.text.startswith("/boostk"):
        price = get_price()
        parts = message.text.split()
        if len(parts) < 2:
            return bot.reply_to(message, f"Укажи количество для буста: /boostk 5 (цена {price}⭐)")
        try:
            boost = float(parts[1])
            if boost <= 0:
                raise ValueError
        except:
            return bot.reply_to(message, "Укажи корректное положительное число для буста.")
        
        total = price * boost
        payer_name = get_name(user)
        markup = InlineKeyboardMarkup()
        cb = f"payboost:klitor:{user.id}:{boost}"
        markup.add(InlineKeyboardButton(f"💫 Оплатить {total} ⭐", callback_data=cb))
        bot.send_message(chat,
            f"{payer_name} хочет увеличить клитор на {boost:.1f} мм. Цена: {total} ⭐",
            reply_markup=markup
        )