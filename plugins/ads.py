import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = None

ADMIN_CHAT = -5037660983
base_price = 1.0

ads_orders = {}
waiting_new_price = {}


def init_plugin(b):
    global bot
    bot = b
    print("[ADS] Plugin loaded!")

    ###############################
    # /priser — ТОЛЬКО В АДМИН ЧАТЕ
    ###############################
    @bot.message_handler(commands=["priser"])
    def set_price(message):
        global base_price
        if message.chat.id != ADMIN_CHAT:
            bot.reply_to(message, "Команда доступна только в админ-чате.")
            return

        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Использование:\n/priser 1.5")
            return

        try:
            base_price = float(parts[1])
            bot.reply_to(message, f"Новая цена за 1 показ: {base_price} Stars")
        except:
            bot.reply_to(message, "Введите корректное число.")

    ###############################
    # /buy_ads
    ###############################
    @bot.message_handler(commands=["buy_ads"])
    def buy_ads(message):
        uid = message.from_user.id
        ads_orders[uid] = {"step": "wait_photo"}
        bot.send_message(uid, "📸 Отправьте фото для рекламы:")

    ###############################
    # Приём фото
    ###############################
    @bot.message_handler(content_types=["photo"])
    def ads_photo(message):
        uid = message.from_user.id
        if uid not in ads_orders or ads_orders[uid]["step"] != "wait_photo":
            return

        ads_orders[uid]["photo"] = message.photo[-1].file_id
        ads_orders[uid]["step"] = "wait_count"
        bot.send_message(uid, "🔢 Введите количество показов:")

    ###############################
    # Количество показов
    ###############################
    @bot.message_handler(func=lambda m: m.from_user.id in ads_orders and ads_orders[m.from_user.id]["step"] == "wait_count")
    def ads_count(message):
        uid = message.from_user.id
        try:
            count = int(message.text)
            if count <= 0:
                raise Exception
        except:
            bot.send_message(uid, "Введите целое число больше нуля.")
            return

        ads_orders[uid]["count"] = count

        approx = base_price * count
        ads_orders[uid]["approx_price"] = approx
        ads_orders[uid]["step"] = "preview"

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Все верно", callback_data=f"confirm_{uid}"))
        kb.add(InlineKeyboardButton("📸 Изменить фото", callback_data=f"changephoto_{uid}"))
        kb.add(InlineKeyboardButton("🔢 Изменить количество", callback_data=f"changecount_{uid}"))
        kb.add(InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{uid}"))

        bot.send_photo(
            uid,
            ads_orders[uid]["photo"],
            caption=(
                f"📋 Предпросмотр рекламы:\n"
                f"Показы: {count}\n"
                f"💰 Примерная стоимость: {approx} Stars\n\n"
                "Проверьте данные."
            ),
            reply_markup=kb
        )

    ###############################################
    # CALLBACKS
    ###############################################

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_"))
    def cancel(call):
        uid = int(call.data.split("_")[1])
        ads_orders.pop(uid, None)
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "❌ Заявка отменена.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("changephoto_"))
    def change_photo(call):
        uid = int(call.data.split("_")[1])
        ads_orders[uid]["step"] = "wait_photo"
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "📸 Отправьте новое фото.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("changecount_"))
    def change_count(call):
        uid = int(call.data.split("_")[1])
        ads_orders[uid]["step"] = "wait_count"
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "🔢 Введите новое количество показов.")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_"))
    def confirm(call):
        uid = int(call.data.split("_")[1])
        order = ads_orders[uid]

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"admin_ok_{uid}"))
        kb.add(InlineKeyboardButton("💰 Одобрить с ценой", callback_data=f"admin_price_{uid}"))
        kb.add(InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{uid}"))

        bot.send_photo(
            ADMIN_CHAT,
            order["photo"],
            caption=(
                f"📢 Новая заявка!\n\n"
                f"👤 @{call.from_user.username}\n"
                f"ID: {uid}\n"
                f"Показы: {order['count']}\n"
                f"💰 Примерная цена: {order['approx_price']}"
            ),
            reply_markup=kb
        )

        bot.answer_callback_query(call.id)
        bot.send_message(uid, "📤 Заявка отправлена на проверку!")

    ###############################################
    # АДМИНСКИЕ КНОПКИ
    ###############################################

    @bot.callback_query_handler(func=lambda c: c.data.startswith("admin_reject_"))
    def admin_reject(call):
        uid = int(call.data.split("_")[2])
        bot.answer_callback_query(call.id, "Отклонено!")
        bot.send_message(uid, "❌ Ваша реклама отклонена.")
        ads_orders.pop(uid, None)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("admin_ok_"))
    def admin_ok(call):
        uid = int(call.data.split("_")[2])
        order = ads_orders[uid]
        bot.answer_callback_query(call.id)

        send_payment(uid, order["approx_price"])

    @bot.callback_query_handler(func=lambda c: c.data.startswith("admin_price_"))
    def admin_price(call):
        uid = int(call.data.split("_")[2])
        waiting_new_price[call.from_user.id] = uid
        bot.answer_callback_query(call.id)
        bot.send_message(ADMIN_CHAT, f"Введите новую цену для сделки (ID {uid}):")

    @bot.message_handler(func=lambda m: m.chat.id == ADMIN_CHAT and m.from_user.id in waiting_new_price)
    def admin_set_price(message):
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
        bot.send_message(ADMIN_CHAT, f"💰 Цена {price} Stars отправлена пользователю.")


###################################################
# ОТПРАВКА ОПЛАТЫ (Telegram Stars)
###################################################
def send_payment(uid, amount):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "💳 Оплатить в Stars",
            pay=True
        )
    )

    bot.send_message(
        uid,
        f"💰 Цена за размещение: {amount} Stars\nНажмите кнопку ниже чтобы оплатить:",
        reply_markup=kb
    )