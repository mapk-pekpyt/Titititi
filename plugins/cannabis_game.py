import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name

DB = "data/cannabis_game.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
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

def money_word(n):
    if n % 10 == 1 and n % 100 != 11:
        return "еврик"
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "еврика"
    return "евриков"

# ================== MAIN ==================
def handle(bot, message):
    user = message.from_user
    text = (message.text or "").lower().strip()
    u = get_user(user)

    # ---------- ЧТО В МЕШОЧКЕ ----------
    if text == "что в мешочке":
        return bot.reply_to(
            message,
            f"🌿 {u['name']}\n\n"
            f"💶 {u['money']} {money_word(u['money'])}\n"
            f"🌱 Кусты: {u['bushes']}\n"
            f"🌿 Травка: {u['weed']}\n"
            f"🥮 Кексы: {u['cakes']}\n"
            f"🚬 Косяки: {u['joints']}\n"
            f"❤️ Сытость: {u['hunger']}"
        )

    # ---------- КУПИТЬ ----------
    if text.startswith("купить"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: купить 5")

        n = int(parts[1])
        cost = n * 10

        if u["money"] < cost:
            return bot.reply_to(
                message,
                f"❌ Не хватает {cost - u['money']} {money_word(cost - u['money'])}"
            )

        add(user.id, "money", -cost)

        if random.random() < 0.1:
            lost = random.randint(1, n)
            got = n - lost
            if got > 0:
                add(user.id, "bushes", got)
            return bot.reply_to(
                message,
                f"😱 Подставной барыга!\n"
                f"Потерял {lost} кустов, урвал {got}"
            )

        add(user.id, "bushes", n)
        return bot.reply_to(
            message,
            f"🌱 Куплено {n} кустов за {cost} {money_word(cost)}"
        )

    # ---------- ФЕРМА ----------
    if text == "ферма":
        if u["bushes"] <= 0:
            return bot.reply_to(message, "❌ Ферма пустая")

        if not cooldown(u["last_collect"], 1):
            mins = int(
                (timedelta(hours=1) -
                 (datetime.now() - datetime.fromisoformat(u["last_collect"]))).total_seconds() // 60
            )
            return bot.reply_to(message, f"⏳ Приходи через {mins} мин")

        gain = random.randint(1, u["bushes"])
        add(user.id, "weed", gain)
        set_time(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрал {gain} травки")

    # ---------- ПРОДАТЬ ----------
    if text.startswith("продать"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: продать 5")

        n = int(parts[1])
        if u["weed"] < n:
            return bot.reply_to(message, "❌ Нечего продавать")

        add(user.id, "weed", -n)
        add(user.id, "money", n)
        return bot.reply_to(
            message,
            f"💶 Впарил {n} травки → +{n} {money_word(n)}"
        )

    # ---------- ИСПЕЧЬ ----------
    if text.startswith("испечь"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: испечь 5")

        n = int(parts[1])
        if u["weed"] < n:
            return bot.reply_to(message, "❌ Не хватает травки")

        baked = sum(1 for _ in range(n) if random.random() > 0.4)
        add(user.id, "weed", -n)
        add(user.id, "cakes", baked)
        return bot.reply_to(
            message,
            f"🥮 Испёк {baked}, остальное сгорело"
        )

    # ---------- КРАФТ ----------
    if text.startswith("крафт"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: крафт 3")

        n = int(parts[1])
        if u["weed"] < n:
            return bot.reply_to(message, "❌ Нет сырья")

        made = sum(1 for _ in range(n) if random.random() > 0.2)
        add(user.id, "weed", -n)
        add(user.id, "joints", made)
        return bot.reply_to(
            message,
            f"🚬 Скрутил {made}, остальное в труху"
        )

    # ---------- СЪЕСТЬ ----------
    if text.startswith("съесть"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ съесть 2")

        n = int(parts[1])
        if u["cakes"] < n:
            return bot.reply_to(message, "❌ Во рту пусто")

        add(user.id, "cakes", -n)
        add(user.id, "hunger", n)
        return bot.reply_to(
            message,
            f"🥮 Сожрал {n}\n❤️ Сытость +{n}"
        )

    # ---------- ДУНУТЬ ----------
    if text == "дунуть":
        if u["joints"] <= 0:
            return bot.reply_to(message, "❌ Дунуть нечего")

        if not cooldown(u["last_smoke"], 1):
            mins = int(
                (timedelta(hours=1) -
                 (datetime.now() - datetime.fromisoformat(u["last_smoke"]))).total_seconds() // 60
            )
            return bot.reply_to(message, f"⏳ Подожди {mins} мин")

        add(user.id, "joints", -1)
        set_time(user.id, "last_smoke")

        roll = random.random()

        if roll < 0.6:
            effect = random.randint(1, 5)
            add(user.id, "high", effect)
            return bot.reply_to(message, f"😵‍💫 Зашло\nКайф +{effect}")

        if roll < 0.85:
            return bot.reply_to(message, "😒 Беспонтовая попалась\nКайф +0")

        effect = random.randint(1, 3)
        add(user.id, "high", -effect)
        return bot.reply_to(message, f"🤢 Подавился дымом\nКайф −{effect}")