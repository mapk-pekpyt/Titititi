import telebot
import os
from triggers import TRIGGERS
from plugins import sisi, hui, klitor, mut, top_plugin, kto

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

BOT_USERNAME = bot.get_me().username.lower()

PLUGINS = {
    "sisi": sisi,
    "hui": hui,
    "klitor": klitor,
    "mut": mut,
    "top_plugin": top_plugin,
    "kto": kto,
}

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text
    if not text:
        return

    cmd_raw = text.split()[0].lower()

    # поддержка /cmd@username
    if "@" in cmd_raw:
        cmd = cmd_raw.split("@")[0]
    else:
        cmd = cmd_raw

    plugin_name = TRIGGERS.get(cmd)
    if not plugin_name:
        return

    plugin = PLUGINS.get(plugin_name)
    if not plugin:
        return

    if hasattr(plugin, "handle"):
        plugin.handle(bot, message)
    else:
        print(f"❗ Плагин {plugin_name} не имеет функции handle()")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()