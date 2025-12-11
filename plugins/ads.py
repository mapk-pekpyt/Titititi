# ads.py
import json
import os
from telebot import types
from datetime import datetime

DATA_FILE = "plugins/ads.json"
ADMIN_ID = 5791171535  # твой Telegram ID
DEFAULT_PRICE = 1.0    # стоимость 1 показа в звездах

def load():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "ads_active": [], "price": DEFAULT_PRICE}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ------------------------
# Команды для всех
# ------------------------
def handle_buy(bot, message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)

    if chat_id != user_id:
        bot.send_message(chat_id, "❌ Реклама работает только в личных сообщениях бота!")
        return

    data = load()
    data["pending"][user_id] = {
        "step": "text",
        "text": "",
        "photo": None,
        "notify": "end"
    }
    save(data)
    bot.send_message(chat_id, f"💰 Стоимость одного показа рекламы: {data.get('price', DEFAULT_PRICE)}⭐\nОтправьте текст вашей рекламы:")

def handle(bot, message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    data = load()
    pending = data.get("pending", {})

    if user_id not in pending:
        return

    entry = pending[user_id]

    if entry["step"] == "text":
        entry["text"] = message.text or ""
        entry["step"] = "photo"
        save(data)

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Добавить фото", callback_data="ads_photo_yes"))
        markup.add(types.InlineKeyboardButton("Без фото", callback_data="ads_photo_no"))
        bot.send_message(chat_id, "Хотите прикрепить фото?", reply_markup=markup)

    elif entry["step"] == "confirm":
        # Дальше админская проверка, но пока только текстовое подтверждение
        bot.send_message(chat_id, "❌ Ошибка: шаг confirm не должен вызываться напрямую.")

# ------------------------
# Callback для кнопок
# ------------------------
def callback(bot, call):
    user_id = str(call.from_user.id)
    data = load()
    pending = data.get("pending", {})
    if user_id not in pending:
        return
    entry = pending[user_id]
    chat_id = call.message.chat.id

    if call.data == "ads_photo_yes":
        entry["step"] = "photo_attach"
        save(data)
        bot.edit_message_text("Отправьте фото рекламы:", chat_id, call.message.message_id)

    elif call.data == "ads_photo_no":
        entry["step"] = "notify"
        entry["photo"] = None
        save(data)
        bot.edit_message_text("Выберите, как часто уведомлять о публикации:", chat_id, call.message.message_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Каждые 10 сообщений", callback_data="ads_notify_10"))
        markup.add(types.InlineKeyboardButton("Каждые 50 сообщений", callback_data="ads_notify_50"))
        markup.add(types.InlineKeyboardButton("Каждые 100 сообщений", callback_data="ads_notify_100"))
        markup.add(types.InlineKeyboardButton("Только по завершению", callback_data="ads_notify_end"))
        bot.send_message(chat_id, "Выберите вариант уведомления:", reply_markup=markup)

    elif call.data.startswith("ads_notify_"):
        notify_type = call.data.replace("ads_notify_", "")
        entry["notify"] = notify_type
        entry["step"] = "admin"
        save(data)
        bot.edit_message_text(f"Уведомления: {notify_type}", chat_id, call.message.message_id)

        # Отправляем на проверку администратору
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Одобрить", callback_data=f"ads_admin_approve_{user_id}"))
        markup.add(types.InlineKeyboardButton("Отклонить", callback_data=f"ads_admin_reject_{user_id}"))
        text_preview = entry["text"]
        if entry["photo"]:
            bot.send_photo(ADMIN_ID, entry["photo"], caption=f"Реклама от {call.from_user.username or user_id}:\n{text_preview}", reply_markup=markup)
        else:
            bot.send_message(ADMIN_ID, f"Реклама от {call.from_user.username or user_id}:\n{text_preview}", reply_markup=markup)

    elif call.data.startswith("ads_admin_approve_") or call.data.startswith("ads_admin_reject_"):
        target_user = call.data.split("_")[-1]
        if call.data.startswith("ads_admin_approve_"):
            # Одобрено
            bot.edit_message_text("✅ Реклама одобрена", call.message.chat.id, call.message.message_id)
            send_user_payment_request(bot, target_user)
        else:
            # Отклонено
            bot.edit_message_text("❌ Реклама отклонена", call.message.chat.id, call.message.message_id)
            bot.send_message(target_user, "❌ Ваша реклама отклонена администратором.")
        # Удаляем заявку
        pending.pop(target_user, None)
        save(data)

# ------------------------
# Оплата
# ------------------------
def send_user_payment_request(bot, user_id):
    data = load()
    price = data.get("price", DEFAULT_PRICE)
    if price <= 0:
        bot.send_message(user_id, "✅ Ваша реклама опубликована бесплатно!")
        # Добавляем в активные сразу
        active_ads = data.get("ads_active", [])
        active_ads.append({"user_id": user_id, "text": "", "photo": None, "notify": "end"})
        data["ads_active"] = active_ads
        save(data)
        return
    # В реальной интеграции сюда вставляется Telegram payment request
    bot.send_message(user_id, f"💳 Для публикации рекламы требуется оплата {price}⭐. (симуляция оплаты)")

# ------------------------
# Команды для администратора
# ------------------------
def handle_priser(bot, message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Только админ может установить цену!")
        return
    try:
        price = float(message.text.split()[1])
        data = load()
        data["price"] = price
        save(data)
        bot.send_message(message.chat.id, f"✅ Цена установлена: {price}⭐ за один показ")
    except Exception:
        bot.send_message(message.chat.id, "❌ Используйте: /priser <цена>")

def handle_all(bot, message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Только админ может использовать эту команду!")
        return
    data = load()
    pending = data.get("pending", {})
    text = "📋 Текущие задачи рекламы:\n"
    for uid, info in pending.items():
        text += f"- User {uid}, step: {info['step']}, notify: {info.get('notify','')}\n"
    bot.send_message(message.chat.id, text)

# ------------------------
# Раздача рекламы с сообщением бота
# ------------------------
def attach_ad(bot, chat_id):
    data = load()
    active_ads = data.get("ads_active", [])
    if not active_ads:
        return
    ad = active_ads.pop(0)  # берем первую рекламу
    data["ads_active"] = active_ads + [ad]  # чередуем
    save(data)
    if ad.get("photo"):
        bot.send_photo(chat_id, ad["photo"], caption=ad["text"])
    else:
        bot.send_message(chat_id, ad["text"])