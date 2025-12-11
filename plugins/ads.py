import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

DATA_FILE = "ads_data.json"
ADMIN_ID = 6039700971  # <-- твой Telegram ID

PRICE_PER_SEND = 100  # цена в stars за одну рассылку

# -------------------------------------
# ФАЙЛ ДАННЫХ
# -------------------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "approved": {}}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# -------------------------------------
# Старт покупки рекламы
# -------------------------------------
def handle_buy(bot, message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)

    if chat_id != message.from_user.id:
        bot.reply_to(message, "Эта команда работает только в ЛС бота.")
        return

    data = load_data()
    data["pending"][user_id] = {"step": "await_text"}
    save_data(data)

    bot.send_message(chat_id, "Отправь текст рекламы одним сообщением.\n"
                              "Все кнопки будут удаляться автоматически.")


# -------------------------------------
# Принимаем текст рекламы
# -------------------------------------
def handle(bot, message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id

    if chat_id != message.from_user.id:
        return

    data = load_data()
    user = data["pending"].get(user_id)
    if not user:
        return

    # 1) Ожидаем текст рекламы
    if user["step"] == "await_text":
        user["text"] = message.text
        user["step"] = "confirm_send"
        save_data(data)

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Все верно", callback_data="ads_confirm"),
            InlineKeyboardButton("Отмена", callback_data="ads_cancel")
        )

        bot.send_message(chat_id, "Подтверди текст.", reply_markup=kb)
        return


# -------------------------------------
# Callback пользователя
# -------------------------------------
def callback(bot, call):
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id

    data = load_data()

    # ⛔ Гарантия удаления кнопок у всех callback
    try:
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    except:
        pass

    # ------------------------------
    # Пользователь: подтверждение
    # ------------------------------
    if call.data == "ads_confirm":

        user = data["pending"].get(user_id)
        if not user:
            bot.answer_callback_query(call.id, "Ошибка.")
            return

        # ОТПРАВЛЯЕМ АДМИНУ НА ОДОБРЕНИЕ
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Одобрить", callback_data=f"ads_admin_ok_{user_id}"),
            InlineKeyboardButton("Отклонить", callback_data=f"ads_admin_no_{user_id}")
        )

        bot.send_message(
            ADMIN_ID,
            f"🔔 Новая реклама от @{call.from_user.username} (ID: {user_id}):\n\n"
            f"{user['text']}",
            reply_markup=kb
        )

        bot.answer_callback_query(call.id, "Отправлено админу на проверку.")
        return

    # ------------------------------
    # Пользователь: отмена
    # ------------------------------
    if call.data == "ads_cancel":
        data["pending"].pop(user_id, None)
        save_data(data)
        bot.answer_callback_query(call.id, "Отменено.")
        bot.send_message(chat_id, "Заказ отменён.")
        return

    # ------------------------------
    # Админ: одобрение
    # ------------------------------
    if call.data.startswith("ads_admin_ok_") and call.from_user.id == ADMIN_ID:
        target_id = call.data.split("_")[-1]
        ad = data["pending"].get(target_id)
        if not ad:
            bot.answer_callback_query(call.id, "Реклама уже обработана.")
            return

        # запрос оплаты
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Оплатить рекламу 💳", callback_data=f"ads_pay_{target_id}")
        )

        bot.send_message(
            int(target_id),
            "Админ одобрил рекламу!\n\nНажми кнопку ниже, чтобы оплатить:",
            reply_markup=kb
        )

        bot.answer_callback_query(call.id, "Одобрено!")
        return

    # ------------------------------
    # Админ: отклонение
    # ------------------------------
    if call.data.startswith("ads_admin_no_") and call.from_user.id == ADMIN_ID:
        target_id = call.data.split("_")[-1]
        data["pending"].pop(target_id, None)
        save_data(data)

        bot.send_message(int(target_id), "Админ отклонил рекламу.")
        bot.answer_callback_query(call.id, "Отклонено.")
        return

    # ------------------------------
    # Оплата: запускаем invoice
    # ------------------------------
    if call.data.startswith("ads_pay_"):
        target_id = call.data.split("_")[-1]
        user = data["pending"].get(target_id)
        if not user:
            bot.answer_callback_query(call.id, "Ошибка.")
            return

        bot.send_invoice(
            int(target_id),
            title="Покупка рекламы",
            description="Оплата рекламной рассылки",
            invoice_payload=f"ads:{target_id}",
            provider_token="",  # Stars → оставить пустым
            currency="XTR",
            prices=[LabeledPrice("Реклама", PRICE_PER_SEND * 100)]  # stars * 100
        )

        bot.answer_callback_query(call.id)
        return


# -------------------------------------
# Успешная оплата
# -------------------------------------
def handle_successful(bot, message):
    payload = message.successful_payment.invoice_payload

    if not payload.startswith("ads:"):
        return

    user_id = payload.split(":")[1]
    data = load_data()

    if user_id not in data["pending"]:
        return

    text = data["pending"][user_id]["text"]

    # Переносим в approved
    data["approved"][user_id] = text
    data["pending"].pop(user_id)
    save_data(data)

    bot.send_message(int(user_id), "Оплата прошла! Реклама запущена 🚀")

    # Тут твой реальный код рассылки
    # send_ads_to_users(text)

    bot.send_message(ADMIN_ID, f"Реклама от {user_id} запущена.")
    

# -------------------------------------
# заглушка рекламы
# -------------------------------------
def attach_ad(bot, chat_id):
    pass