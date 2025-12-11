import os
import json
import telebot
from telebot import types

DATA_FILE = "plugins/ads_data.json"

ADMIN_ID = 123456789  # <<< ВСТАВЬ СВОЙ ID
PROVIDER_TOKEN = ""   # НЕ НУЖНО ДЛЯ ЗВЕЗД (Telegram Stars)

DEFAULT_PRICE = 3  # звезды за 1 показ


# -----------------------------
# Работа с файлом
# -----------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"price": DEFAULT_PRICE, "ads": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {"price": DEFAULT_PRICE, "ads": {}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# -----------------------------
# Команда администратора /priser X
# -----------------------------
def handle_price(bot, message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Нет доступа")

    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, "Используй: /priser число")

    try:
        price = int(parts[1])
    except:
        return bot.reply_to(message, "Цена должна быть числом")

    data = load_data()
    data["price"] = price
    save_data(data)

    bot.reply_to(message, f"💲 Новая цена установлена: {price}⭐ за 1 показ")


# -----------------------------
# Команда /buy_ads
# -----------------------------
def handle_buy(bot, message):
    kb = types.InlineKeyboardMarkup()
    for n in [5, 10, 20, 50, 100]:
        kb.add(types.InlineKeyboardButton(text=f"{n} показов", callback_data=f"ads_amount_{n}"))

    bot.send_message(message.chat.id, "Выбери количество показов:", reply_markup=kb)


# -----------------------------
# Получение текста рекламы
# -----------------------------
def handle_text(bot, message):
    data = load_data()
    uid = str(message.from_user.id)

    if uid not in data["ads"]:
        return

    user = data["ads"][uid]

    # ждем текст
    if user["status"] == "waiting_text":
        user["text"] = message.text
        user["status"] = "waiting_photo"
        save_data(data)
        bot.send_message(message.chat.id, "Отправь фото или /skip")
        return

    # ждем фото
    if user["status"] == "waiting_photo":
        if message.text == "/skip":
            user["photo"] = None
        elif message.photo:
            user["photo"] = message.photo[-1].file_id
        else:
            return bot.send_message(message.chat.id, "Отправь фото или /skip")

        user["status"] = "pending_approval"
        save_data(data)
        send_to_admin(bot, message.from_user.id)


# -----------------------------
# Шаг 3 — Отправляем админу
# -----------------------------
def send_to_admin(bot, user_id):
    data = load_data()
    info = data["ads"][str(user_id)]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Одобрить ✔", callback_data=f"ads_ok_{user_id}"))
    kb.add(types.InlineKeyboardButton("Отклонить ✖", callback_data=f"ads_no_{user_id}"))

    bot.send_message(
        ADMIN_ID,
        f"Реклама от {user_id}\n"
        f"Показы: {info['amount']}\n\n"
        f"Текст:\n{info['text']}",
        reply_markup=kb
    )

    if info["photo"]:
        bot.send_photo(ADMIN_ID, info["photo"])


# -----------------------------
# Обработка кнопок админа
# -----------------------------
def handle_admin_callbacks(bot, call):
    data = load_data()

    # Одобрить
    if call.data.startswith("ads_ok_"):
        user_id = call.data.replace("ads_ok_", "")
        info = data["ads"][user_id]

        # считаем стоимость
        total_stars = data["price"] * info["amount"]

        # бесплатный режим
        if total_stars == 0:
            info["status"] = "active"
            save_data(data)
            bot.send_message(user_id, "Ваша реклама активирована бесплатно ✔")
            bot.send_message(call.message.chat.id, "Активирована бесплатно.")
            return

        # Платеж
        price_label = f"{info['amount']} показов рекламы"
        payload = f"ads_payment_{user_id}"

        kb = types.ReplyKeyboardRemove()

        bot.send_invoice(
            chat_id=int(user_id),
            title="Покупка рекламы",
            description=price_label,
            provider_token="",
            currency="XTR",  # звезды
            prices=[types.LabeledPrice(label=price_label, amount=total_stars)],
            start_parameter="ads",
            invoice_payload=payload
        )

        info["status"] = "waiting_payment"
        save_data(data)

        bot.send_message(call.message.chat.id, "Отправлен инвойс на оплату.")

    # Отклонить
    elif call.data.startswith("ads_no_"):
        user_id = call.data.replace("ads_no_", "")
        bot.send_message(int(user_id), "❌ Ваша реклама отклонена.")
        bot.send_message(call.message.chat.id, "Отклонено.")


# -----------------------------
# После успешной оплаты
# -----------------------------
def handle_successful(bot, message):
    if not message.successful_payment:
        return

    payload = message.successful_payment.invoice_payload

    if not payload.startswith("ads_payment_"):
        return

    user_id = payload.replace("ads_payment_", "")

    data = load_data()
    data["ads"][user_id]["status"] = "active"
    save_data(data)

    bot.send_message(message.chat.id, "✔ Ваша реклама активирована!")


# -----------------------------
# Показы рекламы при действиях
# -----------------------------
def send_random_ads(bot, chat_id):
    data = load_data()
    ads = data["ads"]

    active = [(uid, x) for uid, x in ads.items() if x["status"] == "active" and x["amount"] > 0]
    if not active:
        return

    uid, info = random.choice(active)

    # уменьшаем остаток
    info["amount"] -= 1
    if info["amount"] == 0:
        info["status"] = "finished"

    save_data(data)

    # показываем
    if info["photo"]:
        bot.send_photo(chat_id, info["photo"], caption=info["text"])
    else:
        bot.send_message(chat_id, info["text"])


# -----------------------------
# ГЛАВНЫЙ обработчик callback
# -----------------------------
def handle_callback(bot, call):
    if call.data.startswith("ads_amount_"):
        amount = int(call.data.replace("ads_amount_", ""))

        data = load_data()
        data["ads"][str(call.from_user.id)] = {
            "amount": amount,
            "text": None,
            "photo": None,
            "status": "waiting_text"
        }
        save_data(data)

        bot.send_message(call.message.chat.id, f"Отправь текст рекламы ({amount} показов).")
        return

    handle_admin_callbacks(bot, call)