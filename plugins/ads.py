import json
import os
from telebot import types

DATA_FILE = "plugins/ads_data.json"

ADMIN_ID = 5791171535   # твой id


# -----------------------------------------
# Работа с файлом
# -----------------------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "approved": [], "active": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# -----------------------------------------
# Цена рекламы (меняем через /priser)
# -----------------------------------------
PRICE_PER_MESSAGE = 3  # цена за 1 показ


# -----------------------------------------
# /priser — только админ меняет цену
# -----------------------------------------
def handle_priser(bot, message):
    global PRICE_PER_MESSAGE
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ У вас нет доступа.")
        return

    try:
        new_price = int(message.text.split()[1])
        PRICE_PER_MESSAGE = new_price
        bot.reply_to(message, f"💰 Цена успешно изменена: {new_price}⭐ за показ.")
    except:
        bot.reply_to(message, "Использование: /priser 5")


# -----------------------------------------
# /ads — запуск процесса
# -----------------------------------------
def start(bot, message):
    user = str(message.from_user.id)
    data = load_data()

    data["pending"][user] = {
        "step": "text",
        "text": None,
        "photo": None,
        "count": 1
    }

    save_data(data)

    bot.send_message(message.chat.id, "✍️ Отправьте текст вашей рекламы.")


# -----------------------------------------
# Основной обработчик etapas
# -----------------------------------------
def handle(bot, message):
    user = str(message.from_user.id)
    data = load_data()

    if user not in data["pending"]:
        return

    obj = data["pending"][user]
    step = obj["step"]

    # ------------------------------------------------
    # Этап 1: текст рекламы
    # ------------------------------------------------
    if step == "text":
        obj["text"] = message.text
        obj["step"] = "review"

        price = obj["count"] * PRICE_PER_MESSAGE

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Продолжить", callback_data=f"ads_continue_{user}"))
        kb.add(types.InlineKeyboardButton("Изменить текст", callback_data=f"ads_change_text_{user}"))
        kb.add(types.InlineKeyboardButton("Изменить количество", callback_data=f"ads_change_count_{user}"))

        bot.send_message(
            message.chat.id,
            f"💬 Текст получен!\n"
            f"Количество показов: {obj['count']}\n"
            f"Итоговая цена: {price}⭐\n\n"
            "Что хотите сделать?",
            reply_markup=kb
        )

        save_data(data)
        return

    # ------------------------------------------------
    # Этап 2: изменение количества
    # ------------------------------------------------
    if step == "count":
        try:
            new_count = int(message.text)
            if new_count < 1:
                raise ValueError
            obj["count"] = new_count
            obj["step"] = "review"
            save_data(data)

            price = obj["count"] * PRICE_PER_MESSAGE

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Продолжить", callback_data=f"ads_continue_{user}"))
            kb.add(types.InlineKeyboardButton("Изменить текст", callback_data=f"ads_change_text_{user}"))
            kb.add(types.InlineKeyboardButton("Изменить количество", callback_data=f"ads_change_count_{user}"))

            bot.send_message(
                message.chat.id,
                f"🔢 Новое количество: {obj['count']}\nЦена: {price}⭐",
                reply_markup=kb
            )
        except:
            bot.send_message(message.chat.id, "Введите число, например: 5")
        return

    # ------------------------------------------------
    # Этап 3: фото
    # ------------------------------------------------
    if step == "photo":
        if not message.photo:
            bot.send_message(message.chat.id, "Пришлите фото.")
            return

        obj["photo"] = message.photo[-1].file_id
        obj["step"] = "confirm"
        save_data(data)

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Подтвердить", callback_data=f"ads_confirm_{user}"))

        bot.send_photo(
            message.chat.id,
            obj["photo"],
            caption="📸 Фото получено. Подтвердите отправку.",
            reply_markup=kb
        )
        return


# -----------------------------------------
# Обработка кнопок
# -----------------------------------------
def callback(bot, call):
    data = load_data()
    user = call.from_user.id
    user_s = str(user)

    if user_s not in data["pending"]:
        return

    obj = data["pending"][user_s]

    # Продолжить → ждём фото
    if call.data == f"ads_continue_{user_s}":
        obj["step"] = "photo"
        save_data(data)
        bot.edit_message_text("📸 Пришлите фото для рекламы.", call.message.chat.id, call.message.message_id)
        return

    # Меняем текст
    if call.data == f"ads_change_text_{user_s}":
        obj["step"] = "text"
        save_data(data)
        bot.edit_message_text("✍️ Введите новый текст:", call.message.chat.id, call.message.message_id)
        return

    # Меняем количество
    if call.data == f"ads_change_count_{user_s}":
        obj["step"] = "count"
        save_data(data)
        bot.edit_message_text("🔢 Введите количество показов:", call.message.chat.id, call.message.message_id)
        return

    # Подтверждение → отправка админу
    if call.data == f"ads_confirm_{user_s}":
        obj["step"] = "wait_admin"
        save_data(data)

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Одобрить", callback_data=f"ads_admin_ok_{user_s}"))
        kb.add(types.InlineKeyboardButton("Отклонить", callback_data=f"ads_admin_no_{user_s}"))

        bot.send_message(ADMIN_ID, f"🔥 Новая реклама от {user_s}:\n\n{obj['text']}")
        bot.send_photo(ADMIN_ID, obj["photo"], reply_markup=kb)

        bot.edit_message_caption(
            caption="⏳ Ожидайте одобрения администратора…",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        return

    # -----------------------------------------
    # Админ: одобрить
    # -----------------------------------------
    if call.data.startswith("ads_admin_ok_"):
        target = call.data.split("_")[-1]
        t = data["pending"].get(target)
        if not t:
            return

        # Цена
        price = t["count"] * PRICE_PER_MESSAGE

        # Отправляем пользователю оплату
        invoice = types.LabeledPrice(label="Реклама", amount=price * 100)

        bot.send_invoice(
            chat_id=int(target),
            title="Реклама",
            description="Оплатите чтобы активировать вашу рекламу.",
            invoice_payload=f"ads_pay_{target}",
            provider_token="",  # Stars НЕ требует токена
            currency="XTR",
            prices=[invoice]
        )

        bot.edit_message_caption(
            caption="✔️ Одобрено и отправлено пользователю.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

        save_data(data)
        return

    # -----------------------------------------
    # Админ: отклонить
    # -----------------------------------------
    if call.data.startswith("ads_admin_no_"):
        target = call.data.split("_")[-1]

        bot.send_message(ADMIN_ID, "Введите причину отказа:")
        data["pending"][target]["step"] = "admin_reason"
        save_data(data)
        return


# -----------------------------------------
# Обработка успешной оплаты рекламы
# -----------------------------------------
def handle_successful(bot, message):
    payload = message.successful_payment.invoice_payload
    if not payload.startswith("ads_pay_"):
        return

    user = payload.split("_")[-1]
    data = load_data()

    obj = data["pending"].get(user)
    if not obj:
        return

    # Добавляем в активные рекламы
    data["active"].append(obj)
    del data["pending"][user]
    save_data(data)

    bot.send_message(int(user), "🎉 Ваша реклама активирована!")
    return


# -----------------------------------------
# Отдать одну рекламу (циклично)
# -----------------------------------------
def get_next_ad():
    data = load_data()
    if not data["active"]:
        return None

    # циклический перебор
    ad = data["active"].pop(0)
    data["active"].append(ad)
    save_data(data)
    return ad