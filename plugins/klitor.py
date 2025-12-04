from plugins.common import weighted_random, get_name, ensure_user, update_stat, update_date, was_today
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

def handle(bot, message: Message):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    data = ensure_user(chat, user)

    text = (message.text or "").split()
    cmd = text[0].lower()

    # ===== Ежедневная игра =====
    if cmd == "/klitor":
        if was_today(chat, user, "last_klitor"):
            current = data[str(chat)][str(user.id)]["klitor"]
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и клитор сейчас {current:.1f} мм 😳💦"
            )
        delta = weighted_random()
        new_size = max(0, data[str(chat)][str(user.id)]["klitor"] + delta)
        update_stat(chat, user, "klitor", delta)
        update_date(chat, user, "last_klitor")
        bot.reply_to(
            message,
            f"{name}, клитор вырос на {delta:+.1f} мм, теперь {new_size:.1f} мм 😳💦"
        )
        return

    # ===== Платный буст =====
    if cmd == "/boostk":
        if len(text) < 2:
            return bot.reply_to(message, "Использование: /boostk <число>")
        try:
            boost = float(text[1])
            if boost <= 0:
                raise ValueError()
        except:
            return bot.reply_to(message, "Введите положительное число!")

        try:
            from plugins import bust_price
            price = int(bust_price.price_data)
        except:
            price = 0

        markup = InlineKeyboardMarkup()
        cb_data = f"boost_klitor:{user.id}:{boost}"
        markup.add(InlineKeyboardButton(text=f"💫 Оплатить {price} ⭐", callback_data=cb_data))

        bot.send_message(
            chat,
            f"{name} хочет увеличить клитор на {boost:.1f} мм. Для оплаты нажмите кнопку ниже.",
            reply_markup=markup
        )