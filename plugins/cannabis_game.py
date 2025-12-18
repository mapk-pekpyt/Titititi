import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name

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
def ensure(user):
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
    ensure(user)
    cursor.execute("SELECT * FROM cannabis WHERE user_id=?", (str(user.id),))
    return cursor.fetchone()

def update_field(user_id, field, delta):
    cursor.execute(f"""
        UPDATE cannabis 
        SET {field} = MAX({field} + ?, 0) 
        WHERE user_id=?
    """, (delta, str(user_id)))
    conn.commit()

def set_time(user_id, field):
    cursor.execute(f"""
        UPDATE cannabis 
        SET {field}=? 
        WHERE user_id=?
    """, (datetime.now().isoformat(), str(user_id)))
    conn.commit()

def cooldown_passed(last_time, hours=1):
    if not last_time:
        return True
    return datetime.now() - datetime.fromisoformat(last_time) >= timedelta(hours=hours)

# ================== GAME ==================
def handle(bot, message):
    user = message.from_user
    text = (message.text or "").lower().strip()
    u = get_user(user)
    now = datetime.now()

    # -------- БАЛАНС --------
    if text == "баланс":
        return bot.reply_to(
            message,
            f"🌿 {u[2]}\n\n"
            f"💰 Коины: {u[3]}\n"
            f"🌱 Кусты: {u[3]}\n"
            f"🌿 Конопля: {u[4]}\n"
            f"🥮 Кексы: {u[5]}\n"
            f"🚬 Косяки: {u[6]}\n"
            f"❤️ Сытость: {u[7]}\n"
            f"😵‍💫 Кайф: {u[8]}"
        )

    # -------- КУПИТЬ КУСТЫ --------
    if text.startswith("купить"):
        parts = text.split()
        n = int(parts[1]) if len(parts) > 1 else 1
        cost = n * 10
        if u[2] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")
        update_field(user.id, "coins", -cost)
        update_field(user.id, "bushes", n)
        return bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

    # -------- СОБРАТЬ (раз в час) --------
    if text == "собрать":
        if not cooldown_passed(u[9]):
            mins = int((timedelta(hours=1) - (now - datetime.fromisoformat(u[9]))).seconds / 60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        if u[3] <= 0:
            return bot.reply_to(message, "❌ У тебя нет кустов")
        gain = random.randint(1, u[3])
        update_field(user.id, "weed", gain)
        set_time(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ --------
    if text.startswith("продать "):
        parts = text.split()
        if "кексы" in text:
            n = int(parts[2])
            if u[5] < n:
                return bot.reply_to(message, "❌ Нет кексов")
            earned = n // 5
            update_field(user.id, "cakes", -n)
            update_field(user.id, "coins", earned)
            return bot.reply_to(message, f"💰 Продал {n} кексов → +{earned} коинов")
        elif "косяки" in text:
            n = int(parts[1])
            if u[6] < n:
                return bot.reply_to(message, "❌ Нет косяков")
            earned = n // 2
            update_field(user.id, "joints", -n)
            update_field(user.id, "coins", earned)
            return bot.reply_to(message, f"💰 Продал {n} косяков → +{earned} коинов")
        else:
            n = int(parts[1])
            if u[4] < n:
                return bot.reply_to(message, "❌ Нет конопли")
            earned = n // 10
            update_field(user.id, "weed", -n)
            update_field(user.id, "coins", earned)
            return bot.reply_to(message, f"💰 Продал {n} конопли → +{earned} коинов")

    # -------- ИСПЕЧЬ --------
    if text.startswith("испечь"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        burned = 0
        baked = 0
        for _ in range(n):
            if random.random() < 0.3:
                burned += 1
            else:
                baked += 1
        update_field(user.id, "weed", -n)
        update_field(user.id, "cakes", baked)
        return bot.reply_to(message, f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

    # -------- СЪЕСТЬ (раз в час) --------
    if text.startswith("съесть"):
        if not cooldown_passed(u[10]):
            mins = int((timedelta(hours=1) - (now - datetime.fromisoformat(u[10]))).seconds / 60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        update_field(user.id, "cakes", -n)
        update_field(user.id, "hunger", n)
        set_time(user.id, "last_eat")
        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # -------- КРАФТ КОСЯКОВ --------
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        update_field(user.id, "weed", -n)
        update_field(user.id, "joints", n)
        return bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

    # -------- ПОДЫМИТЬ (раз в час) --------
    if text == "подымить":
        if u[6] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        if not cooldown_passed(u[11]):
            mins = int((timedelta(hours=1) - (now - datetime.fromisoformat(u[11]))).seconds / 60)
            return bot.reply_to(message, f"⏳ Подожди {mins} мин")
        effect = random.randint(1, 5)
        update_field(user.id, "joints", -1)
        update_field(user.id, "high", effect)
        set_time(user.id, "last_smoke")
        return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")