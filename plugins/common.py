import random
import json
import os
from datetime import datetime, timezone

DATA_FILE = "plugins/data.json"

# -------------------------------------------------------
# Германия: текущая дата
# -------------------------------------------------------
def german_date():
    return datetime.now(timezone.utc).astimezone().date()


# -------------------------------------------------------
# Возвращает рост/уменьшение размерности (как раньше)
# ЧИСЛО, НЕ boolean
# -------------------------------------------------------
def weighted_random():
    r = random.randint(1, 100)

    # 65% — маленький рост
    if r <= 65:
        return random.randint(1, 5)

    # 20% — большой рост
    if r <= 85:
        return random.randint(6, 15)

    # 10% — нет изменений
    if r <= 95:
        return 0

    # 5% — уменьшение
    return random.randint(-5, -1)


# -------------------------------------------------------
# Возвращает красивое имя пользователя
# -------------------------------------------------------
def get_name(user):
    if not user:
        return "Безымянный"

    # Основной вариант — first_name + last_name
    if hasattr(user, "first_name") and user.first_name:
        if hasattr(user, "last_name") and user.last_name:
            return f"{user.first_name} {user.last_name}"
        return user.first_name

    # Если есть username
    if hasattr(user, "username") and user.username:
        return f"@{user.username}"

    return "Безымянный"


# -------------------------------------------------------
# Создание структуры данных, если нет
# -------------------------------------------------------
def ensure_user(chat_id, user):
    # Загружаем или создаём файл
    if not os.path.exists(DATA_FILE):
        data = {}
    else:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = {}

    chat_id = str(chat_id)
    user_id = str(user.id)

    # Создаем чат
    if chat_id not in data:
        data[chat_id] = {}

    # Создаём пользователя
    if user_id not in data[chat_id]:
        data[chat_id][user_id] = {
            "sisi": 0,
            "hui": 0,
            "klitor": 0,
            "last_sisi": None,
            "last_hui": None,
            "last_klitor": None
        }

    # Сохраняем структуру
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return data


# -------------------------------------------------------
# Обновление статистики (рост/уменьшение)
# -------------------------------------------------------
def update_stat(chat_id, user, field, delta):
    data = ensure_user(chat_id, user)
    chat_id = str(chat_id)
    user_id = str(user.id)

    data[chat_id][user_id][field] += delta

    # Никогда не опускаем ниже нуля
    if data[chat_id][user_id][field] < 0:
        data[chat_id][user_id][field] = 0

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# -------------------------------------------------------
# Обновляем дату последнего роста
# -------------------------------------------------------
def update_date(chat_id, user, field):
    data = ensure_user(chat_id, user)
    chat_id = str(chat_id)
    user_id = str(user.id)

    data[chat_id][user_id][field] = datetime.now().isoformat()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# -------------------------------------------------------
# Проверяем — уже был сегодня рост или нет
# -------------------------------------------------------
def was_today(chat_id, user, field):
    data = ensure_user(chat_id, user)
    chat_id = str(chat_id)
    user_id = str(user.id)

    timestamp = data[chat_id][user_id][field]

    if not timestamp:
        return False

    dt = datetime.fromisoformat(timestamp)

    return dt.date() == datetime.now().date()