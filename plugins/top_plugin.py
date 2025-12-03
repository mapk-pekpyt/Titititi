# plugins/top_plugin.py

import json
import os
from plugins.common import get_name

TOP_FILE = "top_data.json"


def load_top():
    if not os.path.exists(TOP_FILE):
        return {}
    try:
        with open(TOP_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return {}


def save_top(data):
    with open(TOP_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_stat(chat_id, user, field, amount):
    """
    field:
        - sisi_size (размер груди)
        - hui_size (см)
        - klitor_size (мм)
    """

    chat_id = str(chat_id)
    user_id = str(user.id)

    top = load_top()

    if chat_id not in top:
        top[chat_id] = {}

    if user_id not in top[chat_id]:
        top[chat_id][user_id] = {
            "name": get_name(user),
            "sisi_size": 0,
            "hui_size": 0,
            "klitor_size": 0.0
        }

    top[chat_id][user_id]["name"] = get_name(user)
    top[chat_id][user_id][field] += amount

    save_top(top)


def format_top(chat_id):
    chat_id = str(chat_id)
    top = load_top()

    if chat_id not in top or not top[chat_id]:
        return "Тут ещё никто не играл 😢"

    users = list(top[chat_id].values())

    users.sort(key=lambda u: (u["sisi_size"] + u["hui_size"] + u["klitor_size"]), reverse=True)

    msg = "🏆 *ТОП игроков этого чата:*\n\n"

    for i, u in enumerate(users, start=1):
        msg += (
            f"{i}. *{u['name']}*\n"
            f"   Сиськи: {u['sisi_size']} размер\n"
            f"   Хуй: {u['hui_size']} см\n"
            f"   Клитор: {u['klitor_size']:.1f} мм\n\n"
        )

    return msg


def format_my(chat_id, user_id):
    chat_id = str(chat_id)
    user_id = str(user_id)

    top = load_top()

    if chat_id not in top or user_id not in top[chat_id]:
        return "У тебя пока нет результатов 😢"

    u = top[chat_id][user_id]

    return (
        f"📊 *Твои размеры:*\n\n"
        f"Сиськи: {u['sisi_size']} размер\n"
        f"Хуй: {u['hui_size']} см\n"
        f"Клитор: {u['klitor_size']:.1f} мм"
    )


def handle(bot, message):
    chat_id = message.chat.id
    bot.reply_to(message, format_top(chat_id), parse_mode="Markdown")


def handle_my(bot, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot.reply_to(message, format_my(chat_id, user_id), parse_mode="Markdown")