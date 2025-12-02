# plugins/sisi.py
import random
from main import bot
from core import db_execute, today_date

TABLE = "boobs"

@bot.message_handler(commands=['sisi'])
def cmd_sisi(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    today = today_date()

    row = db_execute(f"SELECT size, last_date FROM {TABLE} WHERE chat_id=? AND user_id=?", (chat_id, user_id), fetch=True)
    if row:
        size = int(row[0]["size"])
        last = row[0]["last_date"]
    else:
        size = 0
        last = None

    if last == today:
        bot.reply_to(message, f"Ой, а ты уже пробовал сегодня 😅\nТвой текущий размер груди — <b>{size}</b> 🍒")
        return

    delta = random.randint(-10, 10)
    new_size = max(0, size + delta)

    db_execute(f"INSERT OR REPLACE INTO {TABLE} (chat_id, user_id, size, last_date) VALUES (?,?,?,?)",
               (chat_id, user_id, new_size, today))

    name = message.from_user.first_name or message.from_user.username or "Игрок"
    sign = f"{delta:+d}"
    bot.reply_to(message, f"🍒 {name}, твой размер груди вырос на <b>{sign}</b>, теперь твой размер груди — <b>{new_size}</b> 🍒")