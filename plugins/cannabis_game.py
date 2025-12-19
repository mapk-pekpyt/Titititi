import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name

DB = "data/cannabis_game.db"
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
        "INSERT OR IGNORE INTO cannabis (user_id, name) VALUES (?,?)",
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

def add(user_id, field, value):
    cursor.execute(
        f"UPDATE cannabis SET {field} = {field} + ? WHERE user_id=?",
        (value, str(user_id))
    )
    conn.commit()

def set_time(user_id, field):
    cursor.execute(
        f"UPDATE cannabis SET {field}=? WHERE user_id=?",
        (datetime.now().isoformat(), str(user_id))
    )
    conn.commit()

def cooldown(last_time, hours=1):
    if not last_time:
        return True
    return datetime.now() - datetime.fromisoformat(last_time) >= timedelta(hours=hours)

def time_left(last_time, hours=1):
    if not last_time:
        return "0 мин"
    diff = timedelta(hours=hours) - (datetime.now() - datetime.fromisoformat(last_time))
    mins = max(int(diff.total_seconds() / 60), 0)
    return f"{mins} мин"

def money_word(n):
    if n % 10 == 1 and n % 100 != 11:
        return "еврейчик"
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "еврейчика"
    return "еврейчиков"

# ================== MAIN ==================
def handle(bot, message):
    user = message.from_user
    text = (message.text or "").lower().strip()
    u = get_user(user)

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

    # -------- КУПИТЬ КУСТЫ --------
    if text.startswith("купить"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: купить 5")

        n = int(parts[1])
        cost = n * 10

        u = get_user(user)
        money, bushes = u[2], u[3]

        if money < cost:
            return bot.reply_to(message, f"❌ Нужно {cost} {money_word(cost)}")

        # шанс подставного покупателя
        lost = 0
        if random.random() < 0.1:
            lost = random.randint(1, n)
            n -= lost

        cursor.execute(
            "UPDATE cannabis SET money = money - ?, bushes = bushes + ? WHERE user_id=?",
            (cost, n, str(user.id))
        )
        conn.commit()

        msg = f"🌱 Куплено {n} кустов за {cost} {money_word(cost)}"
        if lost > 0:
            msg += f"\n⚠️ Попытка была подставной, потеряно {lost} кустов!"
        return bot.reply_to(message, msg)

    # -------- СОБРАТЬ --------
    if text == "собрать":
        if bushes <= 0:
            return bot.reply_to(message, "❌ Нет кустов")

        if not cooldown(u[9], 1):
            return bot.reply_to(message, f"⏳ Подожди {time_left(u[9],1)} до следующего сбора")

        gain = random.randint(1, bushes)
        add(user.id, "weed", gain)
        set_time(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ КОНОПЛЮ --------
    if text.startswith("продать ") and text.split()[1].isdigit():
        n = int(text.split()[1])
        if weed < n:
            return bot.reply_to(message, f"❌ Ты не можешь впарить {n} конопли — нет столько у тебя")

        earn = n * 1
        add(user.id, "weed", -n)
        add(user.id, "money", earn)
        return bot.reply_to(message, f"💶 Впарено {n} конопли → +{earn} {money_word(earn)}")

    # -------- ПРОДАТЬ КЕКСЫ --------
    if text.startswith("продать кексы"):
        parts = text.split()
        if len(parts) != 3 or not parts[2].isdigit():
            return bot.reply_to(message, "❌ Пример: продать кексы 5")

        n = int(parts[2])
        if cakes < n:
            return bot.reply_to(message, "❌ Нет кексов")

        earn = n * 5
        add(user.id, "cakes", -n)
        add(user.id, "money", earn)
        return bot.reply_to(message, f"💶 Впарено {n} кексов → +{earn} {money_word(earn)}")

    # -------- ПРОДАТЬ КОСЯКИ --------
    if text.startswith("продать косяки"):
        parts = text.split()
        if len(parts) != 3 or not parts[2].isdigit():
            return bot.reply_to(message, "❌ Пример: продать косяки 3")

        n = int(parts[2])
        if joints < n:
            return bot.reply_to(message, "❌ Нет косяков")

        earn = n * 3
        add(user.id, "joints", -n)
        add(user.id, "money", earn)
        return bot.reply_to(message, f"💶 Впарено {n} косяков → +{earn} {money_word(earn)}")

    # -------- ИСПЕЧЬ --------
    if text.startswith("испечь"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: испечь 5")
        n = int(parts[1])
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        baked = sum(1 for _ in range(n) if random.random() > 0.4)
        add(user.id, "weed", -n)
        add(user.id, "cakes", baked)
        return bot.reply_to(message, f"🥮 Получилось {baked}, остальное сгорело")

    # -------- КРАФТ --------
    if text.startswith("крафт"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: крафт 3")
        n = int(parts[1])
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        made = sum(1 for _ in range(n) if random.random() > 0.2)
        add(user.id, "weed", -n)
        add(user.id, "joints", made)
        return bot.reply_to(message, f"🚬 Скручено {made}, остальное в труху")

    # -------- ДУНУТЬ --------
    if text == "дунуть":
        if joints <= 0:
            return bot.reply_to(message, "❌ Нет косяков")

        if not cooldown(u[10], 1):
            return bot.reply_to(message, f"⏳ Раз в час, осталось {time_left(u[10],1)}")

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