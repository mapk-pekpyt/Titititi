from plugins.common import weighted_random, get_name, german_date
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today


def handle(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)

    if was_today(chat, user, "last_sisi"):
        current = data[str(chat)][str(user.id)]["sisi"]
        return bot.reply_to(
            message,
            f"{name}, шалунишка ты мой, думал не замечу? "
            f"Ты уже играл сегодня и твои вишенки сейчас {current} размера 😳🍒"
        )

    delta = weighted_random()
    update_stat(chat, user, "sisi", delta)
    update_date(chat, user, "last_sisi")

    new_size = data[str(chat)][str(user.id)]["sisi"] + delta

    bot.reply_to(
        message,
        f"{name}, твои сисечки выросли на {delta:+}, "
        f"теперь твоя грудь {new_size} размера 😳🍒"
    )