import telebot
from telebot import types
import json
import os
import random

DATA_FILE = "plugins/ads_data.json"

# ---------------------------
# Вспомогательные функции
# ---------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "approved": [], "price": 5, "last_sent_index": -1}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------------------------
# Команда установки цены /priser
# ---------------------------
def handle_priser(bot, message):
    parts = message.text.split()
    data = load_data()
    if len(parts) < 2:
        bot.reply_to(message, f"Текущая цена рекламы: {data.get('price',5)} ⭐. Используйте /priser <число>")
        return
    try:
        value = int(parts[1])
        if value < 0:
            value = 0
        data['price'] = value
        save_data(data)
        bot.reply_to(message, f"Цена рекламы успешно установлена: {value} ⭐")
    except:
        bot.reply_to(message, "Ошибка: укажите число после /priser")

# ---------------------------
# Команда начала создания рекламы /buy_ads
# ---------------------------
def handle_buy(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id in data.get("pending", {}):
        bot.reply_to(message, "Вы уже начали создавать рекламу. Завершите текущий процесс.")
        return
    data["pending"][user_id] = {"step": "text", "text": "", "photo": None}
    save_data(data)
    bot.reply_to(message, "Отправьте текст вашей рекламы:")

# ---------------------------
# Обработка текста и фото пользователя
# ---------------------------
def handle(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    user_data = data["pending"].get(user_id)
    if not user_data:
        return

    step = user_data.get("step")

    # Шаг 1 — текст
    if step == "text":
        user_data["text"] = message.text
        user_data["step"] = "photo_choice"
        save_data(data)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Да", callback_data="ads_add_photo_yes"))
        markup.add(types.InlineKeyboardButton("Нет", callback_data="ads_add_photo_no"))
        bot.reply_to(message, f"Хотите добавить фото к рекламе?", reply_markup=markup)
        return

    # Шаг 2 — фото
    if step == "photo" and message.content_type == "photo":
        # Берём наибольшее фото
        file_id = message.photo[-1].file_id
        user_data["photo"] = file_id
        user_data["step"] = "confirm"
        save_data(data)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Подтвердить", callback_data="ads_confirm"))
        bot.reply_to(message, "Фото добавлено. Подтвердите рекламу:", reply_markup=markup)
        return

# ---------------------------
# Callback обработка кнопок
# ---------------------------
def callback(bot, call):
    user_id = str(call.from_user.id)
    data = load_data()
    user_data = data["pending"].get(user_id)
    if not user_data:
        return

    if call.data == "ads_add_photo_yes":
        user_data["step"] = "photo"
        save_data(data)
        bot.send_message(call.message.chat.id, "Прикрепите фото вашей рекламы:")
        return
    elif call.data == "ads_add_photo_no":
        user_data["step"] = "confirm"
        save_data(data)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Подтвердить", callback_data="ads_confirm"))
        bot.send_message(call.message.chat.id, "Подтвердите вашу рекламу:", reply_markup=markup)
        return
    elif call.data == "ads_confirm":
        # Отправляем на модерацию админу
        approved_markup = types.InlineKeyboardMarkup()
        approved_markup.add(types.InlineKeyboardButton("Да", callback_data=f"ads_approve_{user_id}"))
        approved_markup.add(types.InlineKeyboardButton("Нет", callback_data=f"ads_decline_{user_id}"))
        text_preview = user_data.get("text", "")
        bot.send_message(5791171535, f"Новая реклама от {call.from_user.first_name}:\n{text_preview}", reply_markup=approved_markup)
        bot.send_message(call.message.chat.id, "Ваша реклама отправлена на одобрение администрации.")
        del data["pending"][user_id]
        save_data(data)
        return

    # Админская обработка
    if call.data.startswith("ads_approve_"):
        uid = call.data.replace("ads_approve_", "")
        # кнопка оплаты
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Оплатить ⭐", pay=True))
        bot.send_message(int(uid), "Ваша реклама одобрена! Оплатите для запуска:", reply_markup=markup)
    elif call.data.startswith("ads_decline_"):
        uid = call.data.replace("ads_decline_", "")
        bot.send_message(int(uid), "Ваша реклама отклонена администратором.")

# ---------------------------
# Функция вставки рекламы в любое сообщение бота
# ---------------------------
def attach_ad(bot, chat_id):
    data = load_data()
    ads_list = data.get("approved", [])
    if not ads_list:
        return
    # Чередование: берём следующий индекс
    last_index = data.get("last_sent_index", -1)
    next_index = (last_index + 1) % len(ads_list)
    ad = ads_list[next_index]

    # Отправка
    text = ad.get("text", "")
    photo = ad.get("photo")

    if text:
        bot.send_message(chat_id, f"💌 Реклама:\n{text}")
    if photo:
        bot.send_photo(chat_id, photo)

    # Сохраняем индекс
    data["last_sent_index"] = next_index
    save_data(data)