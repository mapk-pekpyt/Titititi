import random
import datetime
from main import bot, db_execute, get_display_name

TABLE = "klitor"

db_execute(f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    chat_id TEXT,
    user_id TEXT,
    size_mm INTEGER,
    last_date TEXT,
    PRIMARY KEY(chat_id, user_id)
)
""")

def change_size(chat_id, user_id):
    today = datetime.date.today().isoformat()
    row = db_execute(f"SELECT size_mm, last_date FROM {TABLE} WHERE chat_id=? AND user_id=?", (str(chat_id), str(user_id)), fetch=True)
    if row:
        last_date = row[0]["last_date"]
        current_size = row[0]["size_mm"]
    else:
        last_date = None
        current_size = 0

    if last_date == today:
        return 0, current_size

    delta = random.randint(-10,10)
    new_size = max(current_size + delta, 0)
    db_execute(f"INSERT OR REPLACE INTO {TABLE}(chat_id, user_id, size_mm, last_date) VALUES(?,?,?,?)",
               (str(chat_id), str(user_id), new_size, today))
    return delta, new_size

@bot.message_handler(commands=['klitor'])
def cmd_klitor(m):
    chat_id, user_id = m.chat.id, m.from_user.id
    delta, new_size_mm = change_size(chat_id, user_id)
    name = get_display_name(chat_id, user_id)
    new_size_cm = round(new_size_mm / 10, 1)  # отображаем в см с одной десятичной

    if delta == 0:
        bot.reply_to(m, f"Ой, а ты уже пробовал сегодня 😅\nТекущий клитор — <b>{new_size_cm}</b> см 🍆")
    else:
        sign = f"{delta:+d}"
        delta_cm = round(delta/10,1)
        bot.reply_to(m, f"🍆 {name}, твой клитор вырос на <b>{sign} мм</b> ({delta_cm} см), теперь — <b>{new_size_cm}</b> см 🍆")