import telebot
import os
from triggers import TRIGGERS
from plugins import PLUGINS  # теперь все плагины через PLUGINS

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

BOT_USERNAME = bot.get_me().username.lower()

# =====================================================
# /my – личные размеры
# =====================================================
@bot.message_handler(commands=["my"])
def my_sizes(message):
    PLUGINS["top_plugin"].handle_my(bot, message)

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
# 🏆 CALLBACK КНОПКИ ТОПА
# =====================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def top_callbacks(call):
    PLUGINS["top_plugin"].handle_top_callback(bot, call)

# =====================================================
# 💬 СЧЁТЧИК СООБЩЕНИЙ (для топа общения)
# =====================================================
@bot.message_handler(func=lambda m: True, content_types=["text"])
def count_messages(message):
    try:
        PLUGINS["top_plugin"].count_message(message.chat.id, message.from_user)
    except:
        pass

# =====================================================
# 🔥 ГЛАВНЫЙ ОБРАБОТЧИК (текст + фото)
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
# Запуск бота
# =====================================================
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()