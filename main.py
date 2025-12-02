import os
import importlib
from telebot import TeleBot

from core import db_execute

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN не установлен!")

bot = TeleBot(TOKEN)

# Загрузка всех плагинов
def load_plugins():
    plugins_dir = "plugins"
    for filename in os.listdir(plugins_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            modulename = filename[:-3]
            module = importlib.import_module(f"{plugins_dir}.{modulename}")
            if hasattr(module, "setup"):
                module.setup(bot)

# Инициализация базы
db_execute("""
CREATE TABLE IF NOT EXISTS game_data (
    chat_id TEXT,
    user_id TEXT,
    game TEXT,
    value REAL,
    last_play TEXT,
    PRIMARY KEY(chat_id, user_id, game)
)
""")

load_plugins()

print("Бот запущен...")
bot.infinity_polling()