from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today


def handle(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)

    if was_today(chat, user, "last_klitor"):
        mm = data[str(chat)][str(user.id)]["klitor"]
        return bot.reply_to(
            message,
            f"{name}, шалунишка ты мой, думал не замечу? "
            f"Ты уже играл сегодня и твоя валына сейчас {mm/10:.1f}см 😳🍑"
        )

    delta_mm = weighted_random() * 1.0  # мм
    update_stat(chat, user, "klitor", delta_mm)
    update_date(chat, user, "last_klitor")

    new_mm = data[str(chat)][str(user.id)]["klitor"] + delta_mm

    bot.reply_to(
        message,
        f"{name}, твой клитор вырос на {delta_mm:+.1f}мм, "
        f"теперь эта валына {new_mm/10:.1f}см 😳🍑"
    )