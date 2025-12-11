import telebot
from telebot import types
import json
import os

DATA_FILE = "plugins/ads_data.json"
ADMIN_ID = 5791171535

# ---------------------------------------------
# Загрузка/сохранение данных
# ---------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": {}, "approved": [], "price": 1, "queue": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------------------------------------------
# Команда /priser — установка цены
# ---------------------------------------------
def handle_priser(bot, message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Используйте /priser <кол-во звезд за 1 рассылку>")
            return
        price = int(parts[1])
        data = load_data()
        data["price"] = price
        save_data(data)
        bot.reply_to(message, f"💰 Цена за 1 рекламу установлена: {price} ⭐")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ---------------------------------------------
# Команда /buy_ads — начало оформления
# ---------------------------------------------
def handle_buy_ads(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    data["pending"][user_id] = {
        "step": "text",
        "text": None,
        "photo": None,
        "count": None
    }
    save_data(data)
    bot.reply_to(message, "✏️ Отправьте текст вашей рекламы:")

# ---------------------------------------------
# Обработка сообщений пользователей в процессе рекламы
# ---------------------------------------------
def handle(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data.get("pending", {}):
        return  # не в процессе

    state = data["pending"][user_id]

    # 1️⃣ Ввод текста
    if state["step"] == "text":
        state["text"] = message.text
        state["step"] = "photo"
        save_data(data)

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Добавить фото", callback_data="ads_photo_yes"))
        markup.add(types.InlineKeyboardButton("Без фото", callback_data="ads_photo_no"))
        bot.reply_to(message, "Хотите добавить фото к рекламе?", reply_markup=markup)
        return

    # 2️⃣ Фото
    if state["step"] == "photo":
        if message.content_type == "photo":
            state["photo"] = message.photo[-1].file_id
            state["step"] = "count"
            save_data(data)
            bot.reply_to(message, "Введите количество рассылок:")
        elif message.text.lower() == "без фото":
            state["photo"] = None
            state["step"] = "count"
            save_data(data)
            bot.reply_to(message, "Введите количество рассылок:")
        else:
            bot.reply_to(message, "❌ Пожалуйста, отправьте фото или выберите 'Без фото'.")
        return

    # 3️⃣ Количество рассылок
    if state["step"] == "count":
        try:
            count = int(message.text)
            if count < 1:
                raise ValueError
            state["count"] = count
            state["step"] = "confirm"
            save_data(data)
        except:
            bot.reply_to(message, "❌ Введите корректное число рассылок.")
            return

        # Показать превью и кнопки
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Да, верно", callback_data=f"ads_confirm_{user_id}"),
            types.InlineKeyboardButton("Изменить текст", callback_data=f"ads_edittext_{user_id}")
        )
        markup.add(
            types.InlineKeyboardButton("Изменить число", callback_data=f"ads_editcount_{user_id}"),
            types.InlineKeyboardButton("Изменить фото", callback_data=f"ads_editphoto_{user_id}")
        )
        preview = f"📢 Превью вашей рекламы:\n\n{state['text']}\nКоличество рассылок: {state['count']}"
        if state["photo"]:
            bot.send_photo(message.chat.id, state["photo"], caption=preview, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, preview, reply_markup=markup)
        return

# ---------------------------------------------
# Обработка callback'ов кнопок
# ---------------------------------------------
def callback(bot, call):
    data = load_data()
    user_id = call.data.split("_")[-1]

    if call.data.startswith("ads_photo_yes"):
        data["pending"][str(call.from_user.id)]["step"] = "photo"
        save_data(data)
        bot.send_message(call.message.chat.id, "Отправьте фото:")
        return

    if call.data.startswith("ads_photo_no"):
        data["pending"][str(call.from_user.id)]["photo"] = None
        data["pending"][str(call.from_user.id)]["step"] = "count"
        save_data(data)
        bot.send_message(call.message.chat.id, "Введите количество рассылок:")
        return

    if call.data.startswith("ads_confirm_") and call.from_user.id == int(user_id):
        # Отправка на проверку админом
        ad = data["pending"].pop(user_id)
        save_data(data)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Да", callback_data=f"ads_admin_yes_{user_id}"),
            types.InlineKeyboardButton("Нет", callback_data=f"ads_admin_no_{user_id}")
        )
        bot.send_message(ADMIN_ID, f"📢 Новая реклама от {call.from_user.first_name}:\n\n{ad['text']}\nКоличество: {ad['count']}", reply_markup=markup)
        if ad["photo"]:
            bot.send_photo(ADMIN_ID, ad["photo"], caption=ad["text"], reply_markup=markup)
        return

    # Админ подтверждает
    if call.data.startswith("ads_admin_yes_") and call.from_user.id == ADMIN_ID:
        uid = call.data.split("_")[-1]
        ad = data["pending"].pop(uid, None)
        if not ad:
            ad = data.get("pending", {}).get(uid)
        if not ad:
            return
        data["approved"].append(ad)
        save_data(data)
        bot.send_message(int(uid), f"✅ Ваша реклама одобрена! Для запуска оплаты используйте /buy_ads")
        return

    # Админ отклоняет
    if call.data.startswith("ads_admin_no_") and call.from_user.id == ADMIN_ID:
        uid = call.data.split("_")[-1]
        ad = data["pending"].pop(uid)
        save_data(data)
        bot.send_message(int(uid), "❌ Ваша реклама отклонена. Исправьте и попробуйте снова.")
        return

# ---------------------------------------------
# Добавляем рекламу к каждому сообщению бота
# ---------------------------------------------
def append_ads(text, photo=None):
    """
    Выбирает одну рекламу из approved, чередует и возвращает текст и фото
    """
    data = load_data()
    if not data["approved"]:
        return text, photo

    ad = data["approved"].pop(0)
    data["approved"].append(ad)  # чередуем
    save_data(data)

    # Формируем сообщение
    ad_text = ad["text"]
    ad_photo = ad.get("photo", None)
    combined_text = f"{text}\n\n📢 Реклама:\n{ad_text}"
    return combined_text, ad_photo

# ---------------------------------------------
# Обёртки для main.py
# ---------------------------------------------
handle_buy = handle_buy_ads
handle_priser = handle_priser