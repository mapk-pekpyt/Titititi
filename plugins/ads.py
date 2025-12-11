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
# Команда /buy_ads
# -----------------------------
def handle_buy(bot, message):
    if message.chat.type != "private":
        bot.send_message(message.chat.id, "❌ Реклама работает только в ЛС бота!")
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    data["pending"][user_id] = {"step": "text", "user_name": message.from_user.username or message.from_user.first_name}
    save_ads(data)
    bot.send_message(message.chat.id, "✏️ Отправьте текст вашей рекламы:")

# -----------------------------
# Обработка сообщений пользователя
# -----------------------------
def handle(bot, message):
    if message.chat.type != "private":
        return
    user_id = str(message.from_user.id)
    data = load_ads()
    if user_id not in data.get("pending", {}):
        return

    ad = data["pending"][user_id]

    # ---------------- Текст рекламы ----------------
    if ad["step"] == "text":
        ad["text"] = message.text
        ad["step"] = "photo"
        save_ads(data)

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"ads_photo_yes_{user_id}"))
        kb.add(InlineKeyboardButton("Без фото", callback_data=f"ads_photo_no_{user_id}"))
        bot.send_message(message.chat.id, "Хотите прикрепить фото?", reply_markup=kb)
        return

    # ---------------- Фото ----------------
    if ad["step"] == "photo":
        if message.content_type == "photo":
            ad["photo"] = message.photo[-1].file_id
            ad["step"] = "confirm"
            save_ads(data)
            send_confirmation(bot, user_id, ad)
            return
        else:
            bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте фото или нажмите 'Без фото' на кнопках.")
            return

# -----------------------------
# Кнопки для подтверждения и изменения
# -----------------------------
def handle_callback(bot, call):
    data = load_ads()
    parts = call.data.split("_")
    action = parts[1]
    user_id = parts[-1]

    if user_id not in data["pending"]:
        bot.answer_callback_query(call.id, "❌ Ошибка!")
        return

    ad = data["pending"][user_id]

    # ---------------- Фото ----------------
    if action == "photo":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        if parts[2] == "yes":
            ad["step"] = "photo"
            bot.send_message(int(user_id), "Отправьте фото:")
        else:
            ad["step"] = "confirm"
            send_confirmation(bot, user_id, ad)
        save_ads(data)
        return

    # ---------------- Подтверждение ----------------
    if action == "confirm" and call.from_user.id == ADMIN_ID:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        data["approved"].append(ad)
        del data["pending"][user_id]
        save_ads(data)
        bot.send_message(ADMIN_ID, f"✅ Реклама от {ad['user_name']} одобрена и добавлена в очередь!")
        bot.send_message(int(user_id), "✅ Ваша реклама одобрена и будет опубликована!")
        return

    # ---------------- Изменения ----------------
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
        save_ads(data)
        return

# -----------------------------
# Отправка подтверждения пользователю и администратору
# -----------------------------
def send_confirmation(bot, user_id, ad):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Все верно", callback_data=f"ads_confirm_{user_id}"))
    kb.add(InlineKeyboardButton("Изменить текст", callback_data=f"ads_change_text_{user_id}"))
    if "photo" in ad:
        kb.add(InlineKeyboardButton("Изменить фото", callback_data=f"ads_change_photo_{user_id}"))

    bot.send_message(int(user_id), f"Проверьте вашу рекламу:\n\n{ad['text']}", reply_markup=kb)

    # Уведомление админа
    admin_kb = InlineKeyboardMarkup()
    admin_kb.add(InlineKeyboardButton("Одобрить", callback_data=f"ads_confirm_{user_id}"))
    admin_kb.add(InlineKeyboardButton("Изменить текст", callback_data=f"ads_change_text_{user_id}"))
    bot.send_message(ADMIN_ID, f"📩 Новая реклама от {ad['user_name']}:\n\n{ad['text']}", reply_markup=admin_kb)

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
    ad["count"] = ad.get("count", 1) - 1
    if ad["count"] > 0:
        data["approved"].append(ad)
    save_ads(data)