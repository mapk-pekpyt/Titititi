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
    money INTEGER DEFAULT 1000,
    bushes INTEGER DEFAULT 0,
    weed INTEGER DEFAULT 0,
    cakes INTEGER DEFAULT 0,
    joints INTEGER DEFAULT 0,
    hunger INTEGER DEFAULT 0,
    high INTEGER DEFAULT 0,
    last_collect TEXT,
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

def get(user):
    ensure(user)
    cursor.execute("SELECT * FROM cannabis WHERE user_id=?", (str(user.id),))
    return cursor.fetchone()

def add(uid, field, value):
    cursor.execute(
        f"UPDATE cannabis SET {field}=MAX({field}+?,0) WHERE user_id=?",
        (value, str(uid))
    )
    conn.commit()

def set_time(uid, field):
    cursor.execute(
        f"UPDATE cannabis SET {field}=? WHERE user_id=?",
        (datetime.now().isoformat(), str(uid))
    )
    conn.commit()

def cooldown(last, hours=1):
    if not last:
        return True
    return datetime.now() - datetime.fromisoformat(last) >= timedelta(hours=hours)

def money_word(n):
    if n % 10 == 1 and n % 100 != 11:
        return "еврейчик"
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "еврейчика"
    return "еврейчиков"

def parse_int(parts, idx):
    try:
        return int(parts[idx])
    except:
        return None

# ================== GAME ==================
def handle(bot, message):
    if not message.text:
        return

    user = message.from_user
    text = message.text.lower().strip()
    parts = text.split()
    u = get(user)

    money, bushes, weed, cakes, joints = u[2], u[3], u[4], u[5], u[6]

    # -------- БАЛАНС --------
    if text == "баланс":
        return bot.reply_to(
            message,
            f"🌿 {u[1]}\n\n"
            f"💶 {money} {money_word(money)}\n"
            f"🌱 Кусты: {bushes}\n"
            f"🌿 Конопля: {weed}\n"
            f"🥮 Кексы: {cakes}\n"
            f"🚬 Косяки: {joints}\n"
            f"❤️ Сытость: {u[7]}\n"
            f"😵‍💫 Кайф: {u[8]}"
        )

    # -------- КУПИТЬ --------
    if parts and parts[0] == "купить":
        n = parse_int(parts, 1)
        if not n or n <= 0:
            return bot.reply_to(message, "❌ Пример: купить 5")

        cost = n * 10
        if money < cost:
            return bot.reply_to(message, f"❌ Нужно {cost} {money_word(cost)}")

        add(user.id, "money", -cost)
        add(user.id, "bushes", n)
        return bot.reply_to(message, f"🌱 Куплено {n} кустов")

    # -------- СОБРАТЬ --------
    if text == "собрать":
        if bushes <= 0:
            return bot.reply_to(message, "❌ Нет кустов")

        if not cooldown(u[9]):
            return bot.reply_to(message, "⏳ Сбор раз в час")

        gain = random.randint(1, bushes)
        add(user.id, "weed", gain)
        set_time(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ КЕКСЫ --------
    if parts[:2] == ["продать", "кексы"]:
        n = parse_int(parts, 2)
        if not n or n <= 0:
            return bot.reply_to(message, "❌ Пример: продать кексы 3")
        if cakes < n:
            return bot.reply_to(message, "❌ Нет кексов")

        earn = n * 5
        add(user.id, "cakes", -n)
        add(user.id, "money", earn)
        return bot.reply_to(message, f"💶 +{earn} {money_word(earn)}")

    # -------- ПРОДАТЬ КОСЯКИ --------
    if parts[:2] == ["продать", "косяки"]:
        n = parse_int(parts, 2)
        if not n or n <= 0:
            return bot.reply_to(message, "❌ Пример: продать косяки 2")
        if joints < n:
            return bot.reply_to(message, "❌ Нет косяков")

        earn = n * 3
        add(user.id, "joints", -n)
        add(user.id, "money", earn)
        return bot.reply_to(message, f"💶 +{earn} {money_word(earn)}")

    # -------- ПРОДАТЬ КОНОПЛЮ --------
    if parts and parts[0] == "продать":
        n = parse_int(parts, 1)
        if not n or n <= 0:
            return bot.reply_to(message, "❌ Пример: продать 10")
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        earn = n * 1
        add(user.id, "weed", -n)
        add(user.id, "money", earn)
        return bot.reply_to(message, f"💶 +{earn} {money_word(earn)}")

    # -------- ИСПЕЧЬ --------
    if parts and parts[0] == "испечь":
        n = parse_int(parts, 1)
        if not n or n <= 0:
            return bot.reply_to(message, "❌ Пример: испечь 5")
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        baked = sum(1 for _ in range(n) if random.random() > 0.4)
        add(user.id, "weed", -n)
        add(user.id, "cakes", baked)
        return bot.reply_to(message, f"🥮 Испёк {baked}, остальное сгорело 🔥")

    # -------- КРАФТ --------
    if parts and parts[0] == "крафт":
        n = parse_int(parts, 1)
        if not n or n <= 0:
            return bot.reply_to(message, "❌ Пример: крафт 5")
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        success = sum(1 for _ in range(n) if random.random() > 0.2)
        add(user.id, "weed", -n)
        add(user.id, "joints", success)
        return bot.reply_to(message, f"🚬 Скрутил {success}, остальное развалилось")

    # -------- ДУНУТЬ --------
    if text == "дунуть":
        if joints <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        if not cooldown(u[10]):
            return bot.reply_to(message, "⏳ Дунуть можно раз в час")

        add(user.id, "joints", -1)

        if random.random() < 0.7:
            effect = random.randint(1, 5)
            add(user.id, "high", effect)
            msg = f"😵‍💫 Кайф +{effect}"
        else:
            effect = random.randint(1, 3)
            add(user.id, "high", -effect)
            msg = f"🤢 Подавился дымом −{effect}"

        set_time(user.id, "last_smoke")
        return bot.reply_to(message, msg)