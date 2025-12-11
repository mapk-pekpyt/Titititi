import json
import os
import random
from telebot import types

DATA_FILE = "plugins/ads_data.json"

# Загрузка данных
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "approved": {}, "price": 1}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Сохранение данных
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Установка цены
def handle_priser(bot, message):
    parts = message.text.split()
    data = load_data()
    if len(parts) >= 2:
        try:
            price = int(parts[1])
            data["price"] = price
            save_data(data)
            bot.reply_to(message, f"💰 Цена рекламы установлена: {price} звезда(ы)")
        except:
            bot.reply_to(message, "❌ Неверный формат. Используйте: /priser <число>")
    else:
        bot.reply_to(message, f"💰 Текущая цена: {data.get('price', 1)} звезда(ы)")

# Начало создания рекламы
def handle_buy(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    data["pending"][user_id] = {"step": "text"}
    save_data(data)
    bot.reply_to(message, "✏️ Отправьте текст вашей рекламы:")

# Обработка сообщений пользователя в процессе рекламы
def handle(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data["pending"]:
        return

    pending = data["pending"][user_id]

    if pending["step"] == "text":
        pending["text"] = message.text
        pending["step"] = "confirm_text"
        save_data(data)

        # Кнопки: продолжить, изменить текст
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Продолжить", callback_data="ads_confirm_text"))
        markup.add(types.InlineKeyboardButton("✏️ Изменить текст", callback_data="ads_change_text"))
        bot.reply_to(message, f"Ваш текст: {message.text}\nХотите продолжить?", reply_markup=markup)

    elif pending["step"] == "photo":
        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
            pending["photo"] = file_id
            pending["step"] = "waiting_admin"
            save_data(data)
            bot.reply_to(message, "📨 Ожидайте одобрения администратора.")
            # Отправляем админу на проверку
            send_to_admin(bot, user_id, pending)
        else:
            bot.reply_to(message, "❌ Прикрепите фото или пропустите отправкой 'без фото'.")

# Колбэки для кнопок
def callback(bot, call):
    user_id = str(call.from_user.id)
    data = load_data()
    pending = data["pending"].get(user_id)
    if not pending:
        return

    if call.data == "ads_confirm_text":
        pending["step"] = "photo"
        save_data(data)
        bot.send_message(user_id, "📸 Прикрепите фото к рекламе или напишите 'без фото':")

    elif call.data == "ads_change_text":
        pending["step"] = "text"
        save_data(data)
        bot.send_message(user_id, "✏️ Отправьте новый текст вашей рекламы:")

# Отправка админу на проверку
ADMIN_ID = 5791171535

def send_to_admin(bot, user_id, ad):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Одобрить", callback_data=f"ads_admin_yes_{user_id}"))
    markup.add(types.InlineKeyboardButton("❌ Отклонить", callback_data=f"ads_admin_no_{user_id}"))
    text = ad.get("text", "")
    photo = ad.get("photo")
    if photo:
        bot.send_photo(ADMIN_ID, photo, caption=f"Реклама от {user_id}:\n{text}", reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, f"Реклама от {user_id}:\n{text}", reply_markup=markup)

# Обработка админских колбэков
def handle_admin(bot, call):
    data = load_data()
    if call.data.startswith("ads_admin_yes_"):
        uid = call.data.split("_")[-1]
        pending = data["pending"].pop(uid, None)
        if pending:
            data["approved"][uid] = pending
            save_data(data)
            bot.send_message(uid, f"✅ Ваша реклама одобрена! Оплатите {data.get('price',1)} звезды.")
            send_payment_button(bot, uid, data.get("price",1))

    elif call.data.startswith("ads_admin_no_"):
        uid = call.data.split("_")[-1]
        pending = data["pending"].pop(uid, None)
        save_data(data)
        if pending:
            bot.send_message(uid, "❌ Ваша реклама отклонена. Напишите причину админу, она будет отправлена.")
            bot.send_message(ADMIN_ID, f"Напишите комментарий для {uid}:")

# Кнопка оплаты через Stars
def send_payment_button(bot, user_id, price):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"💳 Оплатить {price}⭐", callback_data=f"ads_pay_{user_id}"))
    bot.send_message(user_id, "💰 Нажмите для оплаты:", reply_markup=markup)

# Вставка рекламы в каждый ответ
def attach_ad(bot, chat_id):
    data = load_data()
    if not data.get("approved"):
        return
    uid, ad = random.choice(list(data["approved"].items()))
    text = ad.get("text", "")
    photo = ad.get("photo")
    if photo:
        bot.send_photo(chat_id, photo, caption=text)
    else:
        bot.send_message(chat_id, text)