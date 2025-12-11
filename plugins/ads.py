import json
import os
from telebot import types
from datetime import datetime

DATA_FILE = "plugins/ads_data.json"
ADMIN_ID = 5791171535
ads_price = 1  # цена за 1 показ, можно менять через /priser
ads_queue = []

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "approved": [], "price": 1}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def handle_priser(bot, message):
    global ads_price
    try:
        parts = message.text.split()
        if len(parts) == 2:
            ads_price = float(parts[1])
            data = load_data()
            data["price"] = ads_price
            save_data(data)
            bot.reply_to(message, f"💰 Цена за 1 показ установлена: {ads_price}⭐")
    except:
        bot.reply_to(message, "❌ Используйте: /priser <цена>")

def handle_buy(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    data["pending"][user_id] = {}
    save_data(data)
    price = data.get("price", ads_price)
    bot.send_message(message.chat.id, f"💰 Стоимость 1 показа рекламы: {price}⭐\nВведите текст вашей рекламы:")

def handle(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data["pending"]:
        return

    ad = data["pending"][user_id]

    # Текст
    if "text" not in ad:
        ad["text"] = message.text
        save_data(data)
        bot.send_message(message.chat.id, "📸 Прикрепите фото или выберите кнопку ниже:", reply_markup=photo_markup())
        return

    # Фото
    if "photo" not in ad:
        if message.content_type == "photo":
            ad["photo"] = message.photo[-1].file_id
            save_data(data)
        elif message.text.lower() == "без фото":
            ad["photo"] = None
        else:
            bot.send_message(message.chat.id, "❌ Прикрепите фото или напишите 'без фото'.", reply_markup=photo_markup())
            return

    # Количество показов
    if "quantity" not in ad:
        try:
            qty = int(message.text)
            ad["quantity"] = qty
            save_data(data)
        except:
            bot.send_message(message.chat.id, "Введите число показов рекламы (например, 10):")
            return

    # Частота уведомлений
    if "report" not in ad:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("Каждые 10 сообщений", "Каждые 50 сообщений", "Каждые 100 сообщений", "Только по завершению")
        bot.send_message(message.chat.id, "Как часто уведомлять о публикации?", reply_markup=markup)
        return

    if "report" not in ad and message.text in ["Каждые 10 сообщений", "Каждые 50 сообщений", "Каждые 100 сообщений", "Только по завершению"]:
        ad["report"] = message.text
        save_data(data)

    # Отправка превью
    send_preview(bot, message.chat.id, ad)

def photo_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Добавить фото", "Без фото")
    return markup

def send_preview(bot, chat_id, ad):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Всё верно", callback_data="ads_confirm"),
        types.InlineKeyboardButton("✏️ Изменить текст", callback_data="ads_edit_text"),
        types.InlineKeyboardButton("🔢 Изменить число показов", callback_data="ads_edit_quantity"),
        types.InlineKeyboardButton("📸 Изменить фото", callback_data="ads_edit_photo"),
    )

    if ad.get("photo"):
        bot.send_photo(chat_id, ad["photo"], caption=ad["text"], reply_markup=markup)
    else:
        bot.send_message(chat_id, ad["text"], reply_markup=markup)

def callback(bot, call):
    user_id = str(call.from_user.id)
    data = load_data()
    ad = data["pending"].get(user_id) or {}
    
    # Убираем кнопки
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    if call.data == "ads_confirm":
        # Отправляем админом
        bot.send_message(ADMIN_ID, f"📨 Новая реклама от {call.from_user.first_name}")
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Одобрить", callback_data=f"ads_admin:{user_id}"),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f"ads_decline:{user_id}")
        )
        bot.send_message(ADMIN_ID, ad.get("text", ""), reply_markup=markup)
        bot.answer_callback_query(call.id, "Реклама отправлена на проверку админом")

    elif call.data.startswith("ads_admin:") and call.from_user.id == ADMIN_ID:
        target_id = call.data.split(":")[1]
        approved_ad = data["pending"][target_id]
        del data["pending"][target_id]
        data["approved"].append(approved_ad)
        save_data(data)

        chat_id = int(target_id)
        if ads_price > 0:
            pay_markup = types.InlineKeyboardMarkup()
            pay_markup.add(types.InlineKeyboardButton(f"💰 Оплатить ({approved_ad['quantity']*ads_price}⭐)", pay=True))
            bot.send_message(chat_id, "Оплатите рекламу:", reply_markup=pay_markup)
        else:
            bot.send_message(chat_id, "✅ Ваша реклама бесплатно опубликована!")

        bot.answer_callback_query(call.id, "Реклама одобрена и отправлена пользователю")

    elif call.data.startswith("ads_decline:") and call.from_user.id == ADMIN_ID:
        target_id = call.data.split(":")[1]
        del data["pending"][target_id]
        save_data(data)
        bot.send_message(int(target_id), "❌ Ваша реклама отклонена администратором.")
        bot.answer_callback_query(call.id, "Реклама отклонена")

def attach_ad(bot, chat_id):
    # Отправка рекламы с каждым сообщением
    data = load_data()
    if not data.get("approved"):
        return
    ad = data["approved"].pop(0)
    if ad.get("photo"):
        bot.send_photo(chat_id, ad["photo"], caption=ad["text"])
    else:
        bot.send_message(chat_id, ad["text"])
    data["approved"].append(ad)
    save_data(data)