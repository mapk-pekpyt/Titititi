import json
from .common import get_name

FILES = {
    "sisi": "data/sisi.json",
    "hui": "data/hui.json",
    "klitor": "data/klitor.json"
}

EMOJIS = {
    "sisi": "🎀",
    "hui": "🍆",
    "klitor": "💎"
}

TRIGGER = "/top"

def handle(bot, message):
    if not message.text:
        return

    text = message.text.split("@")[0]  # поддержка /top@BotName
    if text != TRIGGER:
        return

    chat_id = str(message.chat.id)

    response = ""

    for key, file in FILES.items():
        try:
            with open(file, "r") as f:
                data = json.load(f)
        except:
            data = {}

        chat_data = data.get(chat_id, {})

        # сортировка
        if key == "klitor":
            sorted_data = sorted(chat_data.items(), key=lambda x: x[1]["size_mm"], reverse=True)
        else:
            sorted_data = sorted(chat_data.items(), key=lambda x: x[1]["size"], reverse=True)

        response += f"{EMOJIS[key]} ТОП {key}:\n"

        for i, (user_id, info) in enumerate(sorted_data[:5], 1):
            name = info.get("name", "Без имени")

            if key == "klitor":
                size = info.get("size_mm", 0)
                response += f"{i}. {name} — {size} мм\n"
            elif key == "sisi":
                size = info.get("size", 0)
                response += f"{i}. {name} — размер {size}\n"
            else:
                size = info.get("size", 0)
                response += f"{i}. {name} — {size} см\n"

        response += "\n"

    bot.send_message(message.chat.id, response)