from core import db_execute, today_date, random_delta
from main import bot

def change_boobs(chat_id, user_id):
    today = today_date()
    row = db_execute("SELECT size,last_date FROM boobs WHERE chat_id=? AND user_id=?", (str(chat_id), str(user_id)), fetch=True)
    if row:
        size, last_date = row[0]["size"], row[0]["last_date"]
        if last_date == today:
            return 0, size
    else:
        size = 0

    delta = random_delta(-10,10)
    new_size = max(size + delta, 0)
    db_execute("INSERT OR REPLACE INTO boobs(chat_id,user_id,size,last_date) VALUES (?,?,?,?)",
               (str(chat_id), str(user_id), new_size, today))
    return delta, new_size

@bot.message_handler(commands=['sisi'])
def cmd_sisi(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    delta, new_size = change_boobs(chat_id, user_id)
    if delta == 0:
        bot.reply_to(message, f"Упс, ты уже играл сегодня 😅 Твой размер груди: {new_size}")
    else:
        bot.reply_to(message, f"🍒 Твой размер груди вырос на {delta}, теперь он: {new_size}")