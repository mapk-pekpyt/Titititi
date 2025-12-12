import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
import telebot

DATA_FILE = "plugins/ads_data.json"
ADMIN_CHAT_ID = -5037660983  # админский чат
CURRENCY = "RUB"
PAYMENT_PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"  # Telegram Stars

def load_ads():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": {}, "approved": []}

def save_ads(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------
# /buy_ads — старт процесса
# -----------------------------
def handle_buy(bot, message):
    if message.chat.type != "private":
        bot.send_message(message.chat.id, "❌ Реклама работает только в ЛС бота!")
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    data["pending"][user_id] = {
        "step": "text",
        "user_name": message.from_user.username or message.from_user.first_name
    }
    save_ads(data)
    bot.send_message(message.chat.id, "✏️ Введите текст вашей рекламы:")

# -----------------------------
# Обработка сообщений пользователя
# -----------------------------
def handle(bot, message):
    if message.chat.type != "private":
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    if user_id not in data["pending"]:
        return
    ad = data["pending"][user_id]

    # Шаги: text → photo → count → confirm → payment
    if ad["step"] == "text":
        ad["text"] = message.text
        ad["step"] = "photo"
        save_ads(data)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"ads_photo_yes_{user_id}"))
        kb.add(InlineKeyboardButton("Без фото", callback_data=f"ads_photo_no_{user_id}"))
        bot.send_message(message.chat.id, "Хотите прикрепить фото?", reply_markup=kb)
        return

    if ad["step"] == "photo":
        if message.content_type == "photo":
            ad["photo"] = message.photo[-1].file_id
        ad["step"] = "count"
        save_ads(data)
        bot.send_message(message.chat.id, "Введите количество показов рекламы (например, 5):")
        return

    if ad["step"] == "count":
        try:
            ad["count"] = int(message.text)
            ad["step"] = "confirm"
            save_ads(data)
            send_confirmation(bot, user_id, ad)
        except:
            bot.send_message(message.chat.id, "❌ Введите число показов!")
        return

# -----------------------------
# Предпросмотр пользователю и отправка админу
# -----------------------------
def send_confirmation(bot, user_id, ad):
    # Кнопки пользователя
    kb_user = InlineKeyboardMarkup()
    kb_user.add(InlineKeyboardButton("✅ Верно", callback_data=f"ads_confirm_{user_id}"))
    kb_user.add(InlineKeyboardButton("❌ Отмена", callback_data=f"ads_cancel_{user_id}"))
    kb_user.add(InlineKeyboardButton("✏️ Изменить текст", callback_data=f"ads_change_text_{user_id}"))
    kb_user.add(InlineKeyboardButton("🖼 Изменить фото", callback_data=f"ads_change_photo_{user_id}"))
    kb_user.add(InlineKeyboardButton("🔢 Изменить количество", callback_data=f"ads_change_count_{user_id}"))

    caption = f"Проверьте вашу рекламу:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    if "photo" in ad:
        bot.send_photo(int(user_id), ad["photo"], caption=caption, reply_markup=kb_user)
    else:
        bot.send_message(int(user_id), caption, reply_markup=kb_user)

    # Кнопки админов
    kb_admin = InlineKeyboardMarkup()
    kb_admin.add(InlineKeyboardButton("Одобрить", callback_data=f"ads_admin_confirm_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Отклонить", callback_data=f"ads_admin_reject_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Одобрить с ценой", callback_data=f"ads_admin_price_{user_id}"))

    text = f"📩 Новая реклама от @{ad['user_name']}:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    if "photo" in ad:
        bot.send_photo(ADMIN_CHAT_ID, ad["photo"], caption=text, reply_markup=kb_admin)
    else:
        bot.send_message(ADMIN_CHAT_ID, text, reply_markup=kb_admin)

# -----------------------------
# Обработка callback
# -----------------------------
def handle_callback(bot, call):
    data = load_ads()
    parts = call.data.split("_")
    user_id = parts[-1]

    # Пользовательские кнопки
    if parts[0] == "ads":
        if parts[1] == "confirm":
            # Отправляем на модерацию
            ad = data["pending"][user_id]
            ad["step"] = "payment"
            save_ads(data)
            send_to_admin(bot, ad, user_id)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(int(user_id), "📨 Ваша реклама отправлена на модерацию. После одобрения вы сможете оплатить показ.")
            return
        if parts[1] == "cancel":
            del data["pending"][user_id]
            save_ads(data)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(int(user_id), "❌ Ваша заявка отменена.")
            return
        if parts[1] == "change":
            ad = data["pending"][user_id]
            step_map = {"text": "text", "photo": "photo", "count": "count"}
            ad["step"] = step_map.get(parts[2].split("_")[-1], "text")
            save_ads(data)
            prompts = {
                "text": "Введите новый текст рекламы:",
                "photo": "Отправьте новое фото или пропустите:",
                "count": "Введите новое количество показов:"
            }
            bot.send_message(int(user_id), prompts[ad["step"]])
            return

    # Админские кнопки
    if parts[0] == "ads" and parts[1] == "admin":
        ad = data["pending"].get(user_id)
        if not ad:
            bot.answer_callback_query(call.id, "❌ Ошибка!")
            return

        # Одобрить
        if parts[2] == "confirm":
            ad["step"] = "invoice"
            save_ads(data)
            bot.send_message(int(user_id), f"✅ Ваша реклама одобрена! Оплатите показ для начала рассылки.")
            send_invoice(bot, user_id, ad)
            return
        # Отклонить
        if parts[2] == "reject":
            del data["pending"][user_id]
            save_ads(data)
            bot.send_message(int(user_id), "❌ Ваша реклама отклонена админом.")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            return
        # Одобрить с ценой
        if parts[2] == "price":
            ad["step"] = "set_price"
            save_ads(data)
            bot.send_message(int(user_id), "Введите новую цену за всю сделку в Stars (например, 0.1):")
            return

# -----------------------------
# Отправка на модерацию (админский чат)
# -----------------------------
def send_to_admin(bot, ad, user_id):
    kb_admin = InlineKeyboardMarkup()
    kb_admin.add(InlineKeyboardButton("Одобрить", callback_data=f"ads_admin_confirm_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Отклонить", callback_data=f"ads_admin_reject_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Одобрить с ценой", callback_data=f"ads_admin_price_{user_id}"))

    text = f"📩 Новая реклама от @{ad['user_name']}:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    if "photo" in ad:
        bot.send_photo(ADMIN_CHAT_ID, ad["photo"], caption=text, reply_markup=kb_admin)
    else:
        bot.send_message(ADMIN_CHAT_ID, text, reply_markup=kb_admin)

# -----------------------------
# Отправка invoice пользователю
# -----------------------------
def send_invoice(bot, user_id, ad):
    price = int(ad.get("price", 0.1) * 100)  # Telegram Stars в копейках
    prices = [LabeledPrice(label="Реклама", amount=price)]
    bot.send_invoice(
        chat_id=int(user_id),
        title="Оплата рекламы",
        description=f"Оплата за показ рекламы ({ad['count']} раз)",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=CURRENCY,
        prices=prices,
        start_parameter="ads_payment",
        payload=f"ads_{user_id}"
    )

# -----------------------------
# Показ рекламы после оплаты
# -----------------------------
def send_random_ads(bot, chat_id):
    data = load_ads()
    if not data.get("approved"):
        return
    ad = data["approved"].pop(0)
    if ad.get("photo"):
        bot.send_photo(chat_id, ad["photo"], caption=ad["text"])
    else:
        bot.send_message(chat_id, ad["text"])
    ad["count"] -= 1
    if ad["count"] > 0:
        data["approved"].append(ad)
    save_ads(data)