import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telebot import TeleBot

DATA_FILE = "plugins/ads_data.json"
ADMIN_CHAT_ID = -5037660983  # Твой админский чат
PROVIDER_TOKEN = os.environ.get("PROVIDER_TOKEN")  # токен Telegram Payment
CURRENCY = "USD"
PRICE_DEFAULT = 10  # базовая цена за сделку, можно менять через /priser

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
def handle_buy(bot: TeleBot, message):
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
def handle(bot: TeleBot, message):
    if message.chat.type != "private":
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    if user_id not in data["pending"]:
        return
    ad = data["pending"][user_id]

    # --- Ввод текста ---
    if ad["step"] == "text":
        ad["text"] = message.text
        ad["step"] = "photo"
        save_ads(data)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"ads_photo_yes_{user_id}"))
        kb.add(InlineKeyboardButton("Без фото", callback_data=f"ads_photo_no_{user_id}"))
        bot.send_message(message.chat.id, "Хотите прикрепить фото?", reply_markup=kb)
        return

    # --- Ввод фото ---
    if ad["step"] == "photo":
        if message.content_type == "photo":
            ad["photo"] = message.photo[-1].file_id
        ad["step"] = "count"
        save_ads(data)
        bot.send_message(message.chat.id, "Введите количество показов рекламы (например, 5):")
        return

    # --- Ввод количества показов ---
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
# Предпросмотр и кнопки
# -----------------------------
def send_confirmation(bot: TeleBot, user_id, ad):
    # Пользовательский предпросмотр
    kb_user = InlineKeyboardMarkup()
    kb_user.add(InlineKeyboardButton("Все верно", callback_data=f"user_confirm_{user_id}"))
    kb_user.add(InlineKeyboardButton("Изменить текст", callback_data=f"user_change_text_{user_id}"))
    if "photo" in ad:
        kb_user.add(InlineKeyboardButton("Изменить фото", callback_data=f"user_change_photo_{user_id}"))
    kb_user.add(InlineKeyboardButton("Изменить количество", callback_data=f"user_change_count_{user_id}"))
    kb_user.add(InlineKeyboardButton("Отменить", callback_data=f"user_cancel_{user_id}"))

    caption = f"Проверьте вашу рекламу:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    bot.send_message(int(user_id), caption, reply_markup=kb_user)

    # Админский предпросмотр
    kb_admin = InlineKeyboardMarkup()
    kb_admin.add(InlineKeyboardButton("Одобрить", callback_data=f"admin_approve_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Отклонить", callback_data=f"admin_reject_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Одобрить с ценой", callback_data=f"admin_price_{user_id}"))

    text = f"📩 Новая реклама от @{ad['user_name']}:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    if "photo" in ad:
        bot.send_photo(ADMIN_CHAT_ID, ad["photo"], caption=text, reply_markup=kb_admin)
    else:
        bot.send_message(ADMIN_CHAT_ID, text, reply_markup=kb_admin)

# -----------------------------
# Обработка callback
# -----------------------------
def handle_callback(bot: TeleBot, call):
    data = load_ads()
    parts = call.data.split("_")
    prefix = parts[0]
    action = parts[1]
    user_id = parts[-1]

    # Проверка существования заявки
    if user_id not in data.get("pending", {}):
        bot.answer_callback_query(call.id, "❌ Заявка не найдена")
        return
    ad = data["pending"][user_id]

    # --- Фото ---
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

    # --- Пользовательский предпросмотр ---
    if prefix == "user":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        if action == "confirm":
            ad["step"] = "waiting_admin"
            save_ads(data)
            bot.send_message(int(user_id), "✅ Заявка отправлена на модерацию админам!")
        elif action.startswith("change"):
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
            elif action.endswith("cancel"):
                del data["pending"][user_id]
                bot.send_message(int(user_id), "❌ Ваша заявка на рекламу отменена.")
        save_ads(data)
        return

    # --- Админский callback ---
    if prefix == "admin":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        if action == "approve":
            ad["step"] = "waiting_payment"
            save_ads(data)
            send_invoice(bot, user_id, ad)
            bot.send_message(call.message.chat.id, f"✅ Заявка @{ad['user_name']} одобрена, пользователь получил счет.")
        elif action == "reject":
            del data["pending"][user_id]
            save_ads(data)
            bot.send_message(call.message.chat.id, f"❌ Заявка @{ad['user_name']} отклонена.")
            bot.send_message(int(user_id), "❌ Ваша заявка на рекламу отклонена админами.")
        elif action == "price":
            ad["step"] = "set_admin_price"
            save_ads(data)
            bot.send_message(call.message.chat.id, f"Введите цену за всю сделку для @{ad['user_name']}:")
        return

# -----------------------------
# Обработка цены от админа
# -----------------------------
def handle_admin_price(bot: TeleBot, message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
    data = load_ads()
    for user_id, ad in data.get("pending", {}).items():
        if ad.get("step") == "set_admin_price":
            try:
                total_price = float(message.text)
                ad["price_override"] = total_price
                ad["step"] = "waiting_payment"
                save_ads(data)
                send_invoice(bot, user_id, ad)
                bot.send_message(message.chat.id, f"✅ Цена для @{ad['user_name']} установлена: {total_price} Stars за сделку. Пользователь получил счет.")
            except:
                bot.send_message(message.chat.id, "❌ Неверная цена!")
            break

# -----------------------------
# Отправка invoice пользователю
# -----------------------------
def send_invoice(bot: TeleBot, user_id, ad):
    data = load_ads()
    total_price = int(ad.get("price_override", data.get("price", PRICE_DEFAULT)) * 100)  # Telegram Stars в сотых
    bot.send_invoice(
        chat_id=int(user_id),
        title="Оплата рекламы",
        description=f"{ad['text']}\n📊 Показов: {ad['count']}",
        provider_token=PROVIDER_TOKEN,
        currency=CURRENCY,
        prices=[LabeledPrice(label="Реклама", amount=total_price)],
        start_parameter="ads_payment",
        payload=f"ads_{user_id}"
    )

# -----------------------------
# Показ рекламы пользователю
# -----------------------------
def send_random_ads(bot: TeleBot, chat_id):
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