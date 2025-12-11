import json
import os
import random
from telebot import types

DATA_FILE = "plugins/ads_data.json"
ADMIN_ID = 5791171535  # Ваш Telegram ID
DEFAULT_PRICE = 1  # цена за 1 отправку, можно менять через /priser

# -----------------------------------
# Работа с данными
# -----------------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"price": DEFAULT_PRICE, "pending": {}, "approved": [], "queue": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------------
# Установка цены
# -----------------------------------
def handle_priser(bot, message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, f"Текущая цена за 1 отправку: {load_data()['price']} ⭐")
        return
    try:
        price = int(parts[1])
        data = load_data()
        data['price'] = price
        save_data(data)
        bot.reply_to(message, f"✅ Цена за 1 отправку рекламы установлена: {price} ⭐")
    except:
        bot.reply_to(message, "❌ Неверный формат. Используйте /priser <число>")

# -----------------------------------
# Начало создания рекламы
# -----------------------------------
def handle_buy_ads(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    data['pending'][user_id] = {"step": "text"}
    save_data(data)
    bot.reply_to(message, "✏️ Отправьте текст вашей рекламы:")

# -----------------------------------
# Обработка сообщений пользователя при создании рекламы
# -----------------------------------
def handle(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    pending = data.get("pending", {})
    if user_id not in pending:
        return  # не в процессе рекламы

    ad = pending[user_id]
    step = ad.get("step")

    if step == "text":
        ad['text'] = message.text
        ad['step'] = "count"
        save_data(data)
        bot.reply_to(message, "🔢 Сколько раз вы хотите отправить рекламу? (введите число)")
        return

    if step == "count":
        try:
            count = int(message.text)
            if count < 1:
                raise ValueError
            ad['count'] = count
            ad['step'] = "photo"
            save_data(data)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Да, добавлю фото", callback_data="ads_photo_yes"))
            markup.add(types.InlineKeyboardButton("Нет, без фото", callback_data="ads_photo_no"))
            bot.reply_to(message, "📸 Хотите прикрепить фото к рекламе?", reply_markup=markup)
        except:
            bot.reply_to(message, "❌ Введите корректное число рассылок")
        return

    if step == "photo_waiting":
        if message.content_type == "photo":
            ad['photo'] = message.photo[-1].file_id
        else:
            ad['photo'] = None
        ad['step'] = "preview"
        send_preview(bot, message, ad)
        save_data(data)
        return

# -----------------------------------
# Предпросмотр рекламы с кнопками
# -----------------------------------
def send_preview(bot, message, ad):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Всё верно", callback_data="ads_preview_yes"))
    markup.add(types.InlineKeyboardButton("✏️ Изменить текст", callback_data="ads_preview_text"))
    markup.add(types.InlineKeyboardButton("🔢 Изменить число рассылок", callback_data="ads_preview_count"))
    markup.add(types.InlineKeyboardButton("📸 Изменить фото", callback_data="ads_preview_photo"))

    text = f"📢 Предпросмотр вашей рекламы:\n\n{ad['text']}\n\nКоличество рассылок: {ad['count']}\nЦена за 1 рассылку: {load_data()['price']} ⭐"
    if ad.get('photo'):
        bot.send_photo(message.chat.id, ad['photo'], caption=text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, text, reply_markup=markup)

# -----------------------------------
# Callback для кнопок
# -----------------------------------
def callback(bot, call):
    user_id = str(call.from_user.id)
    data = load_data()
    pending = data.get("pending", {})
    ad = pending.get(user_id)
    if not ad:
        return

    if call.data == "ads_photo_yes":
        ad['step'] = "photo_waiting"
        save_data(data)
        bot.edit_message_text("📸 Отправьте фото для рекламы:", call.message.chat.id, call.message.message_id)
    if call.data == "ads_photo_no":
        ad['photo'] = None
        ad['step'] = "preview"
        save_data(data)
        send_preview(bot, call.message, ad)
    if call.data.startswith("ads_preview_"):
        if call.data == "ads_preview_yes":
            # отправляем на модерацию
            data['queue'].append({**ad, "user_id": user_id})
            del data['pending'][user_id]
            save_data(data)
            bot.edit_message_text("⏳ Ваша реклама отправлена на одобрение администрации", call.message.chat.id, call.message.message_id)
            # уведомление админ
            send_admin_review(bot, data['queue'][-1])
        elif call.data == "ads_preview_text":
            ad['step'] = "text"
            pending[user_id] = ad
            save_data(data)
            bot.edit_message_text("✏️ Отправьте новый текст рекламы:", call.message.chat.id, call.message.message_id)
        elif call.data == "ads_preview_count":
            ad['step'] = "count"
            pending[user_id] = ad
            save_data(data)
            bot.edit_message_text("🔢 Введите новое число рассылок:", call.message.chat.id, call.message.message_id)
        elif call.data == "ads_preview_photo":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Да, добавлю фото", callback_data="ads_photo_yes"))
            markup.add(types.InlineKeyboardButton("Нет, без фото", callback_data="ads_photo_no"))
            bot.edit_message_text("📸 Хотите изменить фото?", call.message.chat.id, call.message.message_id, reply_markup=markup)

# -----------------------------------
# Отправка админу на проверку
# -----------------------------------
def send_admin_review(bot, ad):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Одобрить", callback_data=f"ads_admin_yes_{ad['user_id']}"))
    markup.add(types.InlineKeyboardButton("❌ Отклонить", callback_data=f"ads_admin_no_{ad['user_id']}"))
    text = f"📢 Новая реклама от {ad['user_id']}:\n\n{ad['text']}\nКоличество рассылок: {ad['count']}"
    if ad.get('photo'):
        bot.send_photo(ADMIN_ID, ad['photo'], caption=text, reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, text, reply_markup=markup)

# -----------------------------------
# Обработка админских кнопок
# -----------------------------------
def admin_callback(bot, call):
    data = load_data()
    if call.data.startswith("ads_admin_yes_"):
        user_id = call.data.split("_")[-1]
        ad = None
        for item in data['queue']:
            if item['user_id'] == user_id:
                ad = item
                break
        if not ad:
            return
        data['approved'].append(ad)
        data['queue'] = [x for x in data['queue'] if x['user_id'] != user_id]
        save_data(data)
        # уведомляем пользователя
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Оплатить рекламу", pay=True))
        bot.send_message(user_id, "✅ Ваша реклама одобрена. Нажмите кнопку для оплаты.", reply_markup=markup)
        bot.answer_callback_query(call.id, "Реклама одобрена")
    elif call.data.startswith("ads_admin_no_"):
        user_id = call.data.split("_")[-1]
        ad = None
        for item in data['queue']:
            if item['user_id'] == user_id:
                ad = item
                break
        if not ad:
            return
        data['queue'] = [x for x in data['queue'] if x['user_id'] != user_id]
        save_data(data)
        bot.send_message(user_id, "❌ Ваша реклама отклонена админом.")
        bot.answer_callback_query(call.id, "Реклама отклонена")

# -----------------------------------
# Отправка рекламы с каждым сообщением бота
# -----------------------------------
def attach_ads(bot, chat_id, message_text, message_photo=None):
    data = load_data()
    approved = data.get('approved', [])
    if not approved:
        return None
    # чередуем рекламу
    ad = approved.pop(0)
    approved.append(ad)
    data['approved'] = approved
    save_data(data)

    text = f"📢 Реклама:\n{ad['text']}"
    if ad.get('photo'):
        bot.send_photo(chat_id, ad['photo'], caption=text)
    else:
        bot.send_message(chat_id, text)