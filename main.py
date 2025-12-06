import telebot
import os
from triggers import TRIGGERS
from plugins import sisi, hui, klitor, mut, top_plugin, kto, bust_price, loto

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
}

# Обработчик /my
@bot.message_handler(commands=["my"])
def my_sizes(message):
    from plugins import top_plugin
    top_plugin.handle_my(bot, message)


# ---------------------------------------------
# ✅ ОБЯЗАТЕЛЬНО: обработчик pre-checkout для Stars
# ---------------------------------------------
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(pre_checkout_query):
    try:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        print("❌ Ошибка pre-checkout:", e)


# -----------------------------------------------------
# 🔥 ГЛАВНЫЙ ОБЩИЙ ОБРАБОТЧИК УСПЕШНОЙ ОПЛАТЫ ДЛЯ ВСЕХ
# -----------------------------------------------------
@bot.message_handler(content_types=['successful_payment'])
def payment_handler(message):
    for name, plugin in PLUGINS.items():
        try:
            if hasattr(plugin, "handle_successful"):
                plugin.handle_successful(bot, message)
        except Exception as e:
            print(f"❌ Ошибка в обработке оплаты у {name}: {e}")


# ---------------------------------------------
# Общий обработчик всех плагинов
# ---------------------------------------------
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