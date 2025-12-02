import telebot
from triggers import TRIGGERS
from plugins import sisi, hui, klitor, mut, top_plugin, kto

import os

# Токен берем из BOTHOST (или .env, если понадобится)
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Словарь для подключения плагинов
PLUGINS = {
    "sisi": sisi,
    "hui": hui,
    "klitor": klitor,
    "mut": mut,
    "top_plugin": top_plugin,
    "kto": kto,
}

# Регистрируем бота и слушаем все сообщения
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text
    if not text:
        return
    cmd = text.split()[0].lower()  # первая "словная" часть команды
    plugin_name = TRIGGERS.get(cmd)
    if plugin_name:
        plugin = PLUGINS.get(plugin_name)
        if plugin:
            plugin.handle(bot, message)  # вызываем плагин

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()