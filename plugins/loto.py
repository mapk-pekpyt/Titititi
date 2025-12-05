# plugins/loto.py
import os
import json
import random

FILE = "data/loto.json"
os.makedirs("data", exist_ok=True)

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
        data[chat_id] = {"total": 0, "users": {}, "lotoprice": 100}
    else:
        if "total" not in data[chat_id]:
            data[chat_id]["total"] = 0
        if "users" not in data[chat_id]:
            data[chat_id]["users"] = {}
        if "lotoprice" not in data[chat_id]:
            data[chat_id]["lotoprice"] = 100

# ------------------ ОБРАБОТКА ОПЛАТ ------------------

def handle_successful(bot, message):
    """
    Добавляет любые успешные оплаты в банк лото.
    Всегда вызывается из main.py.
    """
    data = load()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    ensure_chat(data, chat_id)
    
    # Берём звезды из успешной оплаты
    try:
        stars = getattr(message.successful_payment, "total_amount", 0)
    except:
        stars = 0

    # Добавляем пользователю и в общий банк чата
    data[chat_id]["total"] += stars
    data[chat_id]["users"].setdefault(user_id, 0)
    data[chat_id]["users"][user_id] += stars

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

    # ------------------ /lotoprice ------------------
    if cmd == "/lotoprice":
        parts = text.split()
        if len(parts) < 2:
            bot.reply_to(message, f"💰 Текущий лото-прайс: {data[chat_id]['lotoprice']} ⭐")
            return

        # Только админы могут менять
        try:
            admins = bot.get_chat_administrators(message.chat.id)
            admin_ids = [a.user.id for a in admins]
        except:
            admin_ids = []

        if message.from_user.id not in admin_ids:
            bot.reply_to(message, "⛔ Только админы могут менять цену лото.")
            return

        try:
            new_price = int(parts[1])
            data[chat_id]["lotoprice"] = new_price
            save(data)
            bot.reply_to(message, f"✅ Лото-прайс обновлён: {new_price} ⭐")
        except:
            bot.reply_to(message, "❗ Используй: /lotoprice 150")
        return

    # ------------------ /loto ------------------
    if cmd == "/loto":
        total = data[chat_id]["total"]
        price = data[chat_id]["lotoprice"]

        if total < price:
            bot.reply_to(message, f"🕐 Ещё не набрано {price} ⭐, собрано {total} ⭐")
            return

        # Выбираем победителя
        users = list(data[chat_id]["users"].items())
        if not users:
            bot.reply_to(message, "⚠️ Нет донативших пользователей.")
            return

        winner_id, _ = random.choice(users)
        winner_name = get_user_name(bot, chat_id, int(winner_id))

        reward = total // 2
        bot.send_message(message.chat.id, f"🎉 Поздравляем {winner_name}! Ты выиграл {reward} ⭐!")

        # Сбрасываем накопления
        data[chat_id]["total"] = 0
        data[chat_id]["users"] = {}
        save(data)

# ------------------ ВСПОМОГАТЕЛЬНЫЕ ------------------

def get_user_name(bot, chat_id, user_id):
    try:
        return bot.get_chat_member(chat_id, user_id).user.first_name
    except:
        return "Пользователь"