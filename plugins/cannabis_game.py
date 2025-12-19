import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name

ADMIN_ID = 123456789  # ← ТВОЙ ID

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
        return "еврик"
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "еврика"
    return "евриков"

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
            return bot.reply_to(message, "❌ ебатькредит 500")

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
            f"💶 Закинул {amount} {money_word(amount)}"
        )

    # ---------- ЧТО В МЕШОЧКЕ ----------
    if text == "что в мешочке":
        u = get_user(user)
        return bot.reply_to(
            message,
            f"🌿 {u['name']}\n\n"
            f"💶 {u['money']} {money_word(u['money'])}\n"
            f"🌱 Кусты: {u['bushes']}\n"
            f"🌿 Травка: {u['weed']}\n"
            f"🥮 Кексы: {u['cakes']}\n"
            f"🚬 Косяки: {u['joints']}\n"
            f"😵‍💫 Кайф: {u['high']}"
        )

    # ---------- КУПИТЬ ----------
    if text.startswith("купить"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ купить 5")

        n = int(parts[1])
        cost = n * 10
        u = get_user(user)

        if u["money"] < cost:
            lack = cost - u["money"]
            return bot.reply_to(
                message,
                f"❌ Не хватает {lack} {money_word(lack)}"
            )

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
                f"🚨 Облава! Скинул {lost}, унёс {got}"
            )

        cursor.execute(
            "UPDATE cannabis SET bushes = bushes + ? WHERE user_id=?",
            (n, str(user.id))
        )
        return bot.reply_to(
            message,
            f"🌱 Взял {n} кустов, −{cost} {money_word(cost)}"
        )

    # ---------- ФЕРМА ----------
    if text == "ферма":
        u = get_user(user)
        if u["bushes"] <= 0:
            return bot.reply_to(message, "❌ Пусто, нихуя нет")

        if not cooldown(u["last_collect"], 1):
            mins = int(
                (timedelta(hours=1) -
                 (datetime.now() - datetime.fromisoformat(u["last_collect"]))).total_seconds() // 60
            )
            return bot.reply_to(message, f"⏳ Подожди {mins} мин")

        gain = random.randint(1, u["bushes"])
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed + ?, last_collect = ?
            WHERE user_id=?
        """, (gain, datetime.now().isoformat(), str(user.id)))
        return bot.reply_to(message, f"🌿 Насобирал {gain} травы")

    # ---------- ПРОДАЖА ----------
    if text.startswith("продать"):
        parts = text.split()

        u = get_user(user)

        # ПРОДАТЬ КОНОПЛЮ
        if len(parts) == 2 and parts[1].isdigit():
            n = int(parts[1])
            if u["weed"] < n:
                return bot.reply_to(message, f"❌ Нечего впарить, не хватает {n - u['weed']}")
            earn = n * 1
            cursor.execute("""
                UPDATE cannabis
                SET weed = weed - ?, money = money + ?
                WHERE user_id=?
            """, (n, earn, str(user.id)))
            return bot.reply_to(
                message,
                f"💶 Впарил {n} травы → +{earn} {money_word(earn)}"
            )

        # ПРОДАТЬ КЕКСЫ
        if parts[:2] == ["продать", "кексы"] and parts[2].isdigit():
            n = int(parts[2])
            if u["cakes"] < n:
                return bot.reply_to(message, "❌ Кексов нет")
            earn = n * 5
            cursor.execute("""
                UPDATE cannabis
                SET cakes = cakes - ?, money = money + ?
                WHERE user_id=?
            """, (n, earn, str(user.id)))
            return bot.reply_to(
                message,
                f"💶 Слил {n} кексов → +{earn} {money_word(earn)}"
            )

        # ПРОДАТЬ КОСЯКИ
        if parts[:2] == ["продать", "косяки"] and parts[2].isdigit():
            n = int(parts[2])
            if u["joints"] < n:
                return bot.reply_to(message, "❌ Косяков нет")
            earn = n * 3
            cursor.execute("""
                UPDATE cannabis
                SET joints = joints - ?, money = money + ?
                WHERE user_id=?
            """, (n, earn, str(user.id)))
            return bot.reply_to(
                message,
                f"💶 Сбыл {n} косяков → +{earn} {money_word(earn)}"
            )

    # ---------- ИСПЕЧЬ ----------
    if text.startswith("испечь"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return

        n = int(parts[1])
        u = get_user(user)
        if u["weed"] < n:
            return bot.reply_to(message, "❌ Травы не хватает")

        baked = sum(1 for _ in range(n) if random.random() > 0.4)
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, cakes = cakes + ?
            WHERE user_id=?
        """, (n, baked, str(user.id)))
        return bot.reply_to(
            message,
            f"🥮 Испёк {baked}, остальное сгорело к хуям"
        )

    # ---------- КРАФТ ----------
    if text.startswith("крафт"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return

        n = int(parts[1])
        u = get_user(user)
        if u["weed"] < n:
            return bot.reply_to(message, "❌ Травы мало")

        made = sum(1 for _ in range(n) if random.random() > 0.2)
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, joints = joints + ?
            WHERE user_id=?
        """, (n, made, str(user.id)))
        return bot.reply_to(
            message,
            f"🚬 Скрутил {made}, остальное в труху"
        )