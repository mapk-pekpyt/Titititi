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
    money INTEGER NOT NULL DEFAULT 1000,
    bushes INTEGER NOT NULL DEFAULT 0,
    weed INTEGER NOT NULL DEFAULT 0,
    cakes INTEGER NOT NULL DEFAULT 0,
    joints INTEGER NOT NULL DEFAULT 0,
    hunger INTEGER NOT NULL DEFAULT 0,
    high INTEGER NOT NULL DEFAULT 0,
    last_collect TEXT,
    last_smoke TEXT
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

def money_word(n):
    if n % 10 == 1 and n % 100 != 11:
        return "еврейчик"
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "еврейчика"
    return "еврейчиков"

def cooldown(last_time, hours=1):
    if not last_time:
        return True
    return datetime.now() - datetime.fromisoformat(last_time) >= timedelta(hours=hours)

# ================== MAIN ==================
def handle(bot, message):
    user = message.from_user
    text = (message.text or "").lower().strip()
    u = get_user(user)

    # -------- БАЛАНС --------
    if text == "баланс":
        u = get_user(user)
        return bot.reply_to(
            message,
            f"🌿 {u[1]}\n\n"
            f"💶 {u[2]} {money_word(u[2])}\n"
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
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: купить 5")

        n = int(parts[1])
        cost = n * 10

        # 🔒 АТОМАРНАЯ ПРОВЕРКА + СПИСАНИЕ
        cursor.execute("""
            UPDATE cannabis
            SET money = money - ?
            WHERE user_id = ? AND money >= ?
        """, (cost, str(user.id), cost))

        if cursor.rowcount == 0:
            return bot.reply_to(
                message,
                f"❌ Нужно {cost} {money_word(cost)}"
            )

        # облава
        if random.random() < 0.1:
            lost = random.randint(1, n)
            got = n - lost
            if got > 0:
                cursor.execute(
                    "UPDATE cannabis SET bushes = bushes + ? WHERE user_id=?",
                    (got, str(user.id))
                )
            conn.commit()
            return bot.reply_to(
                message,
                f"😱 Барыга — мент! Ты потерял {lost}, успел унести {got}"
            )

        cursor.execute(
            "UPDATE cannabis SET bushes = bushes + ? WHERE user_id=?",
            (n, str(user.id))
        )
        conn.commit()
        return bot.reply_to(
            message,
            f"🌱 Куплено {n} кустов за {cost} {money_word(cost)}"
        )

    # -------- СОБРАТЬ --------
    if text == "собрать":
        if u[3] <= 0:
            return bot.reply_to(message, "❌ Нет кустов")

        if not cooldown(u[9], 1):
            mins = int(
                (timedelta(hours=1) -
                 (datetime.now() - datetime.fromisoformat(u[9]))).total_seconds() // 60
            )
            return bot.reply_to(message, f"⏳ Подожди {mins} мин")

        gain = random.randint(1, u[3])
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed + ?, last_collect = ?
            WHERE user_id=?
        """, (gain, datetime.now().isoformat(), str(user.id)))
        conn.commit()
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ДУНУТЬ --------
    if text == "дунуть":
        if u[6] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")

        if not cooldown(u[10], 1):
            mins = int(
                (timedelta(hours=1) -
                 (datetime.now() - datetime.fromisoformat(u[10]))).total_seconds() // 60
            )
            return bot.reply_to(message, f"⏳ Подожди {mins} мин")

        effect = random.randint(-3, 5)
        cursor.execute("""
            UPDATE cannabis
            SET joints = joints - 1,
                high = high + ?,
                last_smoke = ?
            WHERE user_id=?
        """, (effect, datetime.now().isoformat(), str(user.id)))
        conn.commit()

        if effect > 0:
            return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")
        elif effect < 0:
            return bot.reply_to(message, f"🤢 Подавился дымом −{abs(effect)}")
        else:
            return bot.reply_to(message, "😐 Ни зашло ни влетело")