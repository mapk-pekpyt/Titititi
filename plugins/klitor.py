# plugins/klitor.py
import random
from main import bot
from core import db_execute, today_date

GAME_TABLE = "klitor"

@bot.message_handler(commands=['klitor'])
def cmd_klitor(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    today = today_date()

    row = db_execute(f"SELECT size, last_date FROM {GAME_TABLE} WHERE chat_id=? AND user_id=?", (chat_id, user_id), fetch=True)
    if row:
        mm = row[0]["size"]
        last = row[0]["last_date"]
    else:
        mm = 0
        last = None

    if last == today:
        bot.reply_to(message, f"Ой, уже играл сегодня 😅\nТекущий клитор — <b>{mm/10:.1f}</b> см 🍆")
        return

    delta = random.randint(-10, 10)  # mm
    new_mm = max(0, mm + delta)

    db_execute(f"INSERT OR REPLACE INTO {GAME_TABLE} (chat_id, user_id, size, last_date) VALUES (?,?,?,?)",
               (chat_id, user_id, new_mm, today))

    name = (message.from_user.first_name or message.from_user.username or "Игрок")
    sign = f"{delta:+d}"
    delta_cm = round(delta/10, 1)
    bot.reply_to(message, f"🍆 {name}, твой клитор вырос на <b>{sign}</b> мм ({delta_cm} см), теперь — <b>{new_mm/10:.1f}</b> см 🍆")