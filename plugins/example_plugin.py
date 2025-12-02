# plugins/example_plugin.py
from main import bot

@bot.message_handler(commands=['test', 'ping'])
def cmd_test(m):
    bot.reply_to(m, "plugin ok ✅")