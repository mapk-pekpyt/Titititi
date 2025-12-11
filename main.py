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
# /my
# ---------------------------------------------
@bot.message_handler(commands=["my"])
def my_sizes(message):
    top_plugin.handle_my(bot, message)
    ads.attach_ad(bot, message.chat.id)

# ---------------------------------------------
# Stars: pre-checkout
# ---------------------------------------------
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# ---------------------------------------------
# Stars: успешная оплата
# ---------------------------------------------
@bot.message_handler(content_types=['successful_payment'])
def payment_handler(message):
    for name, plugin in PLUGINS.items():
        if hasattr(plugin, "handle_successful"):
            plugin.handle_successful(bot, message)

    # Лото
    try:
        stars = 0
        if hasattr(message, "successful_payment"):
            stars = message.successful_payment.total_amount // 100
        loto.add_stars(message.chat.id, message.from_user.id, stars)
        loto.check_loto(bot, message.chat.id)
    except:
        pass

# ---------------------------------------------
# Callback рекламы
# ---------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("ads_"))
def ads_callback(call):
    ads.callback(bot, call)

# ---------------------------------------------
# Обработка текста и фото
# ---------------------------------------------
@bot.message_handler(content_types=["text", "photo"])
def handle_all_messages(message):

    # 1️⃣ если юзер в процессе покупки рекламы
    data = ads.load()
    user_id = str(message.from_user.id)
    if user_id in data.get("pending", {}):
        ads.handle(bot, message)
        return

    # 2️⃣ если это рекламные команды
    text = message.text.lower() if message.text else ""
    if text.startswith("/buy_ads"):
        ads.handle_buy(bot, message)
        return

    if text.startswith("/priser"):
        ads.handle_priser(bot, message)
        return

    # 3️⃣ обычные плагины
    cmd_raw = text.split()[0] if text else ""
    if cmd_raw.startswith("/"):
        cmd = cmd_raw.split("@")[0]
        plugin_name = TRIGGERS.get(cmd)
        if plugin_name:
            plugin = PLUGINS.get(plugin_name)
            if plugin and hasattr(plugin, "handle"):
                plugin.handle(bot, message)
                ads.attach_ad(bot, message.chat.id)
            return

    for trigger, plugin_name in TRIGGERS.items():
        trig = trigger.replace("/", "").lower()
        if text.startswith(trig):
            plugin = PLUGINS.get(plugin_name)
            if plugin and hasattr(plugin, "handle"):
                plugin.handle(bot, message)
                ads.attach_ad(bot, message.chat.id)
            return


print("Бот запущен...")
bot.infinity_polling()