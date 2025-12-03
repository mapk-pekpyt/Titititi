# plugins/sisi.py

from plugins.common import weighted_random, get_name
from plugins.top_plugin import add_stat


def handle(bot, message):
    user = message.from_user
    name = get_name(user)

    delta = weighted_random()

    add_stat(message.chat.id, user, "sisi_size", delta)

    bot.reply_to(
        message,
        f"{name}, твой новый размер сисек: {delta:+} размера 😳",
    )