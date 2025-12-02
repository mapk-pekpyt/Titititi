# plugins/top_plugin.py
import os
import json

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

def ensure_file(path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_data(path):
    ensure_file(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def get_top_text(key, data):
    if key == "klitor":
        sorted_data = sorted(data.items(), key=lambda x: x[1].get("size_mm", 0), reverse=True)
    else:
        sorted_data = sorted(data.items(), key=lambda x: x[1].get("size", 0), reverse=True)

    text = f"{EMOJIS[key]} <b>ТОП {key}</b>:\n"
    if not sorted_data:
        text += "Пусто 😅"
        return text

    for i, (uid, info) in enumerate(sorted_data[:10], 1):
        name = info.get("name", uid)
        if key == "klitor":
            size = info.get("size_mm", 0) / 10
            text += f"{i}. {name} — {size:.1f} см\n"
        else:
            size = info.get("size", 0)
            text += f"{i}. {name} — {size} см\n"
    return text

def handle(bot, message):
    chat_id = message.chat.id
    # send three separate messages (one per game)
    for key, path in FILES.items():
        data = load_data(path)
        text = get_top_text(key, data)
        bot.send_message(chat_id, text, parse_mode="HTML")