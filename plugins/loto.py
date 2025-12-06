# plugins/loto.py
import os
import json
import random
from telebot.types import Message
from plugins.top_plugin import get_name

DATA_FILE = "loto_data.json"
GIFT_AMOUNT = 50  # реальный подарок 50 ⭐

# Загрузка данных
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# Сохранение данных
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Инициализация чата в данных
def ensure_chat(data, chat_id):
    str_id = str(chat_id)
    if str_id not in data:
        data[str_id] = {"bank": 0, "participants": []}
    return data[str_id]

# Добавляем оплату в банк и участников
def add_payment(chat_id, user_id, amount):
    data = load_data()
    chat_data = ensure_chat(data, chat_id)
    chat_data["bank"] += amount
    if user_id not in chat_data["participants"]:
        chat_data["participants"].append(user_id)
    save_data(data)
    return chat_data["bank"], chat_data["participants"]

# Розыгрыш подарка
def send_gift(bot, chat_id, forced=False):
    data = load_data()
    chat_data = ensure_chat(data, chat_id)
    if chat_data["bank"] < 100 and not forced:
        return  # пока не набрали 100⭐

    if not chat_data["participants"]:
        return

    winner_id = random.choice(chat_data["participants"])
    # отправляем подарок
    try:
        bot.send_message(winner_id, f"🎁 Поздравляем! Ты получаешь {GIFT_AMOUNT} ⭐ Stars Gift!")
    except:
        pass

    # списываем из банка 50 ⭐
    chat_data["bank"] -= GIFT_AMOUNT
    if chat_data["bank"] < 0:
        chat_data["bank"] = 0

    # очищаем участников после розыгрыша
    chat_data["participants"] = []
    save_data(data)
    return winner_id

# Обработчик команды /loto
def handle(bot, message: Message):
    data = load_data()
    chat_id = message.chat.id
    chat_data = ensure_chat(data, chat_id)

    text = message.text or ""
    cmd = text.split()[0].lower()

    # Команда тестового подарка
    if cmd.startswith("/gift"):
        winner = send_gift(bot, chat_id, forced=True)
        if winner:
            bot.send_message(chat_id, f"🎁 Тестовый подарок отправлен игроку {get_name(message.from_user)}")
        else:
            bot.send_message(chat_id, "❌ Нет участников для подарка.")
        return

    # Просто показать текущий банк и участников
    if cmd.startswith("/loto"):
        bot.send_message(
            chat_id,
            f"🎰 Лото:\nБанк: {chat_data['bank']}/100 ⭐\nУчастников: {len(chat_data['participants'])}"
        )

# Обработка успешной оплаты
def handle_successful(bot, message: Message):
    if not hasattr(message, "successful_payment") or not message.successful_payment:
        return

    payload = getattr(message.successful_payment, "invoice_payload", "") or \
              getattr(message.successful_payment, "payload", "")

    # payload должен быть вида: boost:<chat_id>:<user_id>:<stat>:<amount>
    parts = payload.split(":")
    if len(parts) < 5:
        return

    _, chat_s, payer_s, stat, amount_s = parts
    try:
        chat_id = int(chat_s)
        payer_id = int(payer_s)
        amount = int(amount_s)
    except:
        return

    # количество ⭐ в зависимости от stat
    stars = 0
    if stat == "sisi":
        stars = amount  # 1⭐ за 1 буст
    elif stat == "mut":
        stars = amount * 2  # 2⭐ за 1 минуту
    else:
        stars = amount

    # Добавляем в банк лото
    bank, participants = add_payment(chat_id, payer_id, stars)

    # ЛС с пользователем
    bot.send_message(
        payer_id,
        f"💫 Получено `{stars}` ⭐. Банк: {bank}/100 ⭐"
    )

    # Если банк >=100, делаем розыгрыш
    if bank >= 100:
        winner_id = send_gift(bot, chat_id)
        if winner_id:
            bot.send_message(
                chat_id,
                f"🎉 Лото завершено! Победитель: {get_name(message.from_user)} ({winner_id}) получает {GIFT_AMOUNT} ⭐ Stars Gift!"
            )