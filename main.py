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
    "ads": ads,            # <-- добавлен плагин рекламы
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
    # 1️⃣ Обработка всех плагинов как было
    for name, plugin in PLUGINS.items():
        try:
            if hasattr(plugin, "handle_successful"):
                plugin.handle_successful(bot, message)
        except Exception as e:
            print(f"❌ Ошибка в обработке оплаты у {name}: {e}")

    # 2️⃣ Лото: добавляем реальные звезды в банк и проверяем лото (если у тебя есть такой метод)
    try:
        stars = 0
        if hasattr(message, "successful_payment"):
            # у Telegram Stars unit = 1/100 «currency units» — у тебя ранее использовалась такая логика
            stars = int(getattr(message.successful_payment, "total_amount", 0)) // 100

        chat_id = message.chat.id
        user_id = message.from_user.id

        if stars > 0 and hasattr(loto, "add_stars"):
            loto.add_stars(chat_id, user_id, stars)
            if hasattr(loto, "check_loto"):
                loto.check_loto(bot, chat_id)

    except Exception as e:
        print(f"❌ Ошибка при добавлении звезд в лото: {e}")


# ---------------------------------------------
# Обработчики для рекламы (без изменения остального майна)
# ---------------------------------------------
@bot.message_handler(commands=["buy_ads"])
def buy_ads_cmd(msg):
    try:
        ads.handle_buy(bot, msg)
    except Exception as e:
        print("Ошибка buy_ads:", e)

@bot.message_handler(commands=["priser"])
def price_cmd(msg):
    try:
        ads.handle_price(bot, msg)
    except Exception as e:
        print("Ошибка priser:", e)


# ---------------------------------------------
# Обработчик callback'ов (нужен для кнопок рекламы и админских кнопок)
# ---------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def global_callback_handler(call):
    try:
        # передаём callback в плагин ads (он сам разбирает префиксы)
        if hasattr(ads, "handle_callback"):
            ads.handle_callback(bot, call)
    except Exception as e:
        print("Ошибка callback:", e)


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
        # если команда не из триггеров, всё равно показываем рекламу при действии
        try:
            ads.send_random_ads(bot, message.chat.id)
        except Exception:
            pass
        return

    plugin = PLUGINS.get(plugin_name)
    if not plugin:
        # аналогично — показываем рекламу при действии
        try:
            ads.send_random_ads(bot, message.chat.id)
        except Exception:
            pass
        return

    if hasattr(plugin, "handle"):
        try:
            plugin.handle(bot, message)
        except Exception as e:
            print(f"❗ Ошибка в плагине {plugin_name}: {e}")
    else:
        print(f"❗ Плагин {plugin_name} не имеет функции handle()")

    # После обработки команды — показываем рекламу (если есть активные)
    try:
        ads.send_random_ads(bot, message.chat.id)
    except Exception as e:
        # не фатальная ошибка, логируем
        print("Ошибка показа рекламы:", e)


if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()