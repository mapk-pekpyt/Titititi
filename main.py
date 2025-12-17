import telebot
import os
from triggers import TRIGGERS
from plugins import sisi, hui, klitor, mut, top_plugin, kto, bust_price, cannabis_game, minus, say, beer

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
    "bust_price": bust_price,
    "cannabis_game": cannabis_game,
    "minus": minus,
    "say": say,
    "beer": beer,
}

# =====================================================
# /my
# =====================================================
@bot.message_handler(commands=["my"])
def my_sizes(message):
    top_plugin.handle_my(bot, message)

# =====================================================
# ⭐ Stars pre-checkout
# =====================================================
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# =====================================================
# 💸 Успешная оплата
# =====================================================
@bot.message_handler(content_types=['successful_payment'])
def payment_handler(message):
    for plugin in PLUGINS.values():
        if hasattr(plugin, "handle_successful"):
            plugin.handle_successful(bot, message)

# =====================================================
# 🏆 CALLBACK КНОПКИ ТОПА (ВАЖНО)
# =====================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def top_callbacks(call):
    top_plugin.handle_top_callback(bot, call)

# =====================================================
# 💬 СЧЁТЧИК СООБЩЕНИЙ (для топа общения)
# =====================================================
@bot.message_handler(func=lambda m: True, content_types=["text"])
def count_messages(message):
    try:
        top_plugin.count_message(message.chat.id, message.from_user)
    except:
        pass

# =====================================================
# 🔥 ГЛАВНЫЙ ОБРАБОТЧИК
# =====================================================
@bot.message_handler(content_types=["text", "photo"])
def handle_all(message):
    plugin_called = False

    # ---------- ФОТО ----------
    if message.content_type == "photo":
        for plugin in PLUGINS.values():
            if hasattr(plugin, "handle"):
                plugin.handle(bot, message)
                plugin_called = True

    # ---------- ТЕКСТ ----------
    else:
        text = message.text
        if not text:
            return

        cmd_raw = text.split()[0].lower()
        cmd = cmd_raw.split("@")[0]

        plugin_name = TRIGGERS.get(cmd)

        if plugin_name and plugin_name in PLUGINS:
            PLUGINS[plugin_name].handle(bot, message)
            plugin_called = True
        else:
            # обычный текст → на все плагины
            for plugin in PLUGINS.values():
                if hasattr(plugin, "handle"):
                    plugin.handle(bot, message)
                    plugin_called = True

# =====================================================
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()