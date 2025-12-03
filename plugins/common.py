# plugins/common.py

import random
from datetime import datetime, timezone

# ====== Время по Германии ======
def german_time():
    return datetime.now(timezone.utc).astimezone()


# ====== Вероятности прироста ======
def weighted_random():
    r = random.randint(1, 100)

    if r <= 65:           # 1–5 наиболее частые
        return random.randint(1, 5)
    elif r <= 80:         # 6–10 немного реже
        return random.randint(6, 10)
    else:                 # редкое уменьшение
        return random.randint(-10, 0)


# ====== Получение настоящего имени ======
def get_name(user):
    """
    Имя профиля, НЕ username.
    """
    try:
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        if user.first_name:
            return user.first_name
        if user.username:
            return f"@{user.username}"
    except:
        pass
    return "Безымянный"