import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

DATA_FILE = "plugins/ads_data.json"
ADMIN_ID = 5791171535

# Дефолтная цена рекламы
PRICE_PER_SHOW = 1.0  # звезды за 1 показ, можно менять через /priser

# Загружаем данные
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "approved": [], "price": PRICE_PER_SHOW}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Установить цену
def set_price(price: float):
    data = load_data()
    data["price"] = price
    save_data(data)

# Начало покупки рекламы
def handle_buy(bot, message):
    data = load_data()
    user_id = str(message.from_user.id)
    bot.send_message(
        message.chat.id,
        f"💰 Стоимость рекламы за 1 показ: {data.get('price', PRICE_PER_SHOW)} ⭐\n"
        "Введите текст вашей рекламы:"
    )
    # Ставим в pending
    data["pending"][user_id] = {"step": "text"}
    save_data(data)

# Установка прайса через команду
def handle_pricer(bot, message):
    try:
        price = float(message.text.split()[1])
    except:
        bot.reply_to(message, "❌ Укажите цену цифрой после команды, например /pricer 0.1")
        return
    set_price(price)
    bot.reply_to(message, f"✅ Цена за 1 показ рекламы установлена: {price} ⭐")

# Основной обработчик рекламы
def handle(bot, message):
    user_id = str(message.from_user.id)
    data = load_data()
    pending = data["pending"].get(user_id)
    if not pending:
        return

    step = pending.get("step")

    if step == "text":
        pending["text"] = message.text
        pending["step"] = "photo_question"
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Да", callback_data=f"ads_photo_yes_{user_id}"),
            InlineKeyboardButton("Нет", callback_data=f"ads_photo_no_{user_id}")
        )
        bot.send_message(message.chat.id, "Добавить фото к рекламе?", reply_markup=kb)
        save_data(data)
        return

    if step == "photo":
        if message.content_type == "photo":
            # берем самое большое фото
            pending["photo_file_id"] = message.photo[-1].file_id
            pending["step"] = "count"
            bot.send_message(message.chat.id, "Введите количество показов рекламы (числом):")
        else:
            bot.send_message(message.chat.id, "❌ Пришлите фото или /пропустить для продолжения без фото.")
        save_data(data)
        return

    if step == "count":
        try:
            cnt = int(message.text)
            pending["count"] = cnt
            pending["step"] = "confirm"
        except:
            bot.send_message(message.chat.id, "❌ Введите число показов цифрой.")
            return

        # показываем превью и кнопки
        text = pending["text"]
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ Всё верно", callback_data=f"ads_confirm_{user_id}"),
            InlineKeyboardButton("✏️ Изменить текст", callback_data=f"ads_edit_text_{user_id}"),
            InlineKeyboardButton("🔢 Изменить число", callback_data=f"ads_edit_count_{user_id}"),
            InlineKeyboardButton("🖼️ Изменить фото", callback_data=f"ads_edit_photo_{user_id}")
        )
        if "photo_file_id" in pending:
            bot.send_photo(message.chat.id, pending["photo_file_id"], caption=text, reply_markup=kb)
        else:
            bot.send_message(message.chat.id, f"📢 Превью рекламы:\n\n{text}", reply_markup=kb)
        save_data(data)
        return

# Callback обработка кнопок
def callback(bot, call):
    data = load_data()
    user_id = call.data.split("_")[-1]

    # Фото да/нет
    if call.data.startswith("ads_photo_yes"):
        data["pending"][user_id]["step"] = "photo"
        save_data(data)
        bot.edit_message_text("📸 Отправьте фото рекламы:", call.message.chat.id, call.message.message_id)
        return
    if call.data.startswith("ads_photo_no"):
        data["pending"][user_id]["step"] = "count"
        save_data(data)
        bot.edit_message_text("Введите количество показов рекламы (числом):", call.message.chat.id, call.message.message_id)
        return

    # Редактирование
    if call.data.startswith("ads_edit_text"):
        data["pending"][user_id]["step"] = "text"
        save_data(data)
        bot.edit_message_text("Введите новый текст рекламы:", call.message.chat.id, call.message.message_id)
        return
    if call.data.startswith("ads_edit_count"):
        data["pending"][user_id]["step"] = "count"
        save_data(data)
        bot.edit_message_text("Введите количество показов рекламы (числом):", call.message.chat.id, call.message.message_id)
        return
    if call.data.startswith("ads_edit_photo"):
        data["pending"][user_id]["step"] = "photo"
        save_data(data)
        bot.edit_message_text("Отправьте новое фото рекламы:", call.message.chat.id, call.message.message_id)
        return

    # Подтверждение пользователем → на проверку админу
    if call.data.startswith("ads_confirm"):
        ad = data["pending"][user_id]
        del data["pending"][user_id]
        # Отправляем админу
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ Одобрить", callback_data=f"ads_admin_yes_{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"ads_admin_no_{user_id}")
        )
        if "photo_file_id" in ad:
            bot.send_photo(ADMIN_ID, ad.get("photo_file_id"), caption=ad["text"], reply_markup=kb)
        else:
            bot.send_message(ADMIN_ID, ad["text"], reply_markup=kb)
        save_data(data)
        bot.edit_message_text("⏳ Реклама отправлена на проверку администрации", call.message.chat.id, call.message.message_id)
        return

    # Админ проверка
    if call.data.startswith("ads_admin_yes"):
        ad_user_id = call.data.split("_")[-1]
        # Добавляем в approved
        ad = {"user_id": ad_user_id, **data.get("pending", {}).get(ad_user_id, {})}
        if "approved" not in data:
            data["approved"] = []
        data["approved"].append(ad)
        save_data(data)
        # Сообщаем пользователю
        price = data.get("price", PRICE_PER_SHOW)
        if price <= 0:
            bot.send_message(ad_user_id, "✅ Ваша реклама бесплатно опубликована.")
        else:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton(f"💰 Оплатить {price} ⭐", pay=True))
            bot.send_message(ad_user_id, "✅ Ваша реклама одобрена. Оплатите для публикации:", reply_markup=kb)
        bot.edit_message_text("✅ Реклама одобрена", call.message.chat.id, call.message.message_id)
        return

    if call.data.startswith("ads_admin_no"):
        ad_user_id = call.data.split("_")[-1]
        bot.send_message(ad_user_id, "❌ Ваша реклама отклонена. Добавьте комментарий:")
        bot.edit_message_text("❌ Реклама отклонена", call.message.chat.id, call.message.message_id)
        return

# Отправка рекламы с каждым сообщением бота
def send_ads(bot, chat_id, message_text):
    data = load_data()
    approved = data.get("approved", [])
    if not approved:
        return

    # Выбираем первую рекламу, отправляем и сдвигаем очередь
    ad = approved.pop(0)
    approved.append(ad)
    data["approved"] = approved
    save_data(data)

    text = ad["text"]
    if "photo_file_id" in ad:
        bot.send_photo(chat_id, ad["photo_file_id"], caption=text)
    else:
        bot.send_message(chat_id, text)