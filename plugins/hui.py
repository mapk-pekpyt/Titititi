# plugins/hui.py
import os
import json
import random
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_FILE = "data/hui.json"
TZ = ZoneInfo("Europe/Berlin")
EMOJI = "🍆"

def ensure_data_dir():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

def load_data():
    ensure_data_dir()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_display_name_from_user(user):
    if getattr(user, "username", None):
        return f"@{user.username}"
    return user.first_name or "Пользователь"

def berlin_today_iso():
    return datetime.now(TZ).date().isoformat()

def handle(bot, message):
    user = message.from_user
    uid = str(user.id)
    name = get_display_name_from_user(user)
    today = berlin_today_iso()

    data = load_data()
    entry = data.get(uid, {"name": name, "size": 0, "last_date": ""})
    entry["name"] = name

    if entry.get("last_date") == today:
        bot.reply_to(message, f"{name} {EMOJI}, ты уже играл сегодня 😅\nТекущий хуй — <b>{entry['size']}</b> см")
        return

    delta = random.randint(-10, 10)
    if entry["size"] + delta < 0:
        delta = -entry["size"]
    entry["size"] = entry["size"] + delta
    entry["last_date"] = today
    data[uid] = entry
    save_data(data)

    sign = f"{delta:+d}"
    bot.reply_to(message, f"{name} {EMOJI}, твой хуй вырос на <b>{sign}</b> см, теперь он равен <b>{entry['size']}</b> см")