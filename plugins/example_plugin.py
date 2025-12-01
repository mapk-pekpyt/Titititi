from main import bot
from core import today_date, random_delta, db_execute

@bot.message_handler(commands=['ping'])
def cmd_ping(message):
    bot.reply_to(message, f"Pong! Сегодня: {today_date()}")