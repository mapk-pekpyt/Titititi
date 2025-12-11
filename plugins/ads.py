import json
import os
from telebot import types

DATA_FILE = "plugins/ads_data.json"
ADMIN_ID = 5791171535   # ← твой настоящий Telegram ID

# -----------------------------
# Загрузка / Сохранение
# -----------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"ads": [], "pending": {}, "price": 5, "counter": 0}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# -----------------------------
# Команда /priser — изменить цену
# -----------------------------
def handle_price(bot, msg):
    parts = msg.text.split()
    data = load_data()

    if msg.from_user.id != ADMIN_ID:
        bot.reply_to(msg, "У вас нет доступа.")
        return

    if len(parts) == 2 and parts[1].isdigit():
        data["price"] = int(parts[1])
        save_data(data)
        bot.reply_to(msg, f"Цена успешно установлена: {data['price']}⭐ за 1 рассылку.")
    else:
        bot.reply_to(msg, f"Текущая цена: {data['price']}⭐.\nИспользование: /priser 10")


# -----------------------------
# Начало покупки рекламы /buy_ads
# -----------------------------
def handle_buy(bot, msg):
    data = load_data()

    data["pending"][str(msg.from_user.id)] = {
        "stage": "wait_text",
        "text": None,
        "photo": None,
        "count": 1,
    }
    save_data(data)

    bot.send_message(msg.chat.id, "Отправьте текст вашей рекламы.")


# -----------------------------
# Главное сообщение после текста
# -----------------------------
def ask_confirm(bot, user_id, chat_id):
    data = load_data()
    entry = data["pending"][str(user_id)]
    price = entry["count"] * data["price"]

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Продолжить", callback_data="ads_continue"),
        types.InlineKeyboardButton("Изменить число", callback_data="ads_change_count"),
        types.InlineKeyboardButton("Изменить текст", callback_data="ads_change_text"),
    )

    bot.send_message(
        chat_id,
        f"Цена за {entry['count']} рассылок: {price} ⭐\n\nПродолжить?",
        reply_markup=kb
    )


# -----------------------------
# Обработка сообщений (текст/фото)
# -----------------------------
def handle(bot, msg):
    user_id = str(msg.from_user.id)
    data = load_data()

    if user_id not in data["pending"]:
        return  # это не реклама

    entry = data["pending"][user_id]

    # -----------------------------
    # 1. Получение текста
    # -----------------------------
    if entry["stage"] == "wait_text":
        entry["text"] = msg.text
        entry["stage"] = "confirm_main"
        save_data(data)
        ask_confirm(bot, msg.from_user.id, msg.chat.id)
        return

    # -----------------------------
    # 2. Изменение текста
    # -----------------------------
    if entry["stage"] == "change_text":
        entry["text"] = msg.text
        entry["stage"] = "confirm_main"
        save_data(data)
        ask_confirm(bot, msg.from_user.id, msg.chat.id)
        return

    # -----------------------------
    # 3. Изменение количества
    # -----------------------------
    if entry["stage"] == "change_count":
        if msg.text.isdigit() and int(msg.text) > 0:
            entry["count"] = int(msg.text)
            entry["stage"] = "confirm_main"
            save_data(data)
            ask_confirm(bot, msg.from_user.id, msg.chat.id)
        else:
            bot.reply_to(msg, "Введите число (например 5).")
        return

    # -----------------------------
    # 4. Ожидание фото
    # -----------------------------
    if entry["stage"] == "wait_photo":
        if not msg.photo:
            bot.reply_to(msg, "Пришлите фото.")
            return

        entry["photo"] = msg.photo[-1].file_id
        entry["stage"] = "wait_confirm"
        save_data(data)

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Подтвердить", callback_data="ads_final_confirm"))

        bot.send_message(msg.chat.id, "Фото получено. Подтвердить?", reply_markup=kb)
        return


# -----------------------------
# Обработка callback кнопок
# -----------------------------
def handle_callback(bot, call):
    user_id = str(call.from_user.id)
    data = load_data()

    # --- Кнопки не рекламы ---
    if not call.data.startswith("ads_") and not call.data.startswith("adm_"):
        return

    # --- Если реклама ---
    if user_id in data["pending"]:
        entry = data["pending"][user_id]

        # Продолжить → запросить фото
        if call.data == "ads_continue":
            entry["stage"] = "wait_photo"
            save_data(data)
            bot.edit_message_text("Отправьте фото для рекламы.", call.message.chat.id, call.message.message_id)
            return

        # Изменить число рассылок
        if call.data == "ads_change_count":
            entry["stage"] = "change_count"
            save_data(data)
            bot.edit_message_text("Введите новое количество рассылок:", call.message.chat.id, call.message.message_id)
            return

        # Изменить текст
        if call.data == "ads_change_text":
            entry["stage"] = "change_text"
            save_data(data)
            bot.edit_message_text("Введите новый текст рекламы:", call.message.chat.id, call.message.message_id)
            return

        # Пользователь подтвердил фото → ждём админа
        if call.data == "ads_final_confirm":
            bot.edit_message_text("Ожидайте одобрения администрации.", call.message.chat.id, call.message.message_id)

            # отправляем админу
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("Одобрить", callback_data=f"adm_yes_{user_id}"),
                types.InlineKeyboardButton("Отклонить", callback_data=f"adm_no_{user_id}")
            )

            bot.send_photo(
                ADMIN_ID,
                entry["photo"],
                caption=f"Реклама от {user_id}:\n\n{entry['text']}",
                reply_markup=kb
            )
            entry["stage"] = "waiting_admin"
            save_data(data)
            return

    # -----------------------------------
    #       А Д М И Н О В Ы Е  К Н О П К И
    # -----------------------------------
    if str(call.from_user.id) == str(ADMIN_ID):

        if call.data.startswith("adm_yes_"):
            uid = call.data.split("_")[2]
            entry = data["pending"][uid]

            price = entry["count"] * data["price"]

            # Отправляем пользователю оплату
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Оплатить", pay=True))

            bot.send_message(
                uid,
                f"Ваша реклама одобрена!\nСтоимость: {price} ⭐\nНажмите кнопку ниже для оплаты:",
                reply_markup=kb
            )

            entry["stage"] = "wait_payment"
            save_data(data)

            bot.edit_message_caption(
                caption="Одобрено.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
            return

        if call.data.startswith("adm_no_"):
            uid = call.data.split("_")[2]

            bot.send_message(ADMIN_ID, "Введите причину отказа:")
            data["pending"][uid]["stage"] = "wait_admin_comment"
            save_data(data)
            data["pending"][uid]["admin_msg"] = call.message.message_id
            save_data(data)
            return


# -------------------------------------
# Админ вводит комментарий отказа
# -------------------------------------
def handle_admin_comment(bot, msg):
    data = load_data()
    text = msg.text

    # ищем кому админ отвечает
    for uid, entry in data["pending"].items():
        if entry.get("stage") == "wait_admin_comment":
            bot.send_message(uid, f"Ваша реклама отклонена.\nПричина: {text}")
            entry["stage"] = "finished"
            save_data(data)
            return


# -------------------------------------
# После оплаты
# -------------------------------------
def handle_successful(bot, msg):
    user_id = str(msg.from_user.id)
    data = load_data()

    if user_id not in data["pending"]:
        return

    entry = data["pending"][user_id]

    if entry["stage"] != "wait_payment":
        return

    # Переносим в активные рекламы
    ad = {
        "text": entry["text"],
        "photo": entry["photo"],
        "remaining": entry["count"]
    }
    data["ads"].append(ad)

    entry["stage"] = "finished"
    save_data(data)

    bot.send_message(msg.chat.id, "Оплата получена! Ваша реклама активирована.")


# -------------------------------------
# Показ реклам при каждом сообщении
# -------------------------------------
def send_random_ads(bot, chat_id):
    data = load_data()
    ads_list = data["ads"]

    if not ads_list:
        return

    idx = data.get("counter", 0)

    if idx >= len(ads_list):
        idx = 0

    ad = ads_list[idx]

    # выбираем следующую
    data["counter"] = idx + 1
    save_data(data)

    # уменьшаем оставшиеся показы
    ad["remaining"] -= 1
    if ad["remaining"] <= 0:
        ads_list.pop(idx)
        save_data(data)

    bot.send_photo(chat_id, ad["photo"], caption=ad["text"])