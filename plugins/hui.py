from plugins.common import weighted_random, get_name, ensure_user, update_stat, update_date, was_today
from plugins.bust_price import get_price
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def handle(bot, message):
    user = message.from_user
    chat = message.chat.id
    data = ensure_user(chat, user)

    if message.text.startswith("/hui"):
        if was_today(chat, user, "last_hui"):
            current = data[str(chat)][str(user.id)]["hui"]
            return bot.reply_to(
                message,
                f"{get_name(user)}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твой хуй сейчас {current} размера 😳🍆"
            )

        delta = weighted_random()
        update_stat(chat, user, "hui", delta)
        update_date(chat, user, "last_hui")
        new_size = data[str(chat)][str(user.id)]["hui"]
        return bot.reply_to(
            message,
            f"{get_name(user)}, твой хуй вырос на {delta:+}, "
            f"теперь он {new_size} размера 😳🍆"
        )

    if message.text.startswith("/boosth"):
        price = get_price()
        parts = message.text.split()
        if len(parts) < 2:
            return bot.reply_to(message, f"Укажи количество для буста: /boosth 5 (цена {price}⭐)")
        try:
            boost = int(parts[1])
            if boost <= 0:
                raise ValueError
        except:
            return bot.reply_to(message, "Укажи корректное положительное число для буста.")
        
        total = price * boost
        payer_name = get_name(user)
        markup = InlineKeyboardMarkup()
        cb = f"payboost:hui:{user.id}:{boost}"
        markup.add(InlineKeyboardButton(f"💫 Оплатить {total} ⭐", callback_data=cb))
        bot.send_message(chat,
            f"{payer_name} хочет увеличить хуй на {boost}. Цена: {total} ⭐",
            reply_markup=markup
        )