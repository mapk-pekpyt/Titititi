# plugins/loto.py
import os
import json
import random

FILE = "data/loto.json"
os.makedirs("data", exist_ok=True)

GIFT_AMOUNT = 50  # 50 Stars Gift
MIN_FOR_GIFT = 100  # минимальный банк для автоматического подарка

# ------------------ ФУНКЦИИ ------------------

def load():
    if not os.path.exists(FILE):
        return {}
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_chat(data, chat_id):
    if chat_id not in data:
        data[chat_id] = {"total": 0, "users": {}}
    else:
        if "total" not in data[chat_id]:
            data[chat_id]["total"] = 0
        if "users" not in data[chat_id]:
            data[chat_id]["users"] = {}

# ------------------ ОБРАБОТКА УСПЕШНОЙ ОПЛАТЫ ------------------

def handle_successful(bot, message):
    """
    Любая успешная оплата добавляется в банк лото.
    Если банк >= MIN_FOR_GIFT, автоматически выбираем победителя.
    """
    data = load()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    ensure_chat(data, chat_id)
    
    # Берём сумму из успешной оплаты (в smallest units, обычно cents)
    try:
        stars = getattr(message.successful_payment, "total_amount", 0)
    except:
        stars = 0

    if stars <= 0:
        return  # не учитываем 0

    # Добавляем в банк и пользователю
    data[chat_id]["total"] += stars
    data[chat_id]["users"].setdefault(user_id, 0)
    data[chat_id]["users"][user_id] += stars

    save(data)

    # Проверяем, достигнут ли минимум для подарка
    if data[chat_id]["total"] >= MIN_FOR_GIFT:
        send_gift(bot, chat_id, data)

# ------------------ ОТПРАВКА GIFT ------------------

def send_gift(bot, chat_id, data, forced=False):
    """
    Выбираем случайного донатившего и отправляем подарок.
    Если forced=True, игнорируем минимальную сумму.
    """
    users = list(data[chat_id]["users"].items())
    if not users:
        return

    winner_id, _ = random.choice(users)
    winner_name = get_user_name(bot, int(chat_id), int(winner_id))

    # Отправка сообщения о подарке (50 Stars Gift)
    bot.send_message(chat_id, f"🎁 Поздравляем {winner_name}! Ты получаешь {GIFT_AMOUNT} Stars Gift!")

    # Сбрасываем банк и список донативших
    data[chat_id]["total"] = 0
    data[chat_id]["users"] = {}
    save(data)

# ------------------ КОМАНДЫ ------------------

def handle(bot, message):
    text = (message.text or "").strip()
    if not text:
        return

    chat_id = str(message.chat.id)
    data = load()
    ensure_chat(data, chat_id)

    cmd_raw = text.split()[0].lower()
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw

    # ------------------ /loto ------------------
    if cmd == "/loto":
        total = data[chat_id]["total"]
        bot.reply_to(message, f"💰 Банк лото в этом чате: {total} ⭐. Минимум для розыгрыша: {MIN_FOR_GIFT} ⭐")
        if total >= MIN_FOR_GIFT:
            send_gift(bot, chat_id, data)
        return

    # ------------------ /gift ------------------
    if cmd == "/gift":
        # Только админ чата может вручную отправить подарок
        try:
            admins = bot.get_chat_administrators(message.chat.id)
            admin_ids = [a.user.id for a in admins]
        except:
            admin_ids = []

        if message.from_user.id not in admin_ids:
            bot.reply_to(message, "⛔ Только админы могут отправлять подарки вручную.")
            return

        send_gift(bot, chat_id, data, forced=True)
        return

# ------------------ ВСПОМОГАТЕЛЬНЫЕ ------------------

def get_user_name(bot, chat_id, user_id):
    try:
        return bot.get_chat_member(chat_id, user_id).user.first_name
    except:
        return "Пользователь"