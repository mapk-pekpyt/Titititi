import random
from main import send

KEY = "sisi"

def register():
    return KEY


def handle(cmd, message, users):
    if cmd != "/sisi":
        return False

    user_id = str(message["from"]["id"])
    chat_id = message["chat"]["id"]
    name = message["from"].get("first_name", "Ты")

    users.setdefault(user_id, {})
    users[user_id].setdefault(KEY, {"value": 0, "last": 0})

    data = users[user_id][KEY]

    if data["last"] == int(time.time() // 86400):
        send(chat_id, f"{name}, ты уже играла сегодня.\nТвой размер: {data['value']}")
        return True

    grow = random.randint(-10, 10)
    new_value = max(0, data["value"] + grow)

    data["value"] = new_value
    data["last"] = int(time.time() // 86400)

    if grow >= 0:
        send(chat_id, f"{name}, твоя грудь выросла на {grow}. Теперь размер: {new_value}")
    else:
        send(chat_id, f"{name}, твоя грудь уменьшилась на {abs(grow)}. Теперь размер: {new_value}")

    return True