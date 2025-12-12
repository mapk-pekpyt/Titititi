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
# ✅ Обработчик pre-checkout для Stars
# ---------------------------------------------
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(pre_checkout_query):
    try:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        print("❌ Ошибка pre-checkout:", e)

# -----------------------------------------------------
# 🔥 Главный обработчик успешной оплаты для всех
# -----------------------------------------------------
@bot.message_handler(content_types=['successful_payment'])
def payment_handler(message):
    for name, plugin in PLUGINS.items():
        try:
            if hasattr(plugin, "handle_successful"):
                plugin.handle_successful(bot, message)
        except Exception as e:
            print(f"❌ Ошибка в обработке оплаты у {name}: {e}")

    # Лото: добавляем реальные звезды
    try:
        stars = 0
        if hasattr(message, "successful_payment"):
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
# Обработчики рекламы
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
# Обработчик callback
# ---------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def global_callback_handler(call):
    try:
        if hasattr(ads, "handle_callback"):
            ads.handle_callback(bot, call)
    except Exception as e:
        print("Ошибка callback:", e)

# ---------------------------------------------
# Общий обработчик всех плагинов (текст + фото)
# ---------------------------------------------
@bot.message_handler(content_types=["text", "photo"])
def handle_all_messages(message):
    user_id = str(message.from_user.id)

    # Проверка рекламы в процессе покупки
    try:
        data = ads.load_ads()
        if user_id in data.get("pending", {}):
            ads.handle(bot, message)
            return
    except Exception:
        pass

    plugin_called = False

    # Фото
    if message.content_type == "photo":
        for name, plugin in PLUGINS.items():
            if hasattr(plugin, "handle"):
                try:
                    plugin.handle(bot, message)
                    plugin_called = True
                except Exception as e:
                    print(f"❗ Ошибка в плагине {name}: {e}")
    else:  # Текст
        text = message.text
        if text:
            cmd_raw = text.split()[0].lower()
            cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw
            plugin_name = TRIGGERS.get(cmd)
            if plugin_name:
                plugin = PLUGINS.get(plugin_name)
                if plugin and hasattr(plugin, "handle"):
                    try:
                        plugin.handle(bot, message)
                        plugin_called = True
                    except Exception as e:
                        print(f"❗ Ошибка в плагине {plugin_name}: {e}")
            else:
                # Обычный текст — пробуем передать всем плагинам один раз
                for name, plugin in PLUGINS.items():
                    if hasattr(plugin, "handle"):
                        try:
                            plugin.handle(bot, message)
                            plugin_called = True
                        except Exception as e:
                            print(f"❗ Ошибка в плагине {name}: {e}")

    # Показываем рекламу один раз, только если плагин был вызван
    if plugin_called:
        try:
            ads.send_random_ads(bot, message.chat.id)
        except Exception as e:
            print("Ошибка показа рекламы:", e)

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()