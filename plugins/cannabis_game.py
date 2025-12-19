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
    last_smoke TEXT,
    last_eat TEXT
)
""")
conn.commit()

# ================== HELPERS ==================
def ensure(user):
    cursor.execute(
        "INSERT OR IGNORE INTO cannabis (user_id, name) VALUES (?, ?)",
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

def can_use(last_time, hours=1):
    if not last_time:
        return True
    return datetime.now() - datetime.fromisoformat(last_time) >= timedelta(hours=hours)

def clamp(v):
    return max(0, int(v))

# ================== GAME ==================
def handle(bot, message):
    if not message.text:
        return

    text = message.text.lower().strip()
    user = message.from_user
    name = get_name(user)

    u = get_user(user)

    # индексы ЧЁТКО
    COINS = 2
    BUSHES = 3
    WEED = 4
    CAKES = 5
    JOINTS = 6
    HUNGER = 7
    HIGH = 8
    LAST_COLLECT = 9
    LAST_SMOKE = 10
    LAST_EAT = 11

    # -------- БАЛАНС --------
    if text == "баланс":
        return bot.reply_to(
            message,
            f"🌿 {name}\n\n"
            f"💰 Коины: {u[COINS]}\n"
            f"🌱 Кусты: {u[BUSHES]}\n"
            f"🌿 Конопля: {u[WEED]}\n"
            f"🥮 Кексы: {u[CAKES]}\n"
            f"🚬 Косяки: {u[JOINTS]}\n"
            f"❤️ Сытость: {u[HUNGER]}\n"
            f"😵‍💫 Кайф: {u[HIGH]}"
        )

    # -------- КУПИТЬ --------
    if text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split()) > 1 else 1
        cost = n * 10
        if u[COINS] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")

        cursor.execute("""
            UPDATE cannabis
            SET coins = coins - ?, bushes = bushes + ?
            WHERE user_id=?
        """, (cost, n, str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"🌱 Куплено {n} кустов")

    # -------- СОБРАТЬ --------
    if text == "собрать":
        if not can_use(u[LAST_COLLECT]):
            return bot.reply_to(message, "⏳ Сбор раз в час")

        if u[BUSHES] <= 0:
            return bot.reply_to(message, "❌ Нет кустов")

        gain = random.randint(1, u[BUSHES])

        cursor.execute("""
            UPDATE cannabis
            SET weed = weed + ?, last_collect=?
            WHERE user_id=?
        """, (gain, datetime.now().isoformat(), str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ --------
    if text.startswith("продать "):
        n = int(text.split()[1])
        if u[WEED] < n:
            return bot.reply_to(message, "❌ Нет конопли")

        earned = n // 10
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, coins = coins + ?
            WHERE user_id=?
        """, (n, earned, str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"💰 +{earned} коинов")

    # -------- ИСПЕЧЬ --------
    if text.startswith("испечь"):
        n = int(text.split()[1])
        if u[WEED] < n:
            return bot.reply_to(message, "❌ Нет конопли")

        baked = sum(1 for _ in range(n) if random.random() > 0.3)

        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, cakes = cakes + ?
            WHERE user_id=?
        """, (n, baked, str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"🥮 Испёк {baked}")

    # -------- СЪЕСТЬ --------
    if text.startswith("съесть"):
        n = int(text.split()[1])
        if u[CAKES] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        if not can_use(u[LAST_EAT]):
            return bot.reply_to(message, "⏳ Есть можно раз в час")

        cursor.execute("""
            UPDATE cannabis
            SET cakes=cakes-?, hunger=hunger+?, last_eat=?
            WHERE user_id=?
        """, (n, n, datetime.now().isoformat(), str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # -------- КРАФТ --------
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if u[WEED] < n:
            return bot.reply_to(message, "❌ Нет конопли")

        cursor.execute("""
            UPDATE cannabis
            SET weed=weed-?, joints=joints+?
            WHERE user_id=?
        """, (n, n, str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

    # -------- ДУНУТЬ --------
    if text == "дунуть":
        if u[JOINTS] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        if not can_use(u[LAST_SMOKE]):
            return bot.reply_to(message, "⏳ Дунуть можно раз в час")

        effect = random.randint(1, 5)

        cursor.execute("""
            UPDATE cannabis
            SET joints=joints-1, high=high+?, last_smoke=?
            WHERE user_id=?
        """, (effect, datetime.now().isoformat(), str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")