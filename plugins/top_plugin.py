import json
import os

# Пути к файлам плагинов
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

# Загрузка данных из JSON
def load_data(file):
    if not os.path.exists(file):
        return {}
    try:
        with open(file, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return {}

# Форматирование топа по конкретной игре
def format_top_for_game(game, chat_id):
    data = load_data(FILES[game])
    chat_id = str(chat_id)

    if chat_id not in data or not data[chat_id]:
        return f"Тут ещё никто не играл в {game} {EMOJIS[game]} 😢"

    # сортировка по размеру (sisi и hui — size, klitor — size_mm)
    if game == "klitor":
        sorted_data = sorted(data[chat_id].items(), key=lambda x: x[1].get("size_mm",0), reverse=True)
    else:
        sorted_data = sorted(data[chat_id].items(), key=lambda x: x[1].get("size",0), reverse=True)

    text = f"🏆 ТОП {EMOJIS[game]} {game}:\n"
    for i, (user_id, info) in enumerate(sorted_data[:5],1):
        name = info.get("name", str(user_id))
        size = info.get("size") if game != "klitor" else info.get("size_mm") / 10  # делаем мм в см если нужно
        text += f"{i}. {name} — {size}\n"

    return text

# Главная функция для команды /top
def handle(bot, message):
    chat_id = message.chat.id
    for game in FILES.keys():
        bot.send_message(chat_id, format_top_for_game(game, chat_id))

# Функция для /my — показывает размеры пользователя
def handle_my(bot, message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    text = ""
    for game, file in FILES.items():
        data = load_data(file)
        if chat_id in data and user_id in data[chat_id]:
            info = data[chat_id][user_id]
            size = info.get("size") if game != "klitor" else info.get("size_mm") / 10
            text += f"{EMOJIS[game]} {game}: {size}\n"
        else:
            text += f"{EMOJIS[game]} {game}: ещё не играл\n"
    bot.send_message(message.chat.id, text)