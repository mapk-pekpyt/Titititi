# plugins/loto.py

import os
import json
import random

FILE = "data/loto.json"
os.makedirs("data", exist_ok=True)


def load():
    if not os.path.exists(FILE):
        return {}
    try:
        with open(FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return {}


def save(data):
    with open(FILE, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -----------------------------------
#  /lotoprice X
# -----------------------------------
def set_price(bot, message):
    chat = str(message.chat.id)
    data = load()

    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Укажи цену: /lotoprice 100")

    try:
        price = int(parts[1])
        if price <= 0:
            raise ValueError
    except:
        return bot.reply_to(message, "Цена должна быть положительным числом!")

    if chat not in data:
        data[chat] = {
            "price": price,
            "stars": 0,
            "users": []
        }
    else:
        data[chat]["price"] = price

    save(data)
    bot.reply_to(message, f"💰 Лотопрайс установлен: {price}⭐")


# -----------------------------------
#  /loto — проверка и запуск
# -----------------------------------
def handle_loto(bot, message):
    chat = str(message.chat.id)
    data = load()

    if chat not in data:
        return bot.reply_to(message, "В этом чате ещё нет лотопрайса. Установи: /lotoprice 100")

    price = data[chat]["price"]
    stars = data[chat]["stars"]

    if stars < price:
        return bot.reply_to(
            message,
            f"⭐ В банке {stars}⭐ / {price}⭐\n"
            f"Нужно ещё {price - stars}⭐ для розыгрыша!"
        )

    # Готов к розыгрышу
    donors = data[chat]["users"]
    unique_donors = list(set(donors))

    if not unique_donors:
        return bot.reply_to(message, "Никто не донатил — разыгрывать нечего.")

    # Выбираем победителя
    winner_id = random.choice(unique_donors)

    # Приз — половина банка
    prize = price // 2

    bot.reply_to(
        message,
        f"🎉 *ЛОТО* 🎉\n\n"
        f"В банке было {price}⭐\n"
        f"Победитель: [пользователь](tg://user?id={winner_id}) 🎉\n"
        f"Выигрыш: {prize}⭐\n\n"
        f"Новый сбор начат!"
        , parse_mode="Markdown"
    )

    # ❗ БОТ ОТПРАВЛЯЕТ ПРИЗ ПОБЕДИТЕЛЮ Stars
    try:
        bot.send_invoice(
            winner_id,
            title="Выигрыш в лото",
            description="Поздравляем! Вы выиграли звёзды!",
            invoice_payload="loto_prize",
            provider_token="",
            currency="XTR",   # Stars
            prices=[{"label": "Выигрыш", "amount": prize}],
            need_name=False,
            need_email=False
        )
    except Exception as e:
        print("Ошибка отправки выигрыша:", e)

    # Сбрасываем накопления
    data[chat]["stars"] = 0
    data[chat]["users"] = []
    save(data)


# -----------------------------------
# ОБРАБОТКА УСПЕШНОЙ ОПЛАТЫ
# -----------------------------------
def handle_successful(bot, message):
    chat = message.chat.id
    if chat is None:
        return

    chat = str(chat)

    data = load()
    if chat not in data:
        return

    stars = message.successful_payment.total_amount
    user_id = message.from_user.id

    # Добавляем в банк
    data[chat]["stars"] += stars

    # Добавляем игрока
    data[chat]["users"].append(user_id)

    save(data)


# -----------------------------------
# ОБРАБОТЧИК КОМАНД
# -----------------------------------
def handle(bot, message):
    text = message.text.lower()

    if text.startswith("/lotoprice"):
        return set_price(bot, message)

    if text.startswith("/loto"):
        return handle_loto(bot, message)