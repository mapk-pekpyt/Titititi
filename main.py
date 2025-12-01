import os
import importlib
from telebot import TeleBot

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")
bot = TeleBot(TOKEN, parse_mode="HTML")

# === Загрузка всех плагинов из папки plugins ===
def load_plugins(bot_instance):
    import plugins  # сам пакет
    for filename in os.listdir("plugins"):
        if filename.endswith(".py") and filename != "__init__.py":
            modulename = filename[:-3]
            importlib.import_module(f"plugins.{modulename}")

load_plugins(bot)

# === Запуск бота ===
if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)