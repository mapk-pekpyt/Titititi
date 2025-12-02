import json, os
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
    if not message.text or not message.text.startswith(TRIGGER):
        return

    chat_id = message.chat.id

    for key, file in FILES.items():
        if not os.path.exists(file):
            bot.send_message(chat_id, f"Топ {EMOJIS[key]} пустой.")
            continue

        with open(file, "r") as f:
            data = json.load(f)

        if key == "klitor":
            sorted_data = sorted(data.items(), key=lambda x: x[1]["size_mm"], reverse=True)
        else:
            sorted_data = sorted(data.items(), key=lambda x: x[1]["size"], reverse=True)

        text = f"{EMOJIS[key]} ТОП {key}:\n"

        for i, (uid, info) in enumerate(sorted_data[:5], 1):
            name = info.get("name", uid)

            if key == "klitor":
                size = info["size_mm"]
                text += f"{i}. {name} — {size} мм\n"
            elif key == "hui":
                size = info["size"]
                text += f"{i}. {name} — {size} см\n"
            else:
                size = info["size"]
                text += f"{i}. {name} — размер {size}\n"

        bot.send_message(chat_id, text)