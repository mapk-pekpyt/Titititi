import json
import os
import random
from datetime import datetime, timedelta

DATA_FILE = "data/sisi.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_real_name(user):
    return getattr(user, 'full_name', getattr(user, 'first_name', f"User{user.id}"))

def handle(bot, message):
    user_id = str(message.from_user.id)
    user_name = get_real_name(message.from_user)
    chat_id = str(message.chat.id)
    
    data = load_data()
    if chat_id not in data:
        data[chat_id] = {}

    user_data = data[chat_id].get(user_id, {"size": 0, "last_play": None})

    # Проверяем, играл ли сегодня
    last_play = user_data.get("last_play")
    today = datetime.now().date()
    if last_play:
        last_play_date = datetime.fromisoformat(last_play).date()
        if last_play_date == today:
            bot.send_message(chat_id, f"{user_name}, ты уже играл сегодня 😅\nТекущий размер груди: {user_data['size']}")
            return

    # Генерируем прирост: чаще 1-5, реже -10-0 и 6-10
    roll = random.randint(1, 100)
    if roll <= 70:
        delta = random.randint(1, 5)
    elif roll <= 85:
        delta = random.randint(-10, 0)
    else:
        delta = random.randint(6, 10)

    # не уменьшаем меньше нуля
    new_size = max(user_data["size"] + delta, 0)
    user_data.update({
        "size": new_size,
        "last_play": datetime.now().isoformat()
    })
    data[chat_id][user_id] = user_data
    save_data(data)

    # Красивое сообщение
    bot.send_message(chat_id, f"🎀 {user_name}, твои сиськи выросли на {delta}!\nТеперь твой размер груди: {new_size}")