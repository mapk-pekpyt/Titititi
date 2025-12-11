import json
import os
from telebot import types

DATA_FILE = "plugins/ads_data.json"
ADMIN_ID = 5791171535

ads_price = 1.0  # по умолчанию цена за 1 показ
ads_queue = []
ads_current_index = 0

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": {}, "approved": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --------------------------
# /priser — установить цену
# --------------------------
def handle_priser(bot, message):
    global ads_price
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, f"Текущая цена за 1 показ: {ads_price} ⭐\nИспользуйте /priser <число>")
            return
        ads_price = float(parts[1])
        bot.send_message(message.chat.id, f"✅ Цена за 1 показ установлена: {ads_price} ⭐")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка! Укажите число. Пример: /priser 0.1")

# --------------------------
# /buy_ads — начать создание рекламы
# --------------------------
def handle_buy(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    data["pending"][user_id] = {"step": "text"}
    save_data(data)
    bot.send_message(message.chat.id, f"💰 Стоимость 1 показа: {ads_price} ⭐\nВведите текст вашей рекламы:")

# --------------------------
# Основной обработчик сообщений в процессе рекламы
# --------------------------
def handle(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    user_ads = data["pending"][user_id]

    step = user_ads.get("step")

    if step == "text":
        user_ads["text"] = message.text
        user_ads["step"] = "photo_choice"
        save_data(data)

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Да", callback_data="ads_add_photo"))
        markup.add(types.InlineKeyboardButton("Нет", callback_data="ads_no_photo"))
        bot.send_message(message.chat.id, "Добавить фото?", reply_markup=markup)

    elif step == "photo":
        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
            user_ads["photo"] = file_id
            user_ads["step"] = "quantity"
            save_data(data)
            bot.send_message(message.chat.id, "Введите количество показов:")
        else:
            bot.send_message(message.chat.id, "Отправьте фото или пропустите через 'Нет'")

    elif step == "quantity":
        try:
            qty = int(message.text)
            user_ads["quantity"] = qty
            user_ads["step"] = "notify"
            save_data(data)

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Каждые 10 сообщений", callback_data="ads_notify_10"))
            markup.add(types.InlineKeyboardButton("Каждые 50 сообщений", callback_data="ads_notify_50"))
            markup.add(types.InlineKeyboardButton("Каждые 100 сообщений", callback_data="ads_notify_100"))
            markup.add(types.InlineKeyboardButton("Только по завершению", callback_data="ads_notify_end"))
            bot.send_message(message.chat.id, "Выберите частоту уведомлений:", reply_markup=markup)
        except:
            bot.send_message(message.chat.id, "Введите число!")

# --------------------------
# Callback для всех кнопок рекламы
# --------------------------
def callback(bot, call):
    user_id = str(call.from_user.id)
    data = load_data()
    user_ads = data["pending"].get(user_id)

    # ------------------ фото
    if call.data == "ads_add_photo":
        user_ads["step"] = "photo"
        save_data(data)
        bot.edit_message_text("📷 Отправьте фото:", call.message.chat.id, call.message.message_id)
    elif call.data == "ads_no_photo":
        user_ads["step"] = "quantity"
        save_data(data)
        bot.edit_message_text("❌ Фото не будет", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Введите количество показов:")

    # ------------------ уведомления
    elif call.data.startswith("ads_notify_"):
        notify = call.data.split("_")[2]
        user_ads["notify"] = notify
        user_ads["step"] = "admin_preview"
        save_data(data)
        bot.edit_message_text(f"✅ Частота уведомлений выбрана: {notify}", call.message.chat.id, call.message.message_id)

        # показать превью и кнопки
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Всё верно", callback_data="ads_admin"))
        markup.add(types.InlineKeyboardButton("✏️ Изменить текст", callback_data="ads_edit_text"))
        markup.add(types.InlineKeyboardButton("📷 Изменить фото", callback_data="ads_edit_photo"))
        markup.add(types.InlineKeyboardButton("🔢 Изменить количество", callback_data="ads_edit_qty"))

        text_preview = f"💬 Текст: {user_ads.get('text','')}\nКоличество показов: {user_ads.get('quantity','')}\nЦена за показ: {ads_price} ⭐"
        bot.send_message(call.message.chat.id, text_preview, reply_markup=markup)

    # ------------------ админская проверка
    elif call.data == "ads_admin" and call.from_user.id == ADMIN_ID:
        # удаляем кнопки
        bot.edit_message_text("✅ Реклама одобрена и отправляется на оплату", call.message.chat.id, call.message.message_id)
        approved_ad = user_ads.copy()
        data["approved"].append(approved_ad)
        del data["pending"][user_id]
        save_data(data)

        # если цена >0 отправляем кнопку оплаты, иначе сразу публикуем
        chat_id = int(user_id)
        if ads_price > 0:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"Оплатить рекламу ({user_ads['quantity']*ads_price}⭐)", pay=True))
            bot.send_message(chat_id, "💰 Оплатите рекламу:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "✅ Реклама бесплатно опубликована!")

# --------------------------
# Вставка рекламы к каждому сообщению
# --------------------------
def attach_ad(bot, chat_id):
    global ads_current_index
    data = load_data()
    ads_list = data.get("approved", [])
    if not ads_list:
        return

    ad = ads_list[ads_current_index % len(ads_list)]
    text = ad.get("text","")
    photo = ad.get("photo")
    if photo:
        bot.send_photo(chat_id, photo, caption=text)
    else:
        bot.send_message(chat_id, text)
    ads_current_index += 1