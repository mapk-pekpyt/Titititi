import sqlite3, random
from datetime import datetime, timedelta
from plugins.common import get_name

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

# ================== TABLE ==================
# ОБЩАЯ ПАМЯТЬ (БЕЗ chat_id)
cursor.execute("""
CREATE TABLE IF NOT EXISTS cannabis (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    coins INTEGER NOT NULL DEFAULT 1000,
    bushes INTEGER NOT NULL DEFAULT 0,
    weed INTEGER NOT NULL DEFAULT 0,
    cakes INTEGER NOT NULL DEFAULT 0,
    joints INTEGER NOT NULL DEFAULT 0,
    hunger INTEGER NOT NULL DEFAULT 0,
    high INTEGER NOT NULL DEFAULT 0,
    last_collect TEXT,
    last_eat TEXT,
    last_smoke TEXT
)
""")
conn.commit()

# ================== HELPERS ==================
def ensure_user(user):
    cursor.execute(
        "INSERT OR IGNORE INTO cannabis(user_id, name) VALUES (?, ?)",
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

def clamp_update(user_id, field, delta):
    cursor.execute(f"SELECT {field} FROM cannabis WHERE user_id=?", (str(user_id),))
    cur = cursor.fetchone()[0]
    new_val = max(0, cur + delta)
    cursor.execute(f"UPDATE cannabis SET {field}=? WHERE user_id=?", (new_val, str(user_id)))
    conn.commit()

def set_time(user_id, field):
    cursor.execute(f"UPDATE cannabis SET {field}=? WHERE user_id=?",
                   (datetime.now().isoformat(), str(user_id)))
    conn.commit()

def cooldown_ok(user, field, hours=1):
    cursor.execute(f"SELECT {field} FROM cannabis WHERE user_id=?", (str(user.id),))
    last = cursor.fetchone()[0]
    if not last:
        return True
    return datetime.now() - datetime.fromisoformat(last) >= timedelta(hours=hours)

# ================== GAME ==================
def handle(bot, message):
    user = message.from_user
    text = (message.text or "").lower().strip()
    name = get_name(user)
    u = get_user(user)

    # Индексы:
    # 0:user_id, 1:name, 2:coins, 3:bushes, 4:weed, 5:cakes, 6:joints, 7:hunger, 8:high

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
            f"😵‍💫 Кайф: {u[8]}"
        )

    # Купить кусты (10 коинов за куст)
    if text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split()) > 1 else 1
        cost = n * 10
        if u[2] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")
        clamp_update(user.id, "coins", -cost)
        clamp_update(user.id, "bushes", n)
        return bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

    # Собрать (раз в час)
    if text == "собрать":
        if not cooldown_ok(user, "last_collect", 1):
            cursor.execute("SELECT last_collect FROM cannabis WHERE user_id=?", (str(user.id),))
            last = cursor.fetchone()[0]
            mins = int((timedelta(hours=1) - (datetime.now() - datetime.fromisoformat(last))).seconds / 60)
            return bot.reply_to(message, f"⏳ Подожди {mins} мин")
        if u[3] <= 0:
            return bot.reply_to(message, "❌ Нет кустов")
        gain = random.randint(1, u[3])
        clamp_update(user.id, "weed", gain)
        set_time(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # Продать коноплю (10 конопли = 1 коин)
    if text.startswith("продать ") and not text.startswith("продать кексы"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        earned = n // 10
        clamp_update(user.id, "weed", -n)
        clamp_update(user.id, "coins", earned)
        return bot.reply_to(message, f"💰 Продано {n} → +{earned} коинов")

    # Испечь
    if text.startswith("испечь"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        baked = sum(1 for _ in range(n) if random.random() >= 0.3)
        clamp_update(user.id, "weed", -n)
        clamp_update(user.id, "cakes", baked)
        return bot.reply_to(message, f"🥮 Испёк {baked}")

    # Съесть (раз в час)
    if text.startswith("съесть"):
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        if not cooldown_ok(user, "last_eat", 1):
            return bot.reply_to(message, "⏳ Рано")
        clamp_update(user.id, "cakes", -n)
        clamp_update(user.id, "hunger", n)
        set_time(user.id, "last_eat")
        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # Продать кексы (5 кексов = 1 коин)
    if text.startswith("продать кексы"):
        n = int(text.split()[2])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        earned = n // 5
        clamp_update(user.id, "cakes", -n)
        clamp_update(user.id, "coins", earned)
        return bot.reply_to(message, f"💰 Продал {n} кексов → +{earned}")

    # Крафт косяков
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        clamp_update(user.id, "weed", -n)
        clamp_update(user.id, "joints", n)
        return bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

    # Подымить (раз в час)
    if text == "подымить":
        if u[6] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        if not cooldown_ok(user, "last_smoke", 1):
            return bot.reply_to(message, "⏳ Рано")
        effect = random.randint(1, 5)
        clamp_update(user.id, "joints", -1)
        clamp_update(user.id, "high", effect)
        set_time(user.id, "last_smoke")
        return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")