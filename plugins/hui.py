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
    if cmd == "/hui":
        if was_today(chat, user, "last_hui"):
            current = data[str(chat)][str(user.id)]["hui"]
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твой хуй сейчас {current} см 😳🍆"
            )
        delta = weighted_random()
        new_size = max(0, data[str(chat)][str(user.id)]["hui"] + delta)
        update_stat(chat, user, "hui", delta)
        update_date(chat, user, "last_hui")
        bot.reply_to(
            message,
            f"{name}, твой хуй вырос на {delta:+}, теперь он {new_size} см 😳🍆"
        )
        return

    # ===== Платный буст =====
    if cmd == "/boosth":
        if len(text) < 2:
            return bot.reply_to(message, "Использование: /boosth <число>")
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
        cb_data = f"boost_hui:{user.id}:{boost}"
        markup.add(InlineKeyboardButton(text=f"💫 Оплатить {price} ⭐", callback_data=cb_data))

        bot.send_message(
            chat,
            f"{name} хочет увеличить хуй на {boost}. Для оплаты нажмите кнопку ниже.",
            reply_markup=markup
        )