# main.py
import os
import importlib
import sys
from telebot import TeleBot
from core import init_db

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in environment variables")

bot = TeleBot(TOKEN, parse_mode="HTML")

# Инициализация БД (создаст таблицы)
init_db()

# Загружаем плагины — после создания bot
def load_plugins():
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    if not os.path.isdir(plugins_dir):
        return
    for filename in os.listdir(plugins_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            modulename = filename[:-3]
            try:
                importlib.import_module(f"plugins.{modulename}")
                print(f"[main] plugin loaded: {modulename}")
            except Exception as e:
                print(f"[main] failed to load plugin {modulename}: {e}", file=sys.stderr)

load_plugins()

if __name__ == "__main__":
    print("[main] bot started")
    bot.infinity_polling(skip_pending=True)