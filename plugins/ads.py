import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

bot = None
ADMIN_CHAT = -5037660983
OWNER_ID = 5775769170

# Хранение заявок
ads_orders = {}          # user_id → {photo_id, text, count, price, final_price, frequency}
waiting_price_input = {} # admin_id → user_id
waiting_new_price = {}   # admin_id → user_id

# Базовая цена за размещение 1 рекламы
base_price = 1.0

def init_plugin(b):
    global bot
    bot = b
    print("ADS Plugin loaded!")


###############################
#      АДМИН КОМАНДА /priser
###############################
@bot.message_handler(commands=["priser"])
def set_price(message):
    global base_price
    if message.chat.id != ADMIN_CHAT:
        bot.reply_to(message, "Эта команда доступна только в админ-чате.")
        return

    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Использование:\n/priser 1.5")
        return

    try:
        base_price = float(parts[1])
        bot.reply_to(message, f"💰 Новая базовая цена за *1 рекламу*: `{base_price}` Stars")
    except:
        bot.reply_to(message, "Ошибка формата цены.")


###############################
#          /buy_ads
###############################
@bot.message_handler(commands=["buy_ads"])
def buy_ads(message):
    uid = message.from_user.id
    ads_orders[uid] = {"step": "wait_photo"}
    bot.send_message(uid, "📸 Отправьте фото вашей рекламы:")


###############################
#      Приём фото
###############################
@bot.message_handler(content_types=["photo"])
def ads_photo(message):
    uid = message.from_user.id
    if uid not in ads_orders or ads_orders[uid].get("step") != "wait_photo":
        return

    photo_id = message.photo[-1].file_id
    ads_orders[uid]["photo"] = photo_id
    ads_orders[uid]["step"] = "wait_count"

    bot.send_message(uid, "🔢 Сколько показов вам нужно?")


################################
#      Приём количества
################################
@bot.message_handler(func=lambda m: m.from_user.id in ads_orders and ads_orders[m.from_user.id].get("step") == "wait_count")
def ads_count(message):
    uid = message.from_user.id
    try:
        count = int(message.text)
        if count <= 0:
            raise Exception()
    except:
        bot.send_message(uid, "Введите целое число > 0")
        return

    ads_orders[uid]["count"] = count
    ads_orders[uid]["step"] = "preview"

    approx_price = base_price * count
    ads_orders[uid]["approx_price"] = approx_price

    # Предпросмотр
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Все верно", callback_data=f"confirm_{uid}"))
    kb.add(InlineKeyboardButton("📸 Изменить фото", callback_data=f"changephoto_{uid}"))
    kb.add(InlineKeyboardButton("🔢 Изменить количество", callback_data=f"changecount_{uid}"))
    kb.add(InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{uid}"))

    bot.send_photo(
        uid,
        ads_orders[uid]["photo"],
        caption=f"📋 Ваша реклама:\n"
                f"Показы: {count}\n"
                f"💰 Примерная цена: {approx_price} Stars\n\n"
                f"Если всё верно — отправим на модерацию.",
        reply_markup=kb
    )


################################
#        CALLBACKS
################################
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def ads_confirm(call):
    uid = int(call.data.split("_")[1])
    order = ads_orders.get(uid)
    if not order:
        return

    # отправляем в админ чат
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"admin_ok_{uid}"))
    kb.add(InlineKeyboardButton("💰 Одобрить с ценой", callback_data=f"admin_newprice_{uid}"))
    kb.add(InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{uid}"))

    bot.send_photo(
        ADMIN_CHAT,
        order["photo"],
        caption=f"📢 Новая заявка!\n\n"
                f"👤 @{call.from_user.username}\n"
                f"ID: {uid}\n"
                f"Показы: {order['count']}\n"
                f"💰 Примерная цена: {order['approx_price']}\n\n"
                f"Выберите действие:",
        reply_markup=kb
    )

    bot.answer_callback_query(call.id, "Отправлено на модерацию!")
    bot.send_message(uid, "📤 Ваша заявка отправлена администраторам!")


##########################
#     ОТКЛОНЕНИЕ
##########################
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reject_"))
def admin_reject(call):
    uid = int(call.data.split("_")[2])
    if uid not in ads_orders:
        return

    bot.send_message(uid, "❌ Ваша реклама отклонена администратором.")
    bot.answer_callback_query(call.id, "Отклонено!")
    del ads_orders[uid]


##########################
#     Одобрить
##########################
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_ok_"))
def admin_ok(call):
    uid = int(call.data.split("_")[2])
    order = ads_orders.get(uid)
    if not order:
        return

    price = order["approx_price"]
    send_payment(uid, price)

    bot.answer_callback_query(call.id, "Одобрено! Счет отправлен пользователю.")


##########################
#  Одобрить с ценой
##########################
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_newprice_"))
def admin_newprice(call):
    uid = int(call.data.split("_")[2])
    waiting_new_price[call.from_user.id] = uid

    bot.answer_callback_query(call.id)
    bot.send_message(ADMIN_CHAT, f"Введите новую цену за ВСЮ сделку для ID {uid}:")


####################################
#   Приём новой цены от админа
####################################
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_CHAT and m.from_user.id in waiting_new_price)
def new_price_handler(message):
    admin_id = message.from_user.id
    uid = waiting_new_price[admin_id]

    try:
        price = float(message.text)
    except:
        bot.send_message(ADMIN_CHAT, "Цена должна быть числом.")
        return

    ads_orders[uid]["final_price"] = price
    del waiting_new_price[admin_id]

    send_payment(uid, price)
    bot.send_message(ADMIN_CHAT, f"💰 Цена установлена: {price} Stars. Счет отправлен пользователю.")


####################################
#      ОТПРАВКА ОПЛАТЫ
####################################
def send_payment(uid, price):
    bot.send_message(
        uid,
        f"💰 Стоимость размещения: {price} Stars\n"
        f"Нажмите кнопку ниже, чтобы оплатить.",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                "💳 Оплатить Stars",
                pay=True
            )
        )
    )