import os
import telebot
from core import init_db
from plugins import load_plugins

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Инициализация базы
init_db()

# Загружаем плагины
load_plugins(bot)

# Запуск бота
if __name__=="__main__":
    bot.infinity_polling(skip_pending=True)