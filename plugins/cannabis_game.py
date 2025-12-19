import sqlite3, random
from datetime import datetime, timedelta
from plugins.common import get_name

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

# ================== TABLE (БЕЗ ЛОМАНИЯ СТАРОЙ) ==================
cursor.execute("""
CREATE TABLE IF NOT EXISTS cannabis (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    money INTEGER,
    bushes INTEGER,
    weed INTEGER,
    cakes INTEGER,
    joints INTEGER,
    hunger INTEGER,
    high INTEGER,
    last_collect TEXT,
    last_smoke TEXT
)
""")
conn.commit()

# ================== FIX OLD DATA ==================
cursor.execute("""
UPDATE cannabis
SET money = 1000
WHERE money IS NULL OR typeof(money) != 'integer'
""")
conn.commit()

# ================== HELPERS ==================
def ensure(user):
    cursor.execute(
        "INSERT OR IGNORE INTO cannabis(user_id, name, money, bushes, weed, cakes, joints, hunger, high) "
        "VALUES (?, ?, 1000, 0, 0, 0, 0, 0, 0)",
        (str(user.id), get_name(user))
    )
    cursor.execute(
        "UPDATE cannabis SET name=? WHERE user_id=?",
        (get_name(user), str(user.id))
    )
    conn.commit()

def get(user):
    ensure(user)
    cursor.execute("""
        SELECT 
            user_id, name, money, bushes, weed, cakes, joints, hunger, high, last_collect, last_smoke
        FROM cannabis
        WHERE user_id=?
    """, (str(user.id),))
    return cursor.fetchone()

def cooldown(last, hours=1):
    if not last:
        return True
    return datetime.now() - datetime.fromisoformat(last) >= timedelta(hours=hours)

# ================== GAME ==================
def handle(bot, message):
    user = message.from_user
    text = (message.text or "").lower().strip()
    parts = text.split()

    u = get(user)

    # -------- БАЛАНС --------
    if text == "баланс":
        bot.reply_to(
            message,
            f"🌿 {u[1]}\n\n"
            f"💶 Еврейчики: {u[2]}\n"
            f"🌱 Кусты: {u[3]}\n"
            f"🌿 Конопля: {u[4]}\n"
            f"🥮 Кексы: {u[5]}\n"
            f"🚬 Косяки: {u[6]}\n"
            f"❤️ Сытость: {u[7]}\n"
            f"😵‍💫 Кайф: {u[8]}"
        )
        return

    # -------- КУПИТЬ --------
    if parts and parts[0] == "купить":
        n = int(parts[1]) if len(parts) > 1 else 1
        cost = n * 10
        if n <= 0 or u[2] < cost:
            bot.reply_to(message, "❌ Не хватает еврейчиков")
            return
        cursor.execute(
            "UPDATE cannabis SET money=money-?, bushes=bushes+? WHERE user_id=?",
            (cost, n, str(user.id))
        )
        conn.commit()
        bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} 💶")
        return

    # -------- СОБРАТЬ --------
    if text == "собрать":
        if not cooldown(u[9]):
            bot.reply_to(message, "⏳ Рано, подожди час")
            return
        if u[3] <= 0:
            bot.reply_to(message, "❌ Нет кустов")
            return
        gain = random.randint(1, u[3])
        cursor.execute(
            "UPDATE cannabis SET weed=weed+?, last_collect=? WHERE user_id=?",
            (gain, datetime.now().isoformat(), str(user.id))
        )
        conn.commit()
        bot.reply_to(message, f"🌿 Собрано {gain} конопли")
        return

    # -------- ПРОДАТЬ --------
    if parts and parts[0] == "продать" and len(parts) == 2:
        n = int(parts[1])
        if n <= 0 or u[4] < n:
            bot.reply_to(message, "❌ Нечего продавать")
            return
        money = n * 1
        cursor.execute(
            "UPDATE cannabis SET weed=weed-?, money=money+? WHERE user_id=?",
            (n, money, str(user.id))
        )
        conn.commit()
        bot.reply_to(message, f"💶 Продано {n} → +{money} еврейчиков")
        return

    # -------- КРАФТ --------
    if parts and parts[0] == "крафт":
        n = int(parts[1])
        if n <= 0 or u[4] < n:
            bot.reply_to(message, "❌ Нет конопли")
            return
        good = sum(1 for _ in range(n) if random.random() > 0.4)
        cursor.execute(
            "UPDATE cannabis SET weed=weed-?, joints=joints+? WHERE user_id=?",
            (n, good, str(user.id))
        )
        conn.commit()
        bot.reply_to(message, f"🚬 Скрутил {good}, остальное развалилось")
        return

    # -------- ДУНУТЬ --------
    if text == "дунуть":
        if u[6] <= 0:
            bot.reply_to(message, "❌ Нет косяков")
            return
        if not cooldown(u[10]):
            bot.reply_to(message, "⏳ Передышка нужна")
            return
        effect = random.choice([-3, -1, 0, 1, 3, 5])
        cursor.execute(
            "UPDATE cannabis SET joints=joints-1, high=high+?, last_smoke=? WHERE user_id=?",
            (effect, datetime.now().isoformat(), str(user.id))
        )
        conn.commit()
        bot.reply_to(
            message,
            f"🔥 Ты улетел 😵‍💫 (+{effect})" if effect > 0 else
            f"🤢 Подавился дымом ({effect})" if effect < 0 else
            "😐 Ни о чём"
        )
        return