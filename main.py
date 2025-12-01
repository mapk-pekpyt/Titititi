import os
import importlib
from telebot import TeleBot
from core import init_db

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")
bot = TeleBot(TOKEN, parse_mode="HTML")

# === Инициализация базы ===
init_db()

# === Загрузка всех плагинов ===
def load_plugins():
    for filename in os.listdir("plugins"):
        if filename.endswith(".py") and filename != "__init__.py":
            modulename = filename[:-3]
            importlib.import_module(f"plugins.{modulename}")

load_plugins()

# === Запуск бота ===
if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)