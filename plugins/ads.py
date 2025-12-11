import telebot
import json
import os
from telebot import types

DATA_FILE = "plugins/ads_data.json"

# Загружаем данные
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": {}, "approved": [], "price": 1}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------
# Обработка сообщений пользователей
# -----------------------------
def handle(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()

    # -----------------------------
    # 1. Новый пользователь начинает рекламу
    # -----------------------------
    if user_id not in data["pending"]:
        data["pending"][user_id] = {
            "step": "text",  # text -> confirm -> photo -> admin
            "text": "",
            "photo": None,
            "count": 1
        }
        save_data(data)
        bot.send_message(message.chat.id, "Отправьте текст вашей рекламы:")
        return

    user_ads = data["pending"][user_id]
    step = user_ads["step"]

    # -----------------------------
    # 2. Шаг: получение текста
    # -----------------------------
    if step == "text" and message.content_type == "text":
        user_ads["text"] = message.text
        user_ads["step"] = "confirm_text"
        save_data(data)

        # Кнопки: Продолжить / Изменить число / Изменить текст
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Продолжить", callback_data="ads_confirm_continue"),
            types.InlineKeyboardButton("✏️ Изменить число рассылок", callback_data="ads_confirm_change_count"),
            types.InlineKeyboardButton("📝 Изменить текст", callback_data="ads_confirm_change_text")
        )
        bot.send_message(message.chat.id,
                         f"Ваша реклама стоит {data['price']} звезд за одну рассылку.\n"
                         f"Текст:\n{message.text}\nВыберите действие:", reply_markup=markup)
        return

    # -----------------------------
    # 3. Шаг: получение фото
    # -----------------------------
    if step == "photo" and message.content_type == "photo":
        photo_id = message.photo[-1].file_id
        user_ads["photo"] = photo_id
        user_ads["step"] = "admin"
        save_data(data)

        # Отправляем админу (ваш ID: 5791171535)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Одобрить", callback_data=f"ads_admin_approve_{user_id}"),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f"ads_admin_reject_{user_id}")
        )
        bot.send_photo(5791171535, photo_id,
                       caption=f"Реклама от {message.from_user.first_name}:\n{user_ads['text']}",
                       reply_markup=markup)
        bot.send_message(message.chat.id, "Ожидайте одобрения администрации...")
        return

# -----------------------------
# Обработка callback кнопок
# -----------------------------
def callback(bot, call):
    user_id = str(call.from_user.id)
    data = load_data()

    # -----------------------------
    # 1. Пользователь подтверждает текст/количество
    # -----------------------------
    if call.data.startswith("ads_confirm_"):
        if user_id not in data["pending"]:
            bot.answer_callback_query(call.id, "Нет активной рекламы")
            return
        user_ads = data["pending"][user_id]

        if call.data == "ads_confirm_continue":
            user_ads["step"] = "photo"
            save_data(data)
            bot.send_message(call.message.chat.id, "Прикрепите фото рекламы:")
            bot.answer_callback_query(call.id)
            return

        if call.data == "ads_confirm_change_count":
            bot.send_message(call.message.chat.id, "Сколько рассылок вы хотите сделать?")
            user_ads["step"] = "change_count"
            save_data(data)
            bot.answer_callback_query(call.id)
            return

        if call.data == "ads_confirm_change_text":
            bot.send_message(call.message.chat.id, "Введите новый текст рекламы:")
            user_ads["step"] = "text"
            save_data(data)
            bot.answer_callback_query(call.id)
            return

    # -----------------------------
    # 2. Админ одобряет/отклоняет
    # -----------------------------
    if call.data.startswith("ads_admin_"):
        action, target_id = call.data.split("_")[2], call.data.split("_")[3]
        if target_id not in data["pending"]:
            bot.answer_callback_query(call.id, "Пользователь не найден")
            return
        user_ads = data["pending"][target_id]

        if action == "approve":
            user_ads["step"] = "payment"
            save_data(data)

            # Кнопка оплаты
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("💳 Оплатить рекламу", pay=True)
            )
            bot.send_message(int(target_id), "Ваша реклама одобрена. Оплатите для рассылки:", reply_markup=markup)
            bot.answer_callback_query(call.id)
            return

        if action == "reject":
            user_ads["step"] = "rejected"
            save_data(data)
            bot.send_message(int(target_id), "Ваша реклама отклонена. Пожалуйста, измените текст и попробуйте снова.")
            bot.answer_callback_query(call.id)
            return

# -----------------------------
# Генерация рекламы при каждом сообщении
# -----------------------------
def get_random_ad():
    data = load_data()
    if not data.get("approved"):
        return None
    # Берём случайную одобренную рекламу
    ad = data["approved"].pop(0)
    # возвращаем в конец для чередования
    data["approved"].append(ad)
    save_data(data)
    return ad

def send_ad(bot, chat_id):
    ad = get_random_ad()
    if not ad:
        return
    if ad.get("photo"):
        bot.send_photo(chat_id, ad["photo"], caption=ad["text"])
    else:
        bot.send_message(chat_id, ad["text"])