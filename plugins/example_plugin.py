def register():
    return "example"


def handle(cmd, message, users):
    if cmd != "/test":
        return False

    chat_id = message["chat"]["id"]
    from main import send

    send(chat_id, "Плагин работает")
    return True