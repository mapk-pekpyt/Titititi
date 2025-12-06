import json
import os
from telebot.types import LabeledPrice

DATA_FILE = "data/loto.json"

# -------------------------------------------------------
#  ЗАГРУЗКА / СОХРАНЕНИЕ
# -------------------------------------------------------

def load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# -------------------------------------------------------
#  ИНИЦИАЛИЗАЦИЯ ДЛЯ ОТДЕЛЬНОГО ЧАТА
# -------------------------------------------------------

def ensure_chat(chat_id):
    data = load()
    if str(chat_id) not in data:
        data[str(chat_id)] = {
            "bank": 0,
            "users": {}  # user_id: stars
        }
        save(data)
    return data


# -------------------------------------------------------
#  НАЧИСЛЕНИЕ СРЕДСТВ
# -------------------------------------------------------

def add_stars(chat_id, user_id, amount):
    data = ensure_chat(chat_id)
    chat_id = str(chat_id)
    user_id = str(user_id)

    if user_id not in data[chat_id]["users"]:
        data[chat_id]["users"][user_id] = 0

    data[chat_id]["users"][user_id] += amount
    data[chat_id]["bank"] += amount

    save(data)


# -------------------------------------------------------
#  ВЫГРЫШ ПРИ 100 ЗВЁЗДАХ
# -------------------------------------------------------

def try_payout(bot, chat_id):
    data = load()
    chat = str(chat_id)

    if chat not in data:
        return

    if data[chat]["bank"] < 100:
        return

    users = data[chat]["users"]
    if not users:
        return

    # выбираем случайного донатера
    import random
    winner = random.choice(list(users.keys()))
    winner_id = int(winner)

    # выдаём подарок
    bot.send_message(chat_id, f"🎁 *Розыгрыш!* Победитель — <a href='tg://user?id={winner_id}'>этот красавчик</a>!\nБот дарит ему 50 ⭐!", parse_mode="HTML")

    # отправка подарка
    try:
        bot.send_invoice(
            winner_id,
            title="Подарок 50 Stars",
            description="Ваш выигрыш!",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Подарок", 50)],
            payload="loto_gift"
        )
    except:
        pass

    # обнуляем банк
    data[chat]["bank"] = 0
    data[chat]["users"] = {}
    save(data)


# -------------------------------------------------------
#  РУЧНОЙ ПОДАРОК
# -------------------------------------------------------

def handle_gift_command(bot, message):
    chat_id = message.chat.id

    try:
        bot.send_invoice(
            chat_id,
            title="Тестовый подарок 50⭐",
            description="Ручная выдача",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Подарок", 50)],
            payload="manual_gift"
        )
    except Exception as e:
        bot.reply_to(message, f"Ошибка отправки подарка: {e}")


# -------------------------------------------------------
#  ОБРАБОТКА УСПЕШНОЙ ОПЛАТЫ
# -------------------------------------------------------

def handle_successful(bot, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Stars → total_amount всегда = звёздам
    stars = message.successful_payment.total_amount

    add_stars(chat_id, user_id, stars)

    bot.send_message(
        user_id,
        f"💫 Получено `{stars}` ⭐\nБанк: {load()[str(chat_id)]['bank']}/100 ⭐",
        parse_mode="Markdown"
    )

    try_payout(bot, chat_id)


# -------------------------------------------------------
#  ЛОВИМ КОМАНДЫ boost/mut
# -------------------------------------------------------

def handle_message_based_payments(bot, message):
    text = message.text.lower()
    chat_id = message.chat.id
    user_id = message.from_user.id

    # /boosts (без числа)
    if text.startswith("/boosts") and "@" not in text:
        parts = text.split()
        if len(parts) == 1:
            amount = 1
        else:
            try:
                amount = int(parts[1])
            except:
                amount = 1

        add_stars(chat_id, user_id, amount)
        try_payout(bot, chat_id)
        return True

    # мут → 2 * минуты
    if text.startswith("мут ") or text.startswith("mut "):
        parts = text.split()
        try:
            minutes = int(parts[1])
        except:
            minutes = 1

        stars = minutes * 2
        add_stars(chat_id, user_id, stars)
        try_payout(bot, chat_id)
        return True

    return False


# -------------------------------------------------------
#  ГЛАВНЫЙ handle ПЛАГИНА
# -------------------------------------------------------

def handle(bot, message):
    text = message.text.lower()

    # /loto
    if text == "/loto":
        data = ensure_chat(message.chat.id)
        bank = data[str(message.chat.id)]["bank"]
        bot.reply_to(message, f"🎰 Банк: {bank}/100 ⭐")
        return

    # /gift
    if text == "/gift":
        handle_gift_command(bot, message)
        return

    # бусты и муты
    handle_message_based_payments(bot, message)