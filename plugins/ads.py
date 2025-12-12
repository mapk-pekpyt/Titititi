import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

DATA_FILE = "plugins/ads_data.json"
ADMIN_CHAT_ID = -5037660983  # Админский групповой чат
PRICE_PER_DEAL = 1  # базовая цена за всю сделку (можно менять командой /priser)
ADMIN_IDS = [5791171535]  # Дополнительно можно добавлять конкретных админов

PROVIDER_TOKEN = os.environ.get("PROVIDER_TOKEN")  # Telegram Stars токен

def load_ads():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": {}, "approved": [], "price": PRICE_PER_DEAL}

def save_ads(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------
# /buy_ads — старт
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
# Обработка текста и фото от пользователя
# -----------------------------
def handle(bot, message):
    if message.chat.type != "private":
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    if user_id not in data["pending"]:
        return
    ad = data["pending"][user_id]

    # Текст рекламы
    if ad["step"] == "text":
        ad["text"] = message.text
        ad["step"] = "photo"
        save_ads(data)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"ads_photo_yes_{user_id}"))
        kb.add(InlineKeyboardButton("Без фото", callback_data=f"ads_photo_no_{user_id}"))
        bot.send_message(message.chat.id, "Хотите прикрепить фото?", reply_markup=kb)
        return

    # Фото
    if ad["step"] == "photo":
        if message.content_type == "photo":
            ad["photo"] = message.photo[-1].file_id
        ad["step"] = "count"
        save_ads(data)
        bot.send_message(message.chat.id, "Введите количество показов рекламы (например, 5):")
        return

    # Количество показов
    if ad["step"] == "count":
        try:
            ad["count"] = int(message.text)
            ad["step"] = "confirm"
            save_ads(data)
            send_user_confirmation(bot, user_id, ad)
        except:
            bot.send_message(message.chat.id, "❌ Введите число показов!")

# -----------------------------
# Предпросмотр пользователю и отправка в админ чат
# -----------------------------
def send_user_confirmation(bot, user_id, ad):
    kb_user = InlineKeyboardMarkup()
    kb_user.add(InlineKeyboardButton("Все верно", callback_data=f"ads_confirm_{user_id}"))
    kb_user.add(InlineKeyboardButton("Изменить текст", callback_data=f"ads_change_text_{user_id}"))
    kb_user.add(InlineKeyboardButton("Изменить фото", callback_data=f"ads_change_photo_{user_id}"))
    kb_user.add(InlineKeyboardButton("Изменить количество", callback_data=f"ads_change_count_{user_id}"))
    kb_user.add(InlineKeyboardButton("Отменить", callback_data=f"ads_cancel_{user_id}"))

    text_preview = f"📋 Проверьте вашу рекламу:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    if "photo" in ad:
        bot.send_photo(int(user_id), ad["photo"], caption=text_preview, reply_markup=kb_user)
    else:
        bot.send_message(int(user_id), text_preview, reply_markup=kb_user)

# -----------------------------
# Callback обработка
# -----------------------------
def handle_callback(bot, call):
    data = load_ads()
    parts = call.data.split("_")
    action = parts[1]
    user_id = parts[-1]

    if user_id not in data.get("pending", {}):
        bot.answer_callback_query(call.id, "❌ Ошибка!")
        return
    ad = data["pending"][user_id]

    # Фото
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

    # Изменения
    if action.startswith("change"):
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        if action.endswith("text"):
            ad["step"] = "text"
            bot.send_message(int(user_id), "Введите новый текст рекламы:")
        elif action.endswith("photo"):
            ad["step"] = "photo"
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"ads_photo_yes_{user_id}"))
            kb.add(InlineKeyboardButton("Без фото", callback_data=f"ads_photo_no_{user_id}"))
            bot.send_message(int(user_id), "Хотите прикрепить фото?", reply_markup=kb)
        elif action.endswith("count"):
            ad["step"] = "count"
            bot.send_message(int(user_id), "Введите новое количество показов рекламы:")
        save_ads(data)
        return

    # Отмена заявки
    if action == "cancel":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        del data["pending"][user_id]
        save_ads(data)
        bot.send_message(int(user_id), "❌ Ваша заявка на рекламу отменена.")
        return

    # Подтверждение пользователем → отправка на модерацию
    if action == "confirm":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        send_to_admin(bot, ad, user_id)
        bot.send_message(int(user_id), "📨 Ваша реклама отправлена на модерацию. После одобрения вы сможете оплатить показ.")
        return

# -----------------------------
# Отправка заявки в админ чат
# -----------------------------
def send_to_admin(bot, ad, user_id):
    kb_admin = InlineKeyboardMarkup()
    kb_admin.add(InlineKeyboardButton("Одобрить", callback_data=f"ads_admin_approve_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Отклонить", callback_data=f"ads_admin_reject_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Одобрить с ценой", callback_data=f"ads_admin_price_{user_id}"))

    text = f"📩 Новая заявка от @{ad['user_name']}:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    if "photo" in ad:
        bot.send_photo(ADMIN_CHAT_ID, ad["photo"], caption=text, reply_markup=kb_admin)
    else:
        bot.send_message(ADMIN_CHAT_ID, text, reply_markup=kb_admin)

# -----------------------------
# Обработка админских callback
# -----------------------------
def handle_admin(bot, call):
    data = load_ads()
    parts = call.data.split("_")
    action = parts[2]
    user_id = parts[-1]

    if user_id not in data.get("pending", {}):
        bot.answer_callback_query(call.id, "❌ Ошибка!")
        return
    ad = data["pending"][user_id]

    # Одобрить без изменения цены
    if action == "approve":
        ad["step"] = "payment"
        data["pending"][user_id] = ad
        save_ads(data)
        bot.send_message(int(user_id), f"✅ Ваша реклама одобрена. Общая стоимость сделки: {PRICE_PER_DEAL} ⭐. Оплатите для начала показа.")
        send_invoice(bot, ad, user_id, PRICE_PER_DEAL)
        return

    # Отклонить
    if action == "reject":
        del data["pending"][user_id]
        save_ads(data)
        bot.send_message(int(user_id), "❌ Ваша заявка отклонена администратором.")
        return

    # Одобрить с изменением цены
    if action == "price":
        bot.send_message(int(call.from_user.id), "Введите новую цену сделки для этой рекламы:")
        # Сохраняем состояние, что админ редактирует цену
        ad["step"] = "set_price"
        data["pending"][user_id] = ad
        save_ads(data)
        return

# -----------------------------
# Установка новой цены админом
# -----------------------------
def set_admin_price(bot, message):
    user_id = None
    data = load_ads()
    # Ищем заявку в состоянии "set_price"
    for uid, ad in data.get("pending", {}).items():
        if ad.get("step") == "set_price":
            user_id = uid
            break
    if not user_id:
        return
    try:
        price = float(message.text)
        ad = data["pending"][user_id]
        ad["step"] = "payment"
        data["pending"][user_id] = ad
        save_ads(data)
        bot.send_message(int(user_id), f"✅ Администратор установил новую цену сделки: {price} ⭐. Оплатите для начала показа.")
        send_invoice(bot, ad, user_id, price)
    except:
        bot.send_message(message.chat.id, "❌ Введите корректное число.")

# -----------------------------
# Отправка invoice пользователю
# -----------------------------
def send_invoice(bot, ad, user_id, price):
    bot.send_invoice(
        chat_id=int(user_id),
        title="Оплата рекламы",
        description=f"{ad['text']}\n📊 Показов: {ad['count']}",
        provider_token=PROVIDER_TOKEN,
        currency="USD",
        prices=[LabeledPrice(label="Реклама", amount=int(price*100))],
        start_parameter="ads_payment",
        payload="ads_payment"
    )

# -----------------------------
# Рассылка рекламы после успешной оплаты
# -----------------------------
def handle_successful(bot, message):
    user_id = str(message.from_user.id)
    data = load_ads()
    if user_id not in data.get("pending", {}):
        return
    ad = data["pending"][user_id]
    # Добавляем в очередь рассылки
    data["approved"].append(ad)
    del data["pending"][user_id]
    save_ads(data)
    bot.send_message(int(user_id), "✅ Оплата прошла успешно! Ваша реклама начнет показ.")

# -----------------------------
# Показ рекламы
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
# /priser — изменить базовую цену сделки
# -----------------------------
def handle_price(bot, message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "❌ Команда доступна только в админ-чате.")
        return
    data = load_ads()
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, f"Текущая базовая цена сделки: {data.get('price', PRICE_PER_DEAL)} ⭐")
        return
    try:
        price = float(parts[1])
        data['price'] = price
        save_ads(data)
        bot.send_message(message.chat.id, f"✅ Базовая цена сделки установлена: {price} ⭐")
    except:
        bot.send_message(message.chat.id, "❌ Введите корректное число.")