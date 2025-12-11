import telebot
import os
from triggers import TRIGGERS
from plugins import sisi, hui, klitor, mut, top_plugin, kto, bust_price, loto, minus, say, ads

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
    "loto": loto,
    "minus": minus,
    "say": say,
    "ads": ads
}

# ---------------------------------------------
# Обработчик /my
# ---------------------------------------------
@bot.message_handler(commands=["my"])
def my_sizes(message):
    from plugins import top_plugin
    top_plugin.handle_my(bot, message)


# ---------------------------------------------
# Запуск рекламы /ads
# ---------------------------------------------
@bot.message_handler(commands=["ads"])
def ads_start(message):
    ads.start(bot, message)


# ---------------------------------------------
# Stars: pre-checkout
# ---------------------------------------------
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(pre_checkout_query):
    try:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        print("❌ Ошибка pre-checkout:", e)


# ---------------------------------------------
# Stars: успешная оплата
# ---------------------------------------------
@bot.message_handler(content_types=['successful_payment'])
def payment_handler(message):
    # обработка всех плагинов
    for name, plugin in PLUGINS.items():
        try:
            if hasattr(plugin, "handle_successful"):
                plugin.handle_successful(bot, message)
        except Exception as e:
            print(f"❌ Ошибка в обработке оплаты у {name}: {e}")

    # Лото обрабатываем отдельно
    try:
        stars = 0
        if hasattr(message, "successful_payment"):
            stars = message.successful_payment.total_amount // 100

        chat_id = message.chat.id
        user_id = message.from_user.id

        if stars > 0:
            loto.add_stars(chat_id, user_id, stars)
            loto.check_loto(bot, chat_id)

    except Exception as e:
        print(f"❌ Ошибка при добавлении звезд в лото: {e}")


# ------------------------------------------------------------------------
# Перехват сообщений рекламного процесса
# ------------------------------------------------------------------------
@bot.message_handler(content_types=["text", "photo"])
def ads_interceptor(message):
    user_id = str(message.from_user.id)
    data = ads.load_data()

    # Если человек внутри рекламного процесса → отправляем в ads.handle
    if user_id in data.get("pending", {}):
        ads.handle(bot, message)
        return

    # Иначе — обычная логика
    return handle_all_messages(message)


# ------------------------------------------------------------------------
# Главный обработчик команд + текстовых команд
# ------------------------------------------------------------------------
def handle_all_messages(message):
    text = message.text
    if not text:
        return

    text_low = text.lower().strip()

    # --------------------------
    # 1️⃣ Если команда начинается с /cmd
    # --------------------------
    cmd_raw = text_low.split()[0]

    if cmd_raw.startswith("/"):
        if "@" in cmd_raw:
            cmd = cmd_raw.split("@")[0]
        else:
            cmd = cmd_raw

        plugin_name = TRIGGERS.get(cmd)
        if plugin_name:
            plugin = PLUGINS.get(plugin_name)
            if plugin and hasattr(plugin, "handle"):
                plugin.handle(bot, message)
            return

    # --------------------------
    # 2️⃣ Текстовые команды без слэша
    # --------------------------
    first_word = text_low.split()[0]  # анализируем первое слово
    for trigger, plugin_name in TRIGGERS.items():
        pure_trigger = trigger.replace("/", "").lower()

        # пример: pure_trigger="sisi", first_word="сиськи" → ок
        if pure_trigger in first_word:
            plugin = PLUGINS.get(plugin_name)
            if plugin and hasattr(plugin, "handle"):
                plugin.handle(bot, message)
            return

    # Если команды нет – игнорируем
    return


# ---------------------------------------------
# Старт
# ---------------------------------------------
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()