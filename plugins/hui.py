import random
import datetime
from main import bot, db_execute, get_display_name

TABLE = "hui"

db_execute(f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    chat_id TEXT,
    user_id TEXT,
    size_cm INTEGER,
    last_date TEXT,
    PRIMARY KEY(chat_id, user_id)
)
""")

def change_size(chat_id, user_id):
    today = datetime.date.today().isoformat()
    row = db_execute(f"SELECT size_cm, last_date FROM {TABLE} WHERE chat_id=? AND user_id=?", (str(chat_id), str(user_id)), fetch=True)
    if row:
        last_date = row[0]["last_date"]
        current_size = row[0]["size_cm"]
    else:
        last_date = None
        current_size = 0

    if last_date == today:
        return 0, current_size

    delta = random.randint(-10,10)
    new_size = max(current_size + delta, 0)
    db_execute(f"INSERT OR REPLACE INTO {TABLE}(chat_id, user_id, size_cm, last_date) VALUES(?,?,?,?)",
               (str(chat_id), str(user_id), new_size, today))
    return delta, new_size

@bot.message_handler(commands=['hui'])
def cmd_hui(m):
    chat_id, user_id = m.chat.id, m.from_user.id
    delta, new_size = change_size(chat_id, user_id)
    name = get_display_name(chat_id, user_id)

    if delta == 0:
        bot.reply_to(m, f"Ой, а ты уже пробовал сегодня 😅\nТекущий хуй — <b>{new_size}</b> см 🍌")
    else:
        sign = f"{delta:+d}"
        bot.reply_to(m, f"🍌 {name}, твой хуй вырос на <b>{sign}</b> см, теперь — <b>{new_size}</b> см 🍌")