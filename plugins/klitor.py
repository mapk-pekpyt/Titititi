from core import db_execute, today_date, random_delta
from main import bot

def change_klitor(chat_id, user_id):
    today = today_date()
    row = db_execute("SELECT size,last_date FROM klitor WHERE chat_id=? AND user_id=?", (str(chat_id), str(user_id)), fetch=True)
    if row:
        size, last_date = row[0]["size"], row[0]["last_date"]
        if last_date == today:
            return 0, size
    else:
        size = 0

    delta = random_delta(-10,10)
    new_size = max(size + delta, 0)
    db_execute("INSERT OR REPLACE INTO klitor(chat_id,user_id,size,last_date) VALUES (?,?,?,?)",
               (str(chat_id), str(user_id), new_size, today))
    return delta, new_size

@bot.message_handler(commands=['klitor'])
def cmd_klitor(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    delta, new_size = change_klitor(chat_id, user_id)
    if delta == 0:
        bot.reply_to(message, f"Упс, ты уже играл сегодня 😅 Твой размер: {new_size/10:.1f} см")
    else:
        bot.reply_to(message, f"💦 Твой клитор вырос на {delta} мм, теперь он: {new_size/10:.1f} см")