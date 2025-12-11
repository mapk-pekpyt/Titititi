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
    top_plugin.handle_my(bot, message)

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

# ---------------------------------------------
# Обработчик callback'ов для рекламы
# ---------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("ads_"))
def ads_callback(call):
    ads.callback(bot, call)

# ------------------------------------------------------------------------
# Главный обработчик команд и текстовых сообщений
# ------------------------------------------------------------------------
@bot.message_handler(content_types=["text", "photo"])
def handle_all_messages(message):
    text = message.text
    if not text:
        return

    text_low = text.lower()
    user_id = str(message.from_user.id)

    # --------------------------
    # Проверка на режим рекламы
    # --------------------------
    data = ads.load_data()
    if user_id in data.get("pending", {}):
        ads.handle(bot, message)
        return

    # --------------------------
    # 1️⃣ Команды с /
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
    # 2️⃣ Текстовые команды без /
    # --------------------------
    for trigger, plugin_name in TRIGGERS.items():
        trig = trigger.replace("/", "").lower()
        if text_low.startswith(trig):
            plugin = PLUGINS.get(plugin_name)
            if plugin and hasattr(plugin, "handle"):
                plugin.handle(bot, message)
            return

    # --------------------------
    # 3️⃣ Нет команд → ничего
    # --------------------------
    return

# ---------------------------------------------
# Старт
# ---------------------------------------------
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()