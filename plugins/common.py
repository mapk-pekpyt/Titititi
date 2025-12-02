import random
from datetime import datetime, timezone

# время по Германии (Берлин)
def german_time():
    return datetime.now(timezone.utc).astimezone()

# вероятность приращения
def weighted_random():
    r = random.randint(1, 100)

    if r <= 65:           # 1–5 наиболее частые
        return random.randint(1, 5)
    elif r <= 80:         # чуть реже 6–10
        return random.randint(6, 10)
    else:                 # редкое уменьшение
        return random.randint(-10, 0)

# имя пользователя
def get_name(user):
    if user.username:
        return f"@{user.username}"
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    return user.first_name or "Безымянный"