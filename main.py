import os
import importlib
from telebot import TeleBot, types

# BotHost автоматически подставляет токен
bot = TeleBot(token=os.environ.get("BOT_TOKEN"))

# Админ бота
ADMIN_USERNAME = "@Sugar_Daddy_rip"

# Функция для загрузки всех плагинов
def load_plugins(bot):
    plugin_dir = "plugins"
    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            modulename = filename[:-3]
            module = importlib.import_module(f"{plugin_dir}.{modulename}")
            if hasattr(module, "register"):
                module.register(bot)
    print("✅ Все плагины загружены")

# Старт бота
if __name__ == "__main__":
    load_plugins(bot)
    print("✅ Бот запущен, ожидаю события...")
    bot.infinity_polling()