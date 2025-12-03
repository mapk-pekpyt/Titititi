import random
from datetime import datetime, timezone, timedelta

# Германия
def german_date():
    return datetime.now(timezone.utc).astimezone().date()

# Вероятности
def weighted_random():
    r = random.randint(1, 100)
    if r <= 65:
        return random.randint(1, 5)
    elif r <= 85:
        return random.randint(6, 10)
    else:
        return random.randint(-10, 0)

# Имя пользователя
def get_name(user):
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    if user.first_name:
        return user.first_name
    if user.username:
        return f"@{user.username}"
    return "Безымянный"