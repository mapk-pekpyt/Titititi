import os
import importlib
import telebot
from core import init_db

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Инициализация БД
init_db()

# Автозагрузка плагинов из папки plugins
PLUGIN_FOLDER = "plugins"
for filename in os.listdir(PLUGIN_FOLDER):
    if filename.endswith(".py") and filename != "__init__.py":
        modulename = filename[:-3]
        importlib.import_module(f"{PLUGIN_FOLDER}.{modulename}")

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен! 🚀")
    bot.infinity_polling(skip_pending=True)