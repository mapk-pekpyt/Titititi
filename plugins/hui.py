import random
import json
from datetime import date
from main import bot, get_display_name

DATA_FILE = "data/hui.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@bot.message_handler(commands=["hui"])
def hui_game(message):
    user = str(message.from_user.id)
    name = get_display_name(message)
    today = str(date.today())

    data = load_data()
    user_data = data.get(user, {"size": 0, "last_play": ""})

    if user_data["last_play"] == today:
        bot.reply_to(message, f"{name} 🍆, ты уже играл сегодня! Твой размер: {user_data['size']} см")
        return

    delta = random.randint(-10, 10)
    user_data["size"] = max(0, user_data["size"] + delta)
    user_data["last_play"] = today
    data[user] = user_data
    save_data(data)

    bot.reply_to(message, f"{name} 🍆, твой член вырос на {delta} см. Теперь он равен {user_data['size']} см")