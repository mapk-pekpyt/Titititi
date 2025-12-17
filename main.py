import os
import telebot

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda m: True)
def echo(m):
    bot.reply_to(m, "Привет! Бот живой.")

try:
    print("Запуск polling...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
except Exception as e:
    print("Ошибка polling:", e)