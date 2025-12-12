import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

DATA_FILE = "plugins/ads_data.json"
ADMIN_CHAT_ID = -5037660983  # групповой админский чат
PROVIDER_TOKEN = os.environ.get("PROVIDER_TOKEN")
DEFAULT_PRICE = 1  # по умолчанию цена за 1 показ

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
# /priser — установка цены (только админский чат)
# -----------------------------
def handle_price(bot, message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "❌ Только в админском чате!")
        return
    parts = message.text.split()
    data = load_ads()
    if len(parts) < 2:
        bot.send_message(message.chat.id, f"Текущая цена за 1 показ: {data.get('price', DEFAULT_PRICE)}")
        return
    try:
        price = float(parts[1])
        data['price'] = price
        save_ads(data)
        bot.send_message(message.chat.id, f"✅ Цена за 1 показ установлена: {price} звезд")
    except:
        bot.send_message(message.chat.id, "❌ Неверное число")

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

    # Шаг 1 — текст
    if ad["step"] == "text":
        ad["text"] = message.text
        ad["step"] = "photo"
        save_ads(data)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"ads_photo_yes_{user_id}"))
        kb.add(InlineKeyboardButton("Без фото", callback_data=f"ads_photo_no_{user_id}"))
        bot.send_message(message.chat.id, "Хотите прикрепить фото?", reply_markup=kb)
        return

    # Шаг 2 — фото
    if ad["step"] == "photo":
        if message.content_type == "photo":
            ad["photo"] = message.photo[-1].file_id
        ad["step"] = "count"
        save_ads(data)
        bot.send_message(message.chat.id, "Введите количество показов рекламы (например, 5):")
        return

    # Шаг 3 — количество показов
    if ad["step"] == "count":
        try:
            ad["count"] = int(message.text)
            ad["step"] = "confirm"
            save_ads(data)
            send_confirmation(bot, user_id, ad)
        except:
            bot.send_message(message.chat.id, "❌ Введите число показов!")

# -----------------------------
# Отправка на подтверждение
# -----------------------------
def send_confirmation(bot, user_id, ad):
    # Кнопки пользователю
    kb_user = InlineKeyboardMarkup()
    kb_user.add(InlineKeyboardButton("Все верно", callback_data=f"ads_confirm_{user_id}"))
    kb_user.add(InlineKeyboardButton("Отменить", callback_data=f"ads_cancel_{user_id}"))
    kb_user.add(InlineKeyboardButton("Изменить фото", callback_data=f"ads_change_photo_{user_id}"))
    kb_user.add(InlineKeyboardButton("Изменить количество", callback_data=f"ads_change_count_{user_id}"))

    bot.send_message(int(user_id), f"Проверьте вашу рекламу:\n\n{ad['text']}\n📊 Показов: {ad['count']}", reply_markup=kb_user)

    # Кнопки админам
    kb_admin = InlineKeyboardMarkup()
    kb_admin.add(InlineKeyboardButton("Одобрить", callback_data=f"ads_confirm_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Отклонить", callback_data=f"ads_reject_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Установить цену", callback_data=f"ads_setprice_{user_id}"))

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

    # Отмена пользователем
    if action == "cancel":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        del data["pending"][user_id]
        save_ads(data)
        bot.send_message(int(user_id), "❌ Ваша заявка на рекламу отменена.")
        return

    # Только админский чат
    if call.message.chat.id != ADMIN_CHAT_ID:
        bot.answer_callback_query(call.id, "❌ Только в админском чате!")
        return

    # Одобрение рекламы — создаём платеж
    if action == "confirm":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        price_per_show = data.get("price", DEFAULT_PRICE)
        total_price = int(ad["count"] * price_per_show * 100)
        bot.send_invoice(
            chat_id=int(user_id),
            title="Оплата рекламы",
            description=f"{ad['text']}\nПоказов: {ad['count']}",
            payload=f"ads_{user_id}",
            provider_token=PROVIDER_TOKEN,
            currency="USD",
            prices=[LabeledPrice(label="Реклама", amount=total_price)]
        )
        bot.send_message(ADMIN_CHAT_ID, f"💰 Отправлен счет пользователю @{ad['user_name']} на оплату {price_per_show} за 1 показ")
        return

    # Отклонение рекламы
    if action == "reject":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        del data["pending"][user_id]
        save_ads(data)
        bot.send_message(int(user_id), "❌ Ваша реклама отклонена администратором.")
        return

    # Изменение цены
    if action == "setprice":
        bot.send_message(ADMIN_CHAT_ID, f"Введите новую цену за 1 показ для @{ad['user_name']}:")
        # Логика установки новой цены можно добавить через отдельную команду /priser
        return

    # Изменения
    if action.startswith("change"):
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        if action.endswith("photo"):
            ad["step"] = "photo"
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"ads_photo_yes_{user_id}"))
            kb.add(InlineKeyboardButton("Без фото", callback_data=f"ads_photo_no_{user_id}"))
            bot.send_message(int(user_id), "Хотите прикрепить фото?", reply_markup=kb)
        elif action.endswith("count"):
            ad["step"] = "count"
            bot.send_message(int(user_id), "Введите новое количество показов:")
        save_ads(data)
        return

# -----------------------------
# Успешная оплата — переносим в approved
# -----------------------------
def handle_successful(bot, message):
    data = load_ads()
    user_id = str(message.from_user.id)
    # Находим заявку по payload (payload может быть "ads_<user_id>")
    ad_list = [ad for ad in data["pending"].values() if str(message.from_user.id) == user_id]
    if not ad_list:
        return
    ad = ad_list[0]
    data["approved"].append(ad)
    del data["pending"][user_id]
    save_ads(data)
    bot.send_message(user_id, "✅ Оплата прошла успешно! Ваша реклама будет опубликована.")

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