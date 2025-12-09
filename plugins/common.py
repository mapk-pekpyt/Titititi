import random
import json
import os
from datetime import datetime, timezone

DATA_FILE = "plugins/data.json"

# ---------------------------
# Германия: текущая дата
# ---------------------------
def german_date():
    return datetime.now(timezone.utc).astimezone().date()

# ---------------------------
# Вероятности
# ---------------------------
def weighted_random():
    r = random.randint(1, 100)
    if r <= 65:
        return True
    return False

# ---------------------------
# Получение имени пользователя
# ---------------------------
def get_name(user):
    if not user:
        return "Безымянный"
    if hasattr(user, "first_name") and user.first_name:
        if hasattr(user, "last_name") and user.last_name:
            return f"{user.first_name} {user.last_name}"
        return user.first_name
    if hasattr(user, "username") and user.username:
        return f"@{user.username}"
    return "Безымянный"

# ---------------------------
# Работа с данными пользователей
# ---------------------------
def ensure_user(chat_id, user):
    if not os.path.exists(DATA_FILE):
        data = {}
    else:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    chat_id = str(chat_id)
    user_id = str(user.id)

    if chat_id not in data:
        data[chat_id] = {}
    if user_id not in data[chat_id]:
        data[chat_id][user_id] = {
            "sisi": 0,
            "hui": 0,
            "klitor": 0,
            "last_sisi": None,
            "last_hui": None,
            "last_klitor": None
        }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return data

def update_stat(chat_id, user, field, delta):
    data = ensure_user(chat_id, user)
    user_id = str(user.id)
    chat_id = str(chat_id)
    data[chat_id][user_id][field] += delta
    # Никогда не делаем отрицательные значения
    if data[chat_id][user_id][field] < 0:
        data[chat_id][user_id][field] = 0
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_date(chat_id, user, field):
    data = ensure_user(chat_id, user)
    user_id = str(user.id)
    chat_id = str(chat_id)
    data[chat_id][user_id][field] = datetime.now().isoformat()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def was_today(chat_id, user, field):
    data = ensure_user(chat_id, user)
    user_id = str(user.id)
    chat_id = str(chat_id)
    val = data[chat_id][user_id][field]
    if not val:
        return False
    dt = datetime.fromisoformat(val)
    return dt.date() == datetime.now().date()