import os
import telebot
from triggers import TRIGGERS

from plugins import (
    sisi, hui, cartel_war_game, klitor, mut,
    top_plugin, kto, bust_price, cannabis_game,
    minus, say, beer, ban
)

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
    "cartel_war_game": cartel_war_game,
    "ban": ban,
    "delete": delete,
}

# =====================================================
# /my — показать свои размеры/статистику
# =====================================================
@bot.message_handler(commands=["my"])
def my_sizes(message):
    try:
        top_plugin.handle_my(bot, message)
    except Exception as e:
        print(f"Ошибка handle_my: {e}")

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
            try:
                plugin.handle_successful(bot, message)
            except Exception as e:
                print(f"Ошибка handle_successful в {plugin}: {e}")

# =====================================================
# 🏆 CALLBACK КНОПКИ ТОПА
# =====================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def top_callbacks(call):
    try:
        top_plugin.handle_top_callback(bot, call)
    except Exception as e:
        print(f"Ошибка handle_top_callback: {e}")

# =====================================================
# 👮 CHAT MEMBER EVENTS (бан/защита админа)
# =====================================================
@bot.chat_member_handler()
def chat_member(update):
    try:
        ban.handle_chat_member_update(bot, update)
    except Exception as e:
        print(f"Ошибка chat_member: {e}")

# =====================================================
# 🔥 ГЛАВНЫЙ ОБРАБОТЧИК
# =====================================================
@bot.message_handler(content_types=["text", "photo"])
def handle_all(message):
    plugin_called = False

    # ---------- Счёт сообщений для топа ----------
    if message.content_type == "text":
        try:
            top_plugin.count_message(message.chat.id, message.from_user)
        except Exception as e:
            print(f"Ошибка count_message: {e}")

    # ---------- Фото ----------
    if message.content_type == "photo":
        for plugin in PLUGINS.values():
            if hasattr(plugin, "handle"):
                try:
                    plugin.handle(bot, message)
                    plugin_called = True
                except Exception as e:
                    print(f"Ошибка handle фото в {plugin}: {e}")

    # ---------- Текст ----------
    if message.content_type == "text":
        text = message.text
        if not text:
            return

        cmd_raw = text.split()[0].lower()
        cmd = cmd_raw.split("@")[0]

        plugin_name = TRIGGERS.get(cmd)
        if plugin_name and plugin_name in PLUGINS:
            try:
                PLUGINS[plugin_name].handle(bot, message)
                plugin_called = True
            except Exception as e:
                print(f"Ошибка handle команды {plugin_name}: {e}")
        else:
            for plugin in PLUGINS.values():
                if hasattr(plugin, "handle"):
                    try:
                        plugin.handle(bot, message)
                        plugin_called = True
                    except Exception as e:
                        print(f"Ошибка handle текста в {plugin}: {e}")

# =====================================================
# Запуск polling
# =====================================================
if __name__ == "__main__":
    print("Бот запущен...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("Ошибка polling:", e)