import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

DATA_FILE = "plugins/ads_data.json"
ADMIN_ID = 5791171535  # твой Telegram ID

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
# Обработка сообщений от пользователя
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

# -----------------------------
# Отправка на подтверждение пользователю и админу
# -----------------------------
def send_confirmation(bot, user_id, ad):
    kb_user = InlineKeyboardMarkup()
    kb_user.add(InlineKeyboardButton("Все верно", callback_data=f"ads_confirm_{user_id}"))
    kb_user.add(InlineKeyboardButton("Изменить текст", callback_data=f"ads_change_text_{user_id}"))
    if "photo" in ad:
        kb_user.add(InlineKeyboardButton("Изменить фото", callback_data=f"ads_change_photo_{user_id}"))
    kb_user.add(InlineKeyboardButton("Изменить количество", callback_data=f"ads_change_count_{user_id}"))

    bot.send_message(int(user_id), f"Проверьте вашу рекламу:\n\n{ad['text']}\n📊 Показов: {ad['count']}", reply_markup=kb_user)

    # Уведомление админу
    kb_admin = InlineKeyboardMarkup()
    kb_admin.add(InlineKeyboardButton("Одобрить", callback_data=f"ads_confirm_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Изменить текст", callback_data=f"ads_change_text_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Изменить фото", callback_data=f"ads_change_photo_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Изменить количество", callback_data=f"ads_change_count_{user_id}"))

    text = f"📩 Новая реклама от {ad['user_name']}:\n\n{ad['text']}\n📊 Показов: {ad['count']}"
    if "photo" in ad:
        bot.send_photo(ADMIN_ID, ad["photo"], caption=text, reply_markup=kb_admin)
    else:
        bot.send_message(ADMIN_ID, text, reply_markup=kb_admin)

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

    # Подтверждение админом
    if action == "confirm" and call.from_user.id == ADMIN_ID:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        data["approved"].append(ad)
        del data["pending"][user_id]
        save_ads(data)
        bot.send_message(ADMIN_ID, f"✅ Реклама от {ad['user_name']} одобрена!")
        bot.send_message(int(user_id), "✅ Ваша реклама одобрена и будет опубликована!")
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