import json
import os
import math
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

DATA_FILE = "plugins/ads_data.json"
ADMIN_CHAT_ID = -5037660983  # групповой чат админов
ADMIN_IDS = []  # можно добавлять отдельных админов при необходимости
PROVIDER_TOKEN = os.environ.get("PROVIDER_TOKEN")  # токен для оплаты Stars

DEFAULT_PRICE = 1  # по умолчанию цена за 1 показ

# -----------------------------
# Загрузка/сохранение данных
# -----------------------------
def load_ads():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": {}, "approved": [], "price": DEFAULT_PRICE, "history": {}, "chats": {}}

def save_ads(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------
# Команды администратора
# -----------------------------
def handle_priser(bot, message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ Только админ может устанавливать цену!")
        return
    parts = message.text.split()
    data = load_ads()
    if len(parts) < 2:
        bot.send_message(message.chat.id, f"Текущая цена за 1 показ: {data.get('price', DEFAULT_PRICE)} Stars")
        return
    try:
        price = float(parts[1])
        data['price'] = price
        save_ads(data)
        bot.send_message(message.chat.id, f"✅ Цена за 1 показ установлена: {price} Stars")
    except:
        bot.send_message(message.chat.id, "❌ Неверное число")

def handle_all(bot, message):
    if message.chat.id != ADMIN_CHAT_ID and message.from_user.id not in ADMIN_IDS:
        return
    data = load_ads()
    text = "📋 Текущие рекламные задачи:\n\n"
    for uid, ad in data.get("pending", {}).items():
        text += f"Пользователь @{ad.get('user_name')}:\nТекст: {ad.get('text','')}\nФото: {'есть' if ad.get('photo') else 'нет'}\nОсталось показов: {ad.get('count',0)}\n\n"
    if not data.get("pending"):
        text += "Задач нет."
    bot.send_message(message.chat.id, text)

def handle_chats(bot, message):
    if message.chat.id != ADMIN_CHAT_ID and message.from_user.id not in ADMIN_IDS:
        return
    data = load_ads()
    stats = data.get("chats", {})
    text = "📊 Активность бота по чатам:\n\n"
    for chat_id, info in stats.items():
        text += f"Чат ID: {chat_id}\nСообщений: {info.get('messages',0)}\n\n"
    if not stats:
        text += "Нет активности."
    bot.send_message(message.chat.id, text)

# -----------------------------
# Старт покупки рекламы
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
# Обработка текста и фото
# -----------------------------
def handle(bot, message):
    if message.chat.type != "private":
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    if user_id not in data.get("pending", {}):
        return
    ad = data["pending"][user_id]

    # Текст
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
        bot.send_message(message.chat.id, "Введите количество показов рекламы:")
        return

    # Количество показов
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
# Подтверждение и предпросмотр
# -----------------------------
def send_confirmation(bot, user_id, ad):
    kb_user = InlineKeyboardMarkup()
    kb_user.add(InlineKeyboardButton("✅ Все верно", callback_data=f"ads_confirm_{user_id}"))
    kb_user.add(InlineKeyboardButton("✏️ Изменить текст", callback_data=f"ads_change_text_{user_id}"))
    if "photo" in ad:
        kb_user.add(InlineKeyboardButton("📷 Изменить фото", callback_data=f"ads_change_photo_{user_id}"))
    kb_user.add(InlineKeyboardButton("🔢 Изменить количество", callback_data=f"ads_change_count_{user_id}"))
    kb_user.add(InlineKeyboardButton("❌ Отменить заявку", callback_data=f"ads_cancel_{user_id}"))

    msg = f"Проверьте вашу рекламу:\n\n{ad['text']}\n📊 Показов: {ad['count']}\n💰 Примерная стоимость: {ad['count']*load_ads().get('price', DEFAULT_PRICE)} Stars"
    bot.send_message(int(user_id), msg, reply_markup=kb_user)

    # Уведомление админам
    kb_admin = InlineKeyboardMarkup()
    kb_admin.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"ads_confirm_{user_id}"))
    kb_admin.add(InlineKeyboardButton("❌ Не одобрено", callback_data=f"ads_reject_{user_id}"))
    kb_admin.add(InlineKeyboardButton("💰 Установить цену", callback_data=f"ads_setprice_{user_id}"))

    text = f"📩 Новая реклама от @{ad.get('user_name')}:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    if "photo" in ad:
        bot.send_photo(ADMIN_CHAT_ID, ad["photo"], caption=text, reply_markup=kb_admin)
    else:
        bot.send_message(ADMIN_CHAT_ID, text, reply_markup=kb_admin)

# -----------------------------
# Callback
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
        # Создаём платеж
        price_per_show = load_ads().get("price", DEFAULT_PRICE)
        total_price = math.ceil(price_per_show * ad["count"])
        if total_price <= 0:
            # бесплатно
            data["approved"].append(ad)
            del data["pending"][user_id]
            save_ads(data)
            bot.send_message(int(user_id), "✅ Ваша реклама одобрена и будет опубликована бесплатно!")
        else:
            bot.send_invoice(
                chat_id=int(user_id),
                title="Оплата рекламы",
                description=f"{ad['text']}\nПоказов: {ad['count']}",
                provider_token=PROVIDER_TOKEN,
                currency="USD",
                prices=[LabeledPrice(label="Реклама", amount=int(total_price*100))],  # Telegram expects cents
                is_flexible=False
            )
        bot.send_message(ADMIN_CHAT_ID, f"✅ Реклама от @{ad.get('user_name')} одобрена и ожидает оплаты!")
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
            bot.send_message(int(user_id), "Введите новое количество показов:")
        save_ads(data)
        return

    if action == "cancel":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        del data["pending"][user_id]
        save_ads(data)
        bot.send_message(int(user_id), "❌ Ваша заявка на рекламу отменена.")

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