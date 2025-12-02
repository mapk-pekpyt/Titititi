import json
import os
from datetime import datetime

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


def get_real_name(user):
    if user.full_name:
        return user.full_name
    if user.first_name:
        return user.first_name
    return f"User{user.id}"


def add_score(chat_id, user, amount):
    chat_id = str(chat_id)
    user_id = str(user.id)

    top = load_top()

    if chat_id not in top:
        top[chat_id] = {}

    if user_id not in top[chat_id]:
        top[chat_id][user_id] = {
            "name": get_real_name(user),
            "score": 0,
            "updated": datetime.utcnow().isoformat()
        }

    top[chat_id][user_id]["score"] += amount
    top[chat_id][user_id]["name"] = get_real_name(user)
    top[chat_id][user_id]["updated"] = datetime.utcnow().isoformat()

    save_top(top)


def format_top(chat_id):
    chat_id = str(chat_id)
    top = load_top()

    if chat_id not in top or not top[chat_id]:
        return "Тут ещё никто не играл 😢"

    sorted_users = sorted(
        top[chat_id].values(),
        key=lambda x: x["score"],
        reverse=True
    )

    result = "🏆 *Топ игроков этого чата:*\n\n"
    for i, u in enumerate(sorted_users, start=1):
        result += f"{i}. *{u['name']}* — `{u['score']}` очков\n"

    return result


# 🌟 Главная функция плагина — вызов через /top
async def run(update, context):
    chat_id = update.effective_chat.id
    await update.message.reply_text(format_top(chat_id), parse_mode="Markdown")