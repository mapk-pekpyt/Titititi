# main.py
import os
import importlib
from telebot import TeleBot
from core import init_db

TOKEN = os.environ.get("BOT_TOKEN", None)
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables")

bot = TeleBot(TOKEN, parse_mode="HTML")

# Инициализация базы (создаёт все таблицы)
init_db()

# Загружаем плагины из каталога plugins
def load_plugins():
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    for filename in os.listdir(plugins_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            modulename = filename[:-3]
            importlib.import_module(f"plugins.{modulename}")

# загружаем
load_plugins()

# Запуск бота
if __name__ == "__main__":
    print("Bot started")
    bot.infinity_polling(skip_pending=True)