import json
import os

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

def load_data(file):
    if not os.path.exists(file):
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def handle(bot, message):
    for key, file in FILES.items():
        data = load_data(file)
        if key == "klitor":
            sorted_data = sorted(data.items(), key=lambda x: x[1].get("size_mm", 0), reverse=True)
        else:
            sorted_data = sorted(data.items(), key=lambda x: x[1].get("size", 0), reverse=True)
        text = f"🏆 Топ {EMOJIS[key]}:\n"
        for i, (user_id, info) in enumerate(sorted_data[:5], 1):
            name = info.get("name", str(user_id))
            size = info.get("size") if key != "klitor" else info.get("size_mm", 0)/10
            text += f"{i}. {name} — {size}\n"
        bot.send_message(message.chat.id, text)