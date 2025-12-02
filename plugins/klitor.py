# plugins/klitor.py
import os
import json
import random
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_FILE = "data/klitor.json"
TZ = ZoneInfo("Europe/Berlin")
EMOJI = "💎"

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
    entry = data.get(uid, {"name": name, "size_mm": 0, "last_date": ""})
    entry["name"] = name

    if entry.get("last_date") == today:
        bot.reply_to(message, f"{name} {EMOJI}, ты уже играл сегодня 😅\nТекущий клитор — <b>{entry['size_mm']/10:.1f}</b> см")
        return

    delta = random.randint(-10, 10)  # mm
    if entry["size_mm"] + delta < 0:
        delta = -entry["size_mm"]
    entry["size_mm"] = entry["size_mm"] + delta
    entry["last_date"] = today
    data[uid] = entry
    save_data(data)

    sign = f"{delta:+d}"
    bot.reply_to(message, f"{name} {EMOJI}, твой клитор вырос на <b>{sign}</b> мм, теперь он равен <b>{entry['size_mm']/10:.1f}</b> см")