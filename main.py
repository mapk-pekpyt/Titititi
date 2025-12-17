import os
import telebot
from triggers import TRIGGERS
from plugins import (
    sisi, hui, klitor, mut, top_plugin, kto, bust_price,
    cannabis_game, minus, say, beer
)

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("Ошибка: BOT_TOKEN не найден")
    exit(1)

# Инициализация бота
try:
    bot = telebot.TeleBot(TOKEN)
    BOT_USERNAME = bot.get_me().username.lower()
    print(f"Бот @{BOT_USERNAME} запущен")
except Exception as e:
    print("Ошибка при инициализации бота:", e)
    exit(1)

# Словарь всех плагинов
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

# =======================
# /my — показать свои размеры
# =======================
@bot.message_handler(commands=["my"])
def my_sizes(message):
    try:
        top_plugin.handle_my(bot, message)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

# =======================
# Stars pre-checkout (оплата)
# =======================
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# =======================
# Успешная оплата
# =======================
@bot.message_handler(content_types=['successful_payment'])
def payment_handler(message):
    for plugin in PLUGINS.values():
        if hasattr(plugin, "handle_successful"):
            try:
                plugin.handle_successful(bot, message)
            except Exception as e:
                print(f"Ошибка handle_successful в {plugin}: {e}")

# =======================
# Callback топа
# =======================
@bot.callback_query_handler(func=lambda call: call.data.startswith("top_"))
def top_callbacks(call):
    try:
        top_plugin.handle_top_callback(bot, call)
    except Exception as e:
        print(f"Ошибка handle_top_callback: {e}")
        call.message.reply(f"Ошибка обработки топа: {e}")

# =======================
# Счётчик сообщений для топа общения
# =======================
@bot.message_handler(func=lambda m: True, content_types=["text"])
def count_messages(message):
    try:
        top_plugin.count_message(message.chat.id, message.from_user)
    except Exception as e:
        print(f"Ошибка count_message: {e}")

# =======================
# Главный обработчик текста и фото
# =======================
@bot.message_handler(content_types=["text", "photo"])
def handle_all(message):
    plugin_called = False

    # Фото
    if message.content_type == "photo":
        for plugin in PLUGINS.values():
            if hasattr(plugin, "handle"):
                try:
                    plugin.handle(bot, message)
                    plugin_called = True
                except Exception as e:
                    print(f"Ошибка handle фото в {plugin}: {e}")

    # Текст
    else:
        text = message.text
        if not text:
            return

        cmd_raw = text.split()[0].lower()
        cmd = cmd_raw.split("@")[0]

        plugin_name = TRIGGERS.get(cmd)

        # Если команда есть в триггерах — плагин по ней
        if plugin_name and plugin_name in PLUGINS:
            try:
                PLUGINS[plugin_name].handle(bot, message)
                plugin_called = True
            except Exception as e:
                print(f"Ошибка handle команды {plugin_name}: {e}")
                bot.reply_to(message, f"Ошибка: {e}")
        else:
            # Иначе пробуем отправить на все плагины
            for plugin in PLUGINS.values():
                if hasattr(plugin, "handle"):
                    try:
                        plugin.handle(bot, message)
                        plugin_called = True
                    except Exception as e:
                        print(f"Ошибка handle текста в {plugin}: {e}")

# =======================
# Запуск бота
# =======================
if __name__ == "__main__":
    print("Запуск polling...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("Ошибка polling:", e)