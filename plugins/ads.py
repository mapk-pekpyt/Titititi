import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

DATA_FILE = "plugins/ads_data.json"
ADMIN_ID = 5791171535  # твой Telegram ID
DEFAULT_PRICE = 1  # по умолчанию 1 звезда за показ

# -----------------------------
# Загрузка/сохранение данных
# -----------------------------
def load_ads():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": {}, "approved": [], "price": DEFAULT_PRICE}

def save_ads(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------
# Команды
# -----------------------------
def handle_priser(bot, message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Только админ может устанавливать цену!")
        return
    parts = message.text.split()
    data = load_ads()
    if len(parts) < 2:
        bot.send_message(message.chat.id, f"Текущая цена за 1 показ: {data.get('price', DEFAULT_PRICE)} звезд")
        return
    try:
        price = float(parts[1])
        data['price'] = price
        save_ads(data)
        bot.send_message(message.chat.id, f"✅ Цена за 1 показ установлена: {price} звезд")
    except:
        bot.send_message(message.chat.id, "❌ Неверное число")

def handle_all(bot, message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_ads()
    text = "📋 Текущие рекламные задачи:\n\n"
    for uid, ad in data.get("pending", {}).items():
        text += f"Пользователь {ad['user_name']}:\nТекст: {ad.get('text','')}\nФото: {'есть' if ad.get('photo') else 'нет'}\nОсталось показов: {ad.get('count',0)}\n\n"
    if not data.get("pending"):
        text += "Задач нет."
    bot.send_message(message.chat.id, text)

def handle_buy(bot, message):
    if message.chat.type != "private":
        bot.send_message(message.chat.id, "❌ Реклама работает только в личных сообщениях бота!")
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    data["pending"][user_id] = {"step": "text", "user_name": message.from_user.username or message.from_user.first_name}
    save_ads(data)
    price = data.get("price", DEFAULT_PRICE)
    bot.send_message(message.chat.id, f"💰 Стоимость 1 показа: {price} звезд\n\n✏️ Введите текст вашей рекламы:")

# -----------------------------
# Обработка текстовых сообщений
# -----------------------------
def handle(bot, message):
    if message.chat.type != "private":
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    if user_id not in data.get("pending", {}):
        return
    ad = data["pending"][user_id]

    if ad["step"] == "text" and message.text:
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
        bot.send_message(message.chat.id, "Введите количество показов рекламы:")
        return

    if ad["step"] == "count":
        try:
            ad["count"] = int(message.text)
            ad["step"] = "confirm"
            save_ads(data)
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Все верно", callback_data=f"ads_confirm_{user_id}"))
            kb.add(InlineKeyboardButton("Изменить текст", callback_data=f"ads_change_text_{user_id}"))
            kb.add(InlineKeyboardButton("Изменить фото", callback_data=f"ads_change_photo_{user_id}"))
            kb.add(InlineKeyboardButton("Изменить количество", callback_data=f"ads_change_count_{user_id}"))
            bot.send_message(message.chat.id, f"Проверьте вашу рекламу:\n\n{ad['text']}", reply_markup=kb)
        except:
            bot.send_message(message.chat.id, "❌ Введите число показов")
        return

# -----------------------------
# Callback
# -----------------------------
def handle_callback(bot, call):
    data = load_ads()
    parts = call.data.split("_")
    action = parts[1]
    user_id = parts[-1]
    if user_id not in data["pending"]:
        bot.answer_callback_query(call.id, "Ошибка!")
        return
    ad = data["pending"][user_id]

    if action == "confirm" and call.from_user.id == ADMIN_ID:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        approved_ad = ad.copy()
        data["approved"].append(approved_ad)
        del data["pending"][user_id]
        save_ads(data)
        price = data.get("price", DEFAULT_PRICE)
        if price <= 0:
            bot.send_message(int(user_id), "✅ Ваша реклама бесплатно опубликована!")
        else:
            bot.send_invoice(
                chat_id=int(user_id),
                title="Оплата рекламы",
                description=f"{ad['text']}\nПоказов: {ad['count']}",
                provider_token=os.environ.get("PROVIDER_TOKEN"),
                currency="USD",
                prices=[LabeledPrice(label="Реклама", amount=int(ad['count']*price*100))]
            )
        bot.send_message(ADMIN_ID, f"Реклама от {ad['user_name']} одобрена!")
        return

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

    if action == "photo":
        if parts[2] == "yes":
            ad["step"] = "photo"
            bot.send_message(int(user_id), "Отправьте фото:")
        else:
            ad["step"] = "count"
            bot.send_message(int(user_id), "Введите количество показов рекламы:")
        save_ads(data)

# -----------------------------
# Прикрепление рекламы к сообщениям
# -----------------------------
def send_random_ads(bot, chat_id):
    data = load_ads()
    if not data.get("approved"):
        return
    ad = data["approved"].pop(0)
    msg = ad["text"]
    if ad.get("photo"):
        bot.send_photo(chat_id, ad["photo"], caption=msg)
    else:
        bot.send_message(chat_id, msg)
    ad["count"] -= 1
    if ad["count"] > 0:
        data["approved"].append(ad)
    save_ads(data)