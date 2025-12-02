import json
import os

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
    if hasattr(user, "full_name") and user.full_name:
        return user.full_name
    if hasattr(user, "first_name") and user.first_name:
        return user.first_name
    return f"User{user.id}"

def add_score(chat_id, user, game, amount):
    """
    chat_id: id чата
    user: объект пользователя
    game: 'sisi', 'hui', 'klitor'
    amount: число для прибавления к текущему размеру
    """
    chat_id = str(chat_id)
    user_id = str(user.id)
    top = load_top()

    if chat_id not in top:
        top[chat_id] = {}

    if user_id not in top[chat_id]:
        top[chat_id][user_id] = {
            "name": get_real_name(user),
            "sisi": 0,
            "hui": 0,
            "klitor": 0
        }

    top[chat_id][user_id][game] += amount
    top[chat_id][user_id]["name"] = get_real_name(user)
    save_top(top)

def format_top(chat_id):
    chat_id = str(chat_id)
    top = load_top()
    if chat_id not in top or not top[chat_id]:
        return "Тут ещё никто не играл 😢"

    # сортировка по сумме всех игр
    sorted_users = sorted(
        top[chat_id].values(),
        key=lambda x: x["sisi"] + x["hui"] + x["klitor"],
        reverse=True
    )

    result = "🏆 Топ игроков чата:\n\n"
    for i, u in enumerate(sorted_users, start=1):
        result += f"{i}. {u['name']} — Сиськи: {u['sisi']}, Хуй: {u['hui']}, Клитор: {u['klitor']}\n"

    return result

def handle(bot, message):
    chat_id = message.chat.id
    bot.send_message(chat_id, format_top(chat_id))

def handle_my(bot, message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    top = load_top()
    if chat_id not in top or user_id not in top[chat_id]:
        bot.send_message(chat_id, "Ты ещё не играл 😢")
        return
    data = top[chat_id][user_id]
    text = (
        f"👤 {data['name']}, твои размеры:\n"
        f"🎀 Сиськи: {data['sisi']}\n"
        f"🍆 Хуй: {data['hui']}\n"
        f"💎 Клитор: {data['klitor']}"
    )
    bot.send_message(chat_id, text)