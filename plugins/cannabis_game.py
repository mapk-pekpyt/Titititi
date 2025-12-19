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
    name TEXT NOT NULL,
    coins INTEGER NOT NULL DEFAULT 1000,
    bushes INTEGER NOT NULL DEFAULT 0,
    weed INTEGER NOT NULL DEFAULT 0,
    cakes INTEGER NOT NULL DEFAULT 0,
    joints INTEGER NOT NULL DEFAULT 0,
    hunger INTEGER NOT NULL DEFAULT 0,
    high INTEGER NOT NULL DEFAULT 0,
    last_collect TEXT,
    last_smoke TEXT,
    last_eat TEXT
)
""")
conn.commit()

# ================== HELPERS ==================
def ensure_user(user):
    cursor.execute("""
        INSERT OR IGNORE INTO cannabis (user_id, name)
        VALUES (?, ?)
    """, (str(user.id), get_name(user)))

    cursor.execute("""
        UPDATE cannabis SET name=? WHERE user_id=?
    """, (get_name(user), str(user.id)))

    conn.commit()

def get_user(user):
    ensure_user(user)
    cursor.execute("""
        SELECT
            coins, bushes, weed, cakes, joints,
            hunger, high, last_collect, last_smoke, last_eat
        FROM cannabis WHERE user_id=?
    """, (str(user.id),))
    return cursor.fetchone()

def cooldown(ts, hours=1):
    if not ts:
        return True
    return datetime.now() - datetime.fromisoformat(ts) >= timedelta(hours=hours)

# ================== GAME ==================
def handle(bot, message):
    if not message.text:
        return

    text = message.text.lower().strip()
    user = message.from_user
    name = get_name(user)

    coins, bushes, weed, cakes, joints, hunger, high, last_collect, last_smoke, last_eat = get_user(user)

    # -------- БАЛАНС --------
    if text == "баланс":
        return bot.reply_to(message,
            f"🌿 {name}\n\n"
            f"💰 Коины: {coins}\n"
            f"🌱 Кусты: {bushes}\n"
            f"🌿 Конопля: {weed}\n"
            f"🥮 Кексы: {cakes}\n"
            f"🚬 Косяки: {joints}\n"
            f"❤️ Сытость: {hunger}\n"
            f"😵‍💫 Кайф: {high}"
        )

    # -------- КУПИТЬ --------
    if text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split()) > 1 else 1
        cost = n * 10
        if coins < cost:
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
        if bushes <= 0:
            return bot.reply_to(message, "❌ Нет кустов")
        if not cooldown(last_collect):
            return bot.reply_to(message, "⏳ Сбор раз в час")

        gain = random.randint(1, bushes)
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed + ?, last_collect=?
            WHERE user_id=?
        """, (gain, datetime.now().isoformat(), str(user.id)))
        conn.commit()
        return bot.reply_to(message, f"🌿 Собрано {gain}")

    # -------- ПРОДАТЬ --------
    if text.startswith("продать "):
        n = int(text.split()[1])
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        earned = n // 10
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, coins = coins + ?
            WHERE user_id=?
        """, (n, earned, str(user.id)))
        conn.commit()
        return bot.reply_to(message, f"💰 +{earned} коинов")

    # -------- КРАФТ --------
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, joints = joints + ?
            WHERE user_id=?
        """, (n, n, str(user.id)))
        conn.commit()
        return bot.reply_to(message, f"🚬 Скрафтил {n}")

    # -------- ДУНУТЬ --------
    if text == "дунуть":
        if joints <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        if not cooldown(last_smoke):
            return bot.reply_to(message, "⏳ Раз в час")

        effect = random.randint(1, 5)
        cursor.execute("""
            UPDATE cannabis
            SET joints=joints-1, high=high+?, last_smoke=?
            WHERE user_id=?
        """, (effect, datetime.now().isoformat(), str(user.id)))
        conn.commit()
        return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")