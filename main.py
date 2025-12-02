from telebot import TeleBot, types
from core import init_db, db_execute
import importlib
import os

TOKEN = "токен_бота_от_ботхоста"
bot = TeleBot(TOKEN)

# инициализация базы
init_db()

# админ
ADMIN = "Sugar_Daddy_rip"

# загрузка плагинов
def load_plugins(bot):
    for filename in os.listdir("plugins"):
        if filename.endswith(".py") and filename != "__init__.py":
            modulename = filename[:-3]
            module = importlib.import_module(f"plugins.{modulename}")
            if hasattr(module, "setup"):
                module.setup(bot)

load_plugins(bot)

# команда /help
@bot.message_handler(commands=["help"])
def help_cmd(message):
    text = (
        "📜 Список команд:\n"
        "/sisi - игра про грудь\n"
        "/hui - игра про хуй\n"
        "/klitor - игра про клитор\n"
        "/top - топ игроков по каждой игре\n"
        "/mut x - выдать мут пользователю (платно, x = минуты)\n"
        "/price x - установить цену 1 минуты мута (только админ)\n"
    )
    bot.send_message(message.chat.id, text)

bot.infinity_polling()