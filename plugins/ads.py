import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

DATA_FILE = "plugins/ads_data.json"
ADMIN_CHAT_ID = -5037660983  # Админский чат
ADMIN_IDS = [5791171535]     # Личные админы
DEFAULT_PRICE = 1.0           # Цена по умолчанию за 1 показ
PROVIDER_TOKEN = os.environ.get("PROVIDER_TOKEN")  # Telegram Payment Token

def load_ads():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": {}, "approved": [], "price": DEFAULT_PRICE}

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
# Обработка текстовых сообщений и фото
# -----------------------------
def handle(bot, message):
    if message.chat.type != "private":
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    if user_id not in data["pending"]:
        return
    ad = data["pending"][user_id]

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
        bot.send_message(message.chat.id, "📊 Введите количество показов рекламы (например, 5):")
        return

    if ad["step"] == "count":
        try:
            ad["count"] = int(message.text)
            ad["step"] = "confirm"
            save_ads(data)
            send_confirmation(bot, user_id, ad)
        except:
            bot.send_message(message.chat.id, "❌ Введите число показов!")

# -----------------------------
# Предпросмотр и кнопки пользователю и админу
# -----------------------------
def send_confirmation(bot, user_id, ad):
    # Пользователь
    kb_user = InlineKeyboardMarkup()
    kb_user.add(InlineKeyboardButton("✅ Все верно", callback_data=f"ads_confirm_{user_id}"))
    kb_user.add(InlineKeyboardButton("✏️ Изменить текст", callback_data=f"ads_change_text_{user_id}"))
    if "photo" in ad:
        kb_user.add(InlineKeyboardButton("🖼 Изменить фото", callback_data=f"ads_change_photo_{user_id}"))
    kb_user.add(InlineKeyboardButton("🔢 Изменить количество", callback_data=f"ads_change_count_{user_id}"))
    kb_user.add(InlineKeyboardButton("❌ Отменить заявку", callback_data=f"ads_cancel_{user_id}"))

    msg = f"📋 Проверьте вашу рекламу:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    if "photo" in ad:
        bot.send_photo(int(user_id), ad["photo"], caption=msg, reply_markup=kb_user)
    else:
        bot.send_message(int(user_id), msg, reply_markup=kb_user)

# Админский чат
    kb_admin = InlineKeyboardMarkup()
    kb_admin.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"ads_admin_approve_{user_id}"))
    kb_admin.add(InlineKeyboardButton("💰 Одобрить с ценой", callback_data=f"ads_admin_price_{user_id}"))
    kb_admin.add(InlineKeyboardButton("❌ Отклонить", callback_data=f"ads_admin_reject_{user_id}"))

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
    action = parts[1]
    user_id = parts[-1]

    ad = data["pending"].get(user_id)
    if not ad:
        bot.answer_callback_query(call.id, "❌ Ошибка!")
        return

    # Фото
    if action == "photo":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        if parts[2] == "yes":
            ad["step"] = "photo"
            bot.send_message(int(user_id), "📷 Отправьте фото:")
        else:
            ad["step"] = "count"
            bot.send_message(int(user_id), "📊 Введите количество показов рекламы:")
        save_ads(data)
        return

    # Пользователь
    if action == "confirm":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(int(user_id), "✅ Заявка подтверждена! Ожидайте одобрения админов.")
        send_confirmation(bot, user_id, ad)  # Отправка в админский чат
        return

    if action == "cancel":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        del data["pending"][user_id]
        save_ads(data)
        bot.send_message(int(user_id), "❌ Заявка отменена!")
        return

    if action.startswith("change"):
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        if action.endswith("text"):
            ad["step"] = "text"
            bot.send_message(int(user_id), "✏️ Введите новый текст рекламы:")
        elif action.endswith("photo"):
            ad["step"] = "photo"
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"ads_photo_yes_{user_id}"))
            kb.add(InlineKeyboardButton("Без фото", callback_data=f"ads_photo_no_{user_id}"))
            bot.send_message(int(user_id), "Хотите прикрепить фото?", reply_markup=kb)
        elif action.endswith("count"):
            ad["step"] = "count"
            bot.send_message(int(user_id), "🔢 Введите новое количество показов рекламы:")
        save_ads(data)
        return

    # Админский чат — только админский чат
    if call.message.chat.id != ADMIN_CHAT_ID:
        return

    if action == "admin":
        sub_action = parts[2]
        if sub_action == "approve":
            # Одобрение — выставляем цену и готовим к оплате
            ad_data = data["pending"].get(user_id)
            if ad_data:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                price = data.get("price", DEFAULT_PRICE) * ad_data["count"]
                ad_data["total_price"] = price
                # Отправка счета пользователю
                bot.send_invoice(
                    chat_id=int(user_id),
                    title="Оплата рекламы",
                    description=f"{ad_data['text']}\n📊 Показов: {ad_data['count']}",
                    provider_token=PROVIDER_TOKEN,
                    currency="USD",
                    prices=[LabeledPrice(label="Реклама", amount=int(price*100))],
                    start_parameter="ads_payment",
                    payload=f"ads_{user_id}"
                )
        elif sub_action == "price":
            bot.send_message(ADMIN_CHAT_ID, f"Введите новую цену за всю сделку в Stars для @{ad['user_name']}:")
        elif sub_action == "reject":
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(int(user_id), "❌ Ваша заявка на рекламу отклонена админом.")
            del data["pending"][user_id]
            save_ads(data)

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
# Команда /priser — установить базовую цену (только в админском чате)
# -----------------------------
def handle_price(bot, message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "❌ Только админ может установить цену!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, f"Текущая базовая цена: {load_ads().get('price', DEFAULT_PRICE)} Stars")
        return
    try:
        price = float(parts[1])
        data = load_ads()
        data['price'] = price
        save_ads(data)
        bot.send_message(message.chat.id, f"✅ Базовая цена за 1 показ установлена: {price} Stars")
    except:
        bot.send_message(message.chat.id, "❌ Неверное число")