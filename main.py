import telebot
import os
from triggers import TRIGGERS
from plugins import sisi, hui, klitor, mut, top_plugin, kto, bust_price, loto, minus, say

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

BOT_USERNAME = bot.get_me().username.lower()

# ❗ ads УБРАН из PLUGINS
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
}

# ---------------------------------------------
# /my
# ---------------------------------------------
@bot.message_handler(commands=["my"])
def my_sizes(message):
    top_plugin.handle_my(bot, message)

# ---------------------------------------------
# Stars pre-checkout
# ---------------------------------------------
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# ---------------------------------------------
# Успешная оплата
# ---------------------------------------------
@bot.message_handler(content_types=['successful_payment'])
def payment_handler(message):
    for plugin in PLUGINS.values():
        if hasattr(plugin, "handle_successful"):
            plugin.handle_successful(bot, message)

    # Лото
    try:
        stars = int(message.successful_payment.total_amount) // 100
        loto.add_stars(message.chat.id, message.from_user.id, stars)
        loto.check_loto(bot, message.chat.id)
    except:
        pass

# ---------------------------------------------
# Команды рекламы (ТОЛЬКО ЯВНЫЕ)
# ---------------------------------------------
@bot.message_handler(commands=["buy_ads"])
def buy_ads_cmd(msg):
    ads.handle_buy(bot, msg)

@bot.message_handler(commands=["priser"])
def price_cmd(msg):
    ads.handle_price(bot, msg)

# ---------------------------------------------
# Callback рекламы
# ---------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    ads.handle_callback(bot, call)

# ---------------------------------------------
# ГЛАВНЫЙ ОБРАБОТЧИК (без вмешательства рекламы)
# ---------------------------------------------
@bot.message_handler(content_types=["text", "photo"])
def handle_all(message):
    plugin_called = False

    # --- Фото ---
    if message.content_type == "photo":
        for plugin in PLUGINS.values():
            if hasattr(plugin, "handle"):
                plugin.handle(bot, message)
                plugin_called = True

    # --- Текст ---
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
            # обычный текст
            for plugin in PLUGINS.values():
                if hasattr(plugin, "handle"):
                    plugin.handle(bot, message)
                    plugin_called = True

    # -----------------------------------------
    # РЕКЛАМА = ПОСЛЕ ВСЕГО, 1 РАЗ
    # -----------------------------------------
    if plugin_called:
        try:
            ads.send_random_ads(bot, message.chat.id)
        except:
            pass

# ---------------------------------------------
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()