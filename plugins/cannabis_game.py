import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name

ADMIN_ID = 5791171535  # ← ТВОЙ ID

DB = "data/cannabis_game.db"
conn = sqlite3.connect(DB, check_same_thread=False, isolation_level=None)
conn.row_factory = sqlite3.Row
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

    # ---------- АДМИН КРЕДИТ ----------
    if text.startswith("ебатькредит"):
        if user.id != ADMIN_ID:
            return

        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: ебатькредит 500")

        amount = int(parts[1])

        target = user
        if message.reply_to_message:
            target = message.reply_to_message.from_user

        ensure(target)
        cursor.execute(
            "UPDATE cannabis SET money = money + ? WHERE user_id=?",
            (amount, str(target.id))
        )
        return bot.reply_to(
            message,
            f"💶 Начислено {amount} {money_word(amount)}"
        )

    # ---------- БАЛАНС ----------
    if text == "баланс":
        u = get_user(user)
        return bot.reply_to(
            message,
            f"🌿 {u['name']}\n\n"
            f"💶 {u['money']} {money_word(u['money'])}\n"
            f"🌱 Кусты: {u['bushes']}\n"
            f"🌿 Конопля: {u['weed']}\n"
            f"🥮 Кексы: {u['cakes']}\n"
            f"🚬 Косяки: {u['joints']}\n"
            f"❤️ Сытость: {u['hunger']}\n"
            f"😵‍💫 Кайф: {u['high']}"
        )

    # ---------- КУПИТЬ ----------
    if text.startswith("купить"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: купить 5")

        n = int(parts[1])
        cost = n * 10
        u = get_user(user)

        if u["money"] < cost:
            lack = cost - u["money"]
            return bot.reply_to(message, f"❌ Не хватает {lack} {money_word(lack)}")

        cursor.execute(
            "UPDATE cannabis SET money = money - ? WHERE user_id=?",
            (cost, str(user.id))
        )

        if random.random() < 0.1:
            lost = random.randint(1, n)
            got = n - lost
            if got > 0:
                cursor.execute(
                    "UPDATE cannabis SET bushes = bushes + ? WHERE user_id=?",
                    (got, str(user.id))
                )
            return bot.reply_to(
                message,
                f"😱 Облава! Потерял {lost}, унёс {got}"
            )

        cursor.execute(
            "UPDATE cannabis SET bushes = bushes + ? WHERE user_id=?",
            (n, str(user.id))
        )
        return bot.reply_to(
            message,
            f"🌱 Куплено {n} кустов за {cost} {money_word(cost)}"
        )

    # ---------- СОБРАТЬ ----------
    if text == "собрать":
        u = get_user(user)
        if u["bushes"] <= 0:
            return bot.reply_to(message, "❌ Нет кустов")

        if not cooldown(u["last_collect"], 1):
            mins = int(
                (timedelta(hours=1) -
                 (datetime.now() - datetime.fromisoformat(u["last_collect"]))).total_seconds() // 60
            )
            return bot.reply_to(message, f"⏳ Осталось {mins} мин")

        gain = random.randint(1, u["bushes"])
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed + ?, last_collect = ?
            WHERE user_id=?
        """, (gain, datetime.now().isoformat(), str(user.id)))
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # ---------- ИСПЕЧЬ ----------
    if text.startswith("испечь"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: испечь 5")

        n = int(parts[1])
        u = get_user(user)
        if u["weed"] < n:
            return bot.reply_to(message, "❌ Не хватает конопли")

        baked = sum(1 for _ in range(n) if random.random() > 0.4)
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, cakes = cakes + ?
            WHERE user_id=?
        """, (n, baked, str(user.id)))
        return bot.reply_to(
            message,
            f"🥮 Испёк {baked}, остальное сгорело"
        )

    # ---------- КРАФТ ----------
    if text.startswith("крафт"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: крафт 5")

        n = int(parts[1])
        u = get_user(user)
        if u["weed"] < n:
            return bot.reply_to(message, "❌ Не хватает конопли")

        made = sum(1 for _ in range(n) if random.random() > 0.2)
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, joints = joints + ?
            WHERE user_id=?
        """, (n, made, str(user.id)))
        return bot.reply_to(
            message,
            f"🚬 Скручено {made}, остальное в труху"
        )