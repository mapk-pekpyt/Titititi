from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today


def handle(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)

    if was_today(chat, user, "last_hui"):
        current = data[str(chat)][str(user.id)]["hui"]
        return bot.reply_to(
            message,
            f"{name}, шалунишка ты мой, думал не замечу? "
            f"Ты уже играл сегодня и твое достоинство сейчас {current}см 😳🍌"
        )

    delta = weighted_random()
    update_stat(chat, user, "hui", delta)
    update_date(chat, user, "last_hui")

    new_size = data[str(chat)][str(user.id)]["hui"] + delta

    bot.reply_to(
        message,
        f"{name}, твой хуй вырос на {delta:+}см, "
        f"теперь твоя гордость {new_size}см 😳🍌"
    )