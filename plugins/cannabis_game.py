import os
import json
import random
from datetime import datetime, timedelta
from plugins.common import get_name, german_date

os.makedirs("data", exist_ok=True)

# -------------------- ПАМЯТЬ --------------------
def _file(chat_id):
    return f"data/игра_{chat_id}.json"

def load(chat_id):
    f = _file(chat_id)
    if not os.path.exists(f):
        return {}
    try:
        with open(f, "r", encoding="utf8") as file:
            return json.load(file)
    except:
        return {}

def save(chat_id, data):
    f = _file(chat_id)
    with open(f, "w", encoding="utf8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def ensure_user(chat_id, user):
    data = load(chat_id)
    uid = str(user.id)
    if uid not in data:
        data[uid] = {
            "коины": 10,
            "кусты": 0,
            "конопля": 0,
            "кексы": 0,
            "косяки": 0,
            "сытость": 0,
            "последний_сбор": None,
            "последний_кайф": None
        }
    save(chat_id, data)
    return data

# -------------------- ЛОГИКА --------------------
def handle(bot, message):
    chat_id = str(message.chat.id)
    user = message.from_user
    name = get_name(user)
    text = (message.text or "").lower().strip()
    data = ensure_user(chat_id, user)
    uid = str(user.id)
    user_data = data[uid]

    now = datetime.now()

    # ---------- БАЛАНС ----------
    if text == "баланс":
        msg = (
            f"🟢 {name}, твой баланс:\n\n"
            f"💰 Коины: {user_data['коины']}\n"
            f"🌱 Кусты: {user_data['кусты']}\n"
            f"🌿 Конопля: {user_data['конопля']}\n"
            f"🥮 Кексы: {user_data['кексы']}\n"
            f"🚬 Косяки: {user_data['косяки']}\n"
            f"❤️ Сытость: {user_data['сытость']}"
        )
        return bot.reply_to(message, msg)

    # ---------- КУСТЫ ----------
    if text.startswith("купить"):
        try:
            n = max(int(text.split()[1]), 1)
        except:
            n = 1
        cost = 10 * n
        if user_data["коины"] < cost:
            return bot.reply_to(message, f"❌ {name}, у тебя нет {cost} коинов!")
        user_data["коины"] -= cost
        user_data["кусты"] += n
        save(chat_id, data)
        return bot.reply_to(message, f"🌱 {name}, ты купил {n} кустов за {cost} коинов!")

    # ---------- СОБРАТЬ КОНОПЛЮ ----------
    if text == "собрать":
        last = user_data.get("последний_сбор")
        if last:
            last_dt = datetime.fromisoformat(last)
            if now - last_dt < timedelta(hours=1):
                remain = timedelta(hours=1) - (now - last_dt)
                minutes = remain.seconds // 60
                return bot.reply_to(message, f"⏳ {name}, еще {minutes} мин до следующего сбора!")
        gain = random.randint(0, user_data["кусты"])
        user_data["конопля"] += gain
        user_data["последний_сбор"] = now.isoformat()
        save(chat_id, data)
        return bot.reply_to(message, f"🌿 {name}, ты собрал {gain} конопли с {user_data['кусты']} кустов!")

    # ---------- ПРОДАТЬ КОНОПЛЮ ----------
    if text.startswith("продать"):
        try:
            n = int(text.split()[1])
        except:
            n = 0
        if user_data["конопля"] < n:
            return bot.reply_to(message, f"❌ {name}, у тебя нет {n} конопли!")
        user_data["конопля"] -= n
        earned = n // 10
        user_data["коины"] += earned
        save(chat_id, data)
        return bot.reply_to(message, f"💰 {name}, ты продал {n} конопли и получил {earned} коинов!")

    # ---------- ИСПЕЧЬ КЕКСЫ ----------
    if text.startswith("испечь"):
        try:
            n = int(text.split()[1])
        except:
            n = 0
        if user_data["конопля"] < n:
            return bot.reply_to(message, f"❌ {name}, у тебя нет {n} конопли!")
        burned = 0
        baked = 0
        for _ in range(n):
            if random.random() < 0.3:  # 30% шанс сгореть
                burned += 1
            else:
                baked += 1
        user_data["конопля"] -= n
        user_data["кексы"] += baked
        save(chat_id, data)
        return bot.reply_to(
            message,
            f"🥮 {name}, ты испёк {baked} кексов 🔥{burned} сгорело"
        )

    # ---------- СЪЕСТЬ КЕКС ----------
    if text.startswith("съесть"):
        try:
            n = int(text.split()[1])
        except:
            n = 0
        if user_data["кексы"] < n:
            return bot.reply_to(message, f"❌ {name}, у тебя нет {n} кексов!")
        user_data["кексы"] -= n
        user_data["сытость"] += n
        save(chat_id, data)
        return bot.reply_to(message, f"❤️ {name}, ты съел {n} кексов и +{n} сытости!")

    # ---------- ПРОДАТЬ КЕКСЫ ----------
    if text.startswith("продать кексы"):
        try:
            n = int(text.split()[2])
        except:
            n = 0
        if user_data["кексы"] < n:
            return bot.reply_to(message, f"❌ {name}, у тебя нет {n} кексов!")
        earned = n // 5
        user_data["кексы"] -= n
        user_data["коины"] += earned
        save(chat_id, data)
        return bot.reply_to(message, f"💰 {name}, ты продал {n} кексов и получил {earned} коинов!")

    # ---------- КРАФТ КОСЯКОВ ----------
    if text.startswith("крафт"):
        try:
            n = int(text.split()[1])
        except:
            n = 0
        if user_data["конопля"] < n:
            return bot.reply_to(message, f"❌ {name}, у тебя нет {n} конопли!")
        user_data["конопля"] -= n
        user_data["косяки"] += n
        save(chat_id, data)
        return bot.reply_to(message, f"🚬 {name}, ты скрутил {n} косяков!")

    # ---------- ПОДЫМИТЬ ----------
    if text == "подымить":
        last = user_data.get("последний_кайф")
        if last:
            last_dt = datetime.fromisoformat(last)
            if now - last_dt < timedelta(hours=1):
                remain = timedelta(hours=1) - (now - last_dt)
                minutes = remain.seconds // 60
                return bot.reply_to(message, f"⏳ {name}, еще {minutes} мин до следующего кайфа!")
        effect = random.choices(
            population=[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5],
            weights=[1,1,1,1,1,5,10,10,10,5,3],
            k=1
        )[0]
        user_data["последний_кайф"] = now.isoformat()
        save(chat_id, data)
        return bot.reply_to(message, f"😵‍💫 {name}, твой кайф изменился на {effect}!")