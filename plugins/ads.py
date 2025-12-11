import telebot
from telebot import types
import json
import os

DATA_FILE = "plugins/ads_data.json"
ADMIN_ID = 5791171535  # Твой Telegram ID

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "approved": {}, "price": 10}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -------------------------
# Команда /priser
# -------------------------
def handle_priser(bot, message):
    data = load_data()
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, f"Текущая цена рекламы: {data.get('price',10)} звезд.")
        return
    try:
        price = int(parts[1])
        if price < 0:
            price = 0
        data['price'] = price
        save_data(data)
        bot.reply_to(message, f"Цена рекламы установлена на {price} звезд за 1 рассылку.")
    except:
        bot.reply_to(message, "Неверное число. Используйте /priser <число>")

# -------------------------
# Команда /buy_ads
# -------------------------
def handle_buy(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    data['pending'][user_id] = {"step": "text", "text": "", "photo": None}
    save_data(data)
    bot.reply_to(message, "Отправьте текст вашей рекламы:")

# -------------------------
# Обработка сообщений пользователей в процессе рекламы
# -------------------------
def handle(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data.get("pending", {}):
        return False  # Не реклама

    user_data = data['pending'][user_id]
    step = user_data.get("step")

    if step == "text":
        user_data['text'] = message.text
        user_data['step'] = "confirm_text"
        save_data(data)

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Продолжить", callback_data="ads_confirm_text"))
        markup.add(types.InlineKeyboardButton("✏️ Изменить текст", callback_data="ads_edit_text"))
        bot.reply_to(message, f"Ваша реклама:\n\n{message.text}\n\nЦена: {data.get('price',10)} звезд. Хотите продолжить?", reply_markup=markup)
        return True

    if step == "photo" and message.content_type == "photo":
        photo_id = message.photo[-1].file_id
        user_data['photo'] = photo_id
        user_data['step'] = "ready_to_send"
        save_data(data)
        bot.reply_to(message, "Фото добавлено. Нажмите 'Подтвердить рекламу' когда готовы.", reply_markup=confirm_markup())
        return True

    return True

# -------------------------
# Клавиатура подтверждения
# -------------------------
def confirm_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Подтвердить рекламу", callback_data="ads_send_admin"))
    return markup

# -------------------------
# Обработка callback
# -------------------------
def callback(bot, call):
    user_id = str(call.from_user.id)
    data = load_data()
    user_data = data['pending'].get(user_id)
    if not user_data:
        return

    if call.data == "ads_edit_text":
        user_data['step'] = "text"
        save_data(data)
        bot.send_message(user_id, "Отправьте новый текст рекламы:")

    elif call.data == "ads_confirm_text":
        user_data['step'] = "photo"
        save_data(data)
        bot.send_message(user_id, "Прикрепите фото (или отправьте /skip если без фото):")

    elif call.data == "ads_send_admin":
        data['pending'][user_id]['step'] = "wait_admin"
        save_data(data)
        bot.send_message(user_id, "Ожидайте одобрения администрации.")
        # Отправляем админке
        text = data['pending'][user_id]['text']
        photo = data['pending'][user_id].get('photo')
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Одобрить", callback_data=f"ads_admin_yes_{user_id}"))
        markup.add(types.InlineKeyboardButton("❌ Отклонить", callback_data=f"ads_admin_no_{user_id}"))
        if photo:
            bot.send_photo(ADMIN_ID, photo, caption=f"Реклама от {call.from_user.first_name}:\n\n{text}", reply_markup=markup)
        else:
            bot.send_message(ADMIN_ID, f"Реклама от {call.from_user.first_name}:\n\n{text}", reply_markup=markup)

    elif call.data.startswith("ads_admin_yes_"):
        uid = call.data.split("_")[-1]
        udata = data['pending'].pop(uid, None)
        if udata:
            data['approved'][uid] = udata
            save_data(data)
            bot.send_message(int(uid), "Ваша реклама одобрена! Нажмите кнопку для оплаты.", reply_markup=pay_markup(data))
        bot.answer_callback_query(call.id, "Одобрено")

    elif call.data.startswith("ads_admin_no_"):
        uid = call.data.split("_")[-1]
        udata = data['pending'].pop(uid, None)
        save_data(data)
        bot.send_message(int(uid), "Реклама отклонена. Попробуйте изменить текст или фото.")
        bot.answer_callback_query(call.id, "Отклонено")

# -------------------------
# Клавиатура оплаты
# -------------------------
def pay_markup(data):
    price = data.get("price", 10)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"💫 Оплатить {price} звезд", callback_data="ads_pay"))
    return markup

# -------------------------
# Обработка успешной оплаты
# -------------------------
def handle_successful(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    # реклама уже должна быть в approved
    if user_id in data.get("approved", {}):
        # Отправляем себе уведомление, что реклама оплачена
        bot.send_message(user_id, "Оплата получена! Ваша реклама теперь будет вставляться в ответы бота.")
        # Всё готово к вставке в остальные плагины