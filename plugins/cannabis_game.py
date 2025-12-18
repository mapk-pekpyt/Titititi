import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name
from plugins import top_plugin

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

# ================== TABLE ==================
cursor.execute("""
CREATE TABLE IF NOT EXISTS cannabis (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    coins INTEGER DEFAULT 1000,
    bushes INTEGER DEFAULT 0,
    weed INTEGER DEFAULT 0,
    cakes INTEGER DEFAULT 0,
    joints INTEGER DEFAULT 0,
    hunger INTEGER DEFAULT 0,
    high INTEGER DEFAULT 0,
    last_collect TEXT,
    last_eat TEXT,
    last_smoke TEXT
)
""")
conn.commit()

# ================== HELPERS ==================
def ensure_user(user):
    cursor.execute(
        "INSERT OR IGNORE INTO cannabis(user_id,name) VALUES (?,?)",
        (str(user.id), get_name(user))
    )
    cursor.execute(
        "UPDATE cannabis SET name=? WHERE user_id=?",
        (get_name(user), str(user.id))
    )
    conn.commit()

def get_user(user):
    ensure_user(user)
    cursor.execute(
        "SELECT * FROM cannabis WHERE user_id=?",
        (str(user.id),)
    )
    return cursor.fetchone()

def update_user(user_id, field, delta):
    cursor.execute(f"UPDATE cannabis SET {field}={field}+? WHERE user_id=?", (delta, str(user_id)))
    conn.commit()

def set_user_time(user_id, field):
    cursor.execute(f"UPDATE cannabis SET {field}=? WHERE user_id=?", (datetime.now().isoformat(), str(user_id)))
    conn.commit()

def cooldown_passed(last_time, hours=1):
    if not last_time:
        return True
    return datetime.now() - datetime.fromisoformat(last_time) >= timedelta(hours=hours)

# ================== GAME ==================
def handle(bot, message):
    user = message.from_user
    text = (message.text or "").lower().strip()
    name = get_name(user)

    u = get_user(user)

    # -------- БАЛАНС --------
    if text == "баланс":
        return bot.reply_to(
            message,
            f"🌿 {name}\n\n"
            f"💰 Коины: {u[2]}\n"
            f"🌱 Кусты: {u[3]}\n"
            f"🌿 Конопля: {u[4]}\n"
            f"🥮 Кексы: {u[5]}\n"
            f"🚬 Косяки: {u[6]}\n"
            f"❤️ Сытость: {u[7]}\n"
            f"😵 Кайф: {u[8]}"
        )

    # -------- КУПИТЬ КУСТЫ --------
    if text.startswith("купить"):
        try:
            n = int(text.split()[1])
        except:
            n = 1
        cost = n * 10

        if u[2] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")

        update_user(user.id, "coins", -cost)
        update_user(user.id, "bushes", n)

        # Обновляем топ только кусты
        top_plugin.update_stat("global", user, "bushes", n)

        return bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

    # -------- СБОР (РАЗ В ЧАС) --------
    if text == "собрать":
        if not cooldown_passed(u[9]):
            mins = int((timedelta(hours=1) - (datetime.now() - datetime.fromisoformat(u[9]))).seconds / 60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")

        if u[3] <= 0:
            return bot.reply_to(message, "❌ У тебя нет кустов")

        gain = random.randint(1, u[3])
        update_user(user.id, "weed", gain)
        set_user_time(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ ТРАВУ --------
    if text.startswith("продать ") and not text.startswith("продать кексы"):
        parts = text.split()
        n = int(parts[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        earned = n // 10
        update_user(user.id, "weed", -n)
        update_user(user.id, "coins", earned)
        return bot.reply_to(message, f"💰 Продано {n} → +{earned} коинов")

    # -------- ПРОДАТЬ КЕКСЫ --------
    if text.startswith("продать кексы"):
        parts = text.split()
        n = int(parts[2])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        earned = n // 5
        update_user(user.id, "cakes", -n)
        update_user(user.id, "coins", earned)
        return bot.reply_to(message, f"💰 Продал {n} кексов → +{earned} коинов")

    # -------- КРАФТ КОСЯКОВ --------
    if text.startswith("крафт"):
        try:
            n = int(text.split()[1])
        except:
            n = 1
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        update_user(user.id, "weed", -n)
        update_user(user.id, "joints", n)
        return bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

    # -------- ЕСТЬ КЕКС --------
    if text.startswith("съесть"):
        try:
            n = int(text.split()[1])
        except:
            n = 1
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        if not cooldown_passed(u[10]):
            mins = int((timedelta(hours=1) - (datetime.now() - datetime.fromisoformat(u[10]))).seconds / 60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        update_user(user.id, "cakes", -n)
        update_user(user.id, "hunger", n)
        set_user_time(user.id, "last_eat")
        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # -------- ДУНУТЬ --------
    if text == "подымить":
        if u[6] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        if not cooldown_passed(u[11]):
            mins = int((timedelta(hours=1) - (datetime.now() - datetime.fromisoformat(u[11]))).seconds / 60)
            return bot.reply_to(message, f"⏳ Подожди {mins} мин")
        effect = random.randint(1, 5)
        update_user(user.id, "joints", -1)
        update_user(user.id, "high", effect)
        set_user_time(user.id, "last_smoke")
        # Обновляем топ по кайфу если нужно
        return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")