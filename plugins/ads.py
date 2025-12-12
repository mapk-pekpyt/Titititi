import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

DATA_FILE = "plugins/ads_data.json"
ADMIN_CHAT_ID = -5037660983  # групповой чат админов
PRICE_DEFAULT = 1  # цена за один показ в Stars

def load_ads():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": {}, "approved": [], "price": PRICE_DEFAULT}

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
# Обработка сообщений от пользователя
# -----------------------------
def handle(bot, message):
    if message.chat.type != "private":
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    if user_id not in data.get("pending", {}):
        return
    ad = data["pending"][user_id]

    # --- текст рекламы ---
    if ad["step"] == "text":
        ad["text"] = message.text
        ad["step"] = "photo"
        save_ads(data)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"user_photo_yes_{user_id}"))
        kb.add(InlineKeyboardButton("Без фото", callback_data=f"user_photo_no_{user_id}"))
        bot.send_message(message.chat.id, "Хотите прикрепить фото?", reply_markup=kb)
        return

    # --- фото ---
    if ad["step"] == "photo":
        if message.content_type == "photo":
            ad["photo"] = message.photo[-1].file_id
        ad["step"] = "count"
        save_ads(data)
        bot.send_message(message.chat.id, "Введите количество показов рекламы (например, 5):")
        return

    # --- количество показов ---
    if ad["step"] == "count":
        try:
            ad["count"] = int(message.text)
            ad["step"] = "confirm"
            save_ads(data)
            send_confirmation(bot, user_id, ad)
        except:
            bot.send_message(message.chat.id, "❌ Введите число показов!")

# -----------------------------
# Отправка предпросмотра и админам
# -----------------------------
def send_confirmation(bot, user_id, ad):
    # кнопки пользователя
    kb_user = InlineKeyboardMarkup()
    kb_user.add(InlineKeyboardButton("✅ Все верно", callback_data=f"user_confirm_{user_id}"))
    kb_user.add(InlineKeyboardButton("❌ Отменить", callback_data=f"user_cancel_{user_id}"))
    kb_user.add(InlineKeyboardButton("✏️ Изменить текст", callback_data=f"user_change_text_{user_id}"))
    kb_user.add(InlineKeyboardButton("🖼 Изменить фото", callback_data=f"user_change_photo_{user_id}"))
    kb_user.add(InlineKeyboardButton("🔢 Изменить количество", callback_data=f"user_change_count_{user_id}"))

    # сообщение пользователю с фото если есть
    if "photo" in ad:
        bot.send_photo(int(user_id), ad["photo"], caption=f"📋 Проверьте вашу рекламу:\n\n{ad['text']}\n📊 Показов: {ad['count']}", reply_markup=kb_user)
    else:
        bot.send_message(int(user_id), f"📋 Проверьте вашу рекламу:\n\n{ad['text']}\n📊 Показов: {ad['count']}", reply_markup=kb_user)

    # уведомление в админский чат
    kb_admin = InlineKeyboardMarkup()
    kb_admin.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"admin_approve_{user_id}"))
    kb_admin.add(InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{user_id}"))
    kb_admin.add(InlineKeyboardButton("💰 Одобрить с изменением цены", callback_data=f"admin_price_{user_id}"))

    text_admin = f"📩 Новая реклама от @{ad['user_name']}:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    if "photo" in ad:
        bot.send_photo(ADMIN_CHAT_ID, ad["photo"], caption=text_admin, reply_markup=kb_admin)
    else:
        bot.send_message(ADMIN_CHAT_ID, text_admin, reply_markup=kb_admin)

# -----------------------------
# Обработка callback
# -----------------------------
def handle_callback(bot, call):
    data = load_ads()
    parts = call.data.split("_")
    prefix = parts[0]
    action = parts[1]
    user_id = parts[-1]

    # --- CALLBACK для пользователя ---
    if prefix == "user" and user_id in data.get("pending", {}):
        ad = data["pending"][user_id]

        if action == "photo":
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            if parts[2] == "yes":
                ad["step"] = "photo"
                bot.send_message(int(user_id), "Отправьте фото:")
            else:
                ad["step"] = "count"
                bot.send_message(int(user_id), "Введите количество показов рекламы:")
            save_ads(data)
            return

        if action == "confirm":
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(int(user_id), "✅ Ваша заявка отправлена на проверку админам!")
            # здесь не публикуем, ждём оплаты после одобрения
            return

        if action == "cancel":
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(int(user_id), "❌ Ваша заявка отменена.")
            del data["pending"][user_id]
            save_ads(data)
            return

        if action.startswith("change"):
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            if action.endswith("text"):
                ad["step"] = "text"
                bot.send_message(int(user_id), "Введите новый текст рекламы:")
            elif action.endswith("photo"):
                ad["step"] = "photo"
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"user_photo_yes_{user_id}"))
                kb.add(InlineKeyboardButton("Без фото", callback_data=f"user_photo_no_{user_id}"))
                bot.send_message(int(user_id), "Хотите прикрепить фото?", reply_markup=kb)
            elif action.endswith("count"):
                ad["step"] = "count"
                bot.send_message(int(user_id), "Введите новое количество показов рекламы:")
            save_ads(data)
            return

    # --- CALLBACK для админов ---
    if prefix == "admin":
        ad = data["pending"].get(user_id)
        if not ad:
            bot.answer_callback_query(call.id, "❌ Ошибка! Заявка не найдена.")
            return

        # одобрить
        if action == "approve":
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, f"✅ Заявка @{ad['user_name']} одобрена. Отправляем пользователю счет.")
            send_invoice(bot, user_id, ad)
            return

        # отклонить
        if action == "reject":
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, f"❌ Заявка @{ad['user_name']} отклонена.")
            bot.send_message(int(user_id), "❌ Ваша реклама отклонена админами.")
            del data["pending"][user_id]
            save_ads(data)
            return

        # одобрить с изменением цены
        if action == "price":
            bot.send_message(call.message.chat.id, f"Введите новую цену за один показ для @{ad['user_name']}:")
            ad["step"] = "set_admin_price"
            save_ads(data)
            return

# -----------------------------
# Создание invoice для оплаты
# -----------------------------
def send_invoice(bot, user_id, ad):
    data = load_ads()
    price_per_show = data.get("price", PRICE_DEFAULT)
    total_amount = int(ad["count"] * price_per_show * 100)  # Stars в сотых
    bot.send_invoice(
        chat_id=int(user_id),
        title="Оплата рекламы",
        description=f"{ad['text']}\nПоказов: {ad['count']}",
        provider_token=os.environ.get("PROVIDER_TOKEN"),  # твой токен Telegram Payments
        currency="USD",
        prices=[LabeledPrice(label="Реклама", amount=total_amount)],
        start_parameter="ads_payment",
        payload=f"ads_{user_id}"
    )

# -----------------------------
# Показ рекламы пользователю
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

# -----------------------------
# Команда /priser — изменить базовую цену
# -----------------------------
def handle_price(bot, message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "❌ Команда доступна только в админском чате!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        data = load_ads()
        bot.send_message(message.chat.id, f"Текущая цена за 1 показ: {data.get('price', PRICE_DEFAULT)}")
        return
    try:
        price = float(parts[1])
        data = load_ads()
        data["price"] = price
        save_ads(data)
        bot.send_message(message.chat.id, f"✅ Базовая цена за 1 показ установлена: {price} Stars")
    except:
        bot.send_message(message.chat.id, "❌ Неверное число!")