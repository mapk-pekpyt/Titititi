from main import bot, get_display_name
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

@bot.message_handler(commands=["top"])
def top_all(message):
    for key, file in FILES.items():
        try:
            with open(file, "r") as f:
                data = json.load(f)
        except:
            data = {}

        # сортировка по размеру
        if key == "klitor":
            sorted_data = sorted(data.items(), key=lambda x: x[1]["size_mm"], reverse=True)
        else:
            sorted_data = sorted(data.items(), key=lambda x: x[1]["size"], reverse=True)

        text = f"🏆 Топ {EMOJIS[key]}:\n"
        for i, (user_id, info) in enumerate(sorted_data[:5], 1):
            name = info.get("name", str(user_id))
            size = info.get("size") if key != "klitor" else info.get("size_mm")/10
            text += f"{i}. {name} — {size}\n"

        bot.send_message(message.chat.id, text)