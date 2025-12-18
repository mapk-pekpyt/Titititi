import sqlite3, random
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
    cursor.execute("SELECT * FROM cannabis WHERE user_id=?", (str(user.id),))
    return cursor.fetchone()

def update_field(user_id, field, delta):
    cursor.execute(
        f"UPDATE cannabis SET {field}=MAX(0,{field}+?) WHERE user_id=?",
        (delta, str(user_id))
    )
    conn.commit()

def set_time(user_id, field):
    cursor.execute(
        f"UPDATE cannabis SET {field}=? WHERE user_id=?",
        (datetime.now().isoformat(), str(user_id))
    )
    conn.commit()

def can_use(user, field, hours=1):
    user_row = get_user(user)
    last = user_row[{"last_collect":9, "last_eat":10, "last_smoke":11}[field]]
    if not last:
        return True
    last_time = datetime.fromisoformat(last)
    return datetime.now() - last_time >= timedelta(hours=hours)

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
            f"🌿 {name}\n"
            f"💰 Коины: {u[2]}\n"
            f"🌱 Кусты: {u[3]}\n"
            f"🌿 Конопля: {u[4]}\n"
            f"🥮 Кексы: {u[5]}\n"
            f"🚬 Косяки: {u[6]}\n"
            f"❤️ Сытость: {u[7]}\n"
            f"😵‍💫 Кайф: {u[8]}"
        )

    # -------- КУПИТЬ КУСТЫ --------
    if text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split()) > 1 else 1
        cost = n * 10
        if u[2] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")
        update_field(user.id, "coins", -cost)
        update_field(user.id, "bushes", n)
        top_plugin.update_stat("all_chats", user, "bushes")
        return bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

    # -------- СОБРАТЬ (раз в час) --------
    if text == "собрать":
        if not can_use(user, "last_collect"):
            last = datetime.fromisoformat(u[9])
            mins = int((timedelta(hours=1)-(datetime.now()-last)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        if u[3] <= 0:
            return bot.reply_to(message, "❌ Нет кустов")
        gain = random.randint(1, u[3])
        update_field(user.id, "weed", gain)
        set_time(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ --------
    if text.startswith("продать ") and not text.startswith("продать кексы"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        earned = max(n//10,1)
        update_field(user.id, "weed", -n)
        update_field(user.id, "coins", earned)
        return bot.reply_to(message, f"💰 Продано {n} → +{earned} коинов")

    # -------- ИСПЕЧЬ --------
    if text.startswith("испечь"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        baked, burned = 0,0
        for _ in range(n):
            if random.random() < 0.3: burned+=1
            else: baked+=1
        update_field(user.id, "weed", -n)
        update_field(user.id, "cakes", baked)
        return bot.reply_to(message, f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

    # -------- СЪЕСТЬ --------
    if text.startswith("съесть"):
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        if not can_use(user, "last_eat"):
            last = datetime.fromisoformat(u[10])
            mins = int((timedelta(hours=1)-(datetime.now()-last)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        update_field(user.id, "cakes", -n)
        update_field(user.id, "hunger", n)
        set_time(user.id, "last_eat")
        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # -------- ПРОДАТЬ КЕКСЫ --------
    if text.startswith("продать кексы"):
        n = int(text.split()[2])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        earned = max(n//5,1)
        update_field(user.id, "cakes", -n)
        update_field(user.id, "coins", earned)
        return bot.reply_to(message, f"💰 Продал {n} кексов → +{earned} коинов")

    # -------- КРАФТ --------
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
        if not can_use(user, "last_smoke"):
            last = datetime.fromisoformat(u[11])
            mins = int((timedelta(hours=1)-(datetime.now()-last)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        effect = random.randint(1,5)
        update_field(user.id, "joints", -1)
        update_field(user.id, "high", effect)
        set_time(user.id, "last_smoke")
        top_plugin.update_stat("all_chats", user, "high", effect)
        return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")