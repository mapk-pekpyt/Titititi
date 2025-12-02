import json
import os

DATA_FILES = {
    "sisi": "data/sisi.json",
    "hui": "data/hui.json",
    "klitor": "data/klitor.json"
}

def handle(bot, message):
    chat_id = message.chat.id
    for name, file in DATA_FILES.items():
        if not os.path.exists(file):
            bot.send_message(chat_id, f"{name} топ: пока пусто 😅")
            continue
        with open(file, "r") as f:
            data = json.load(f)
        sorted_users = sorted(data.items(), key=lambda x: x[1]["size"], reverse=True)
        text = f"🏆 {name} Топ 5:\n"
        for i, (uid, info) in enumerate(sorted_users[:5], start=1):
            text += f"{i}. {info.get('size',0)} — {uid}\n"
        bot.send_message(chat_id, text)