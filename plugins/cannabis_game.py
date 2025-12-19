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
        f"UPDATE cannabis SET {field} = MAX({field} + ?, 0) WHERE user_id=?",
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

    # -------- КУПИТЬ --------
    if text.startswith("купить"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "❌ Пример: купить 5")

        n = int(parts[1])
        cost = n * 10

        if money < cost:
            return bot.reply_to(
                message,
                f"❌ Нужно {cost} {money_word(cost)}, не хватает {cost - money}"
            )

        add(user.id, "money", -cost)
        add(user.id, "bushes", n)
        return bot.reply_to(
            message,
            f"🛒 Взял {n} кустов\n💶 −{cost} {money_word(cost)}"
        )

    # -------- СОБРАТЬ --------
    if text == "собрать":
        if bushes <= 0:
            return bot.reply_to(message, "❌ У тебя даже кустов нет")

        if not cooldown(u[9], 1):
            return bot.reply_to(message, "⏳ Кусты ещё не выросли")

        gain = random.randint(1, bushes)
        add(user.id, "weed", gain)
        set_time(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрал {gain} грамм")

    # ================= ПРОДАЖИ =================

    def failed_deal(item, lost):
        return (
            f"🚨 Подстава!\n"
            f"👮 Покупатель оказался мутным\n"
            f"❌ Ты скинул {lost} {item} и свалил без денег"
        )

    # -------- ПРОДАТЬ КОНОПЛЮ --------
    if text.startswith("продать ") and text.split()[1].isdigit():
        n = int(text.split()[1])

        if weed < n:
            return bot.reply_to(
                message,
                f"❌ Ты не можешь впарить {n}, не хватает {n - weed}"
            )

        if random.random() < 0.1:
            add(user.id, "weed", -n)
            return bot.reply_to(message, failed_deal("грамм травы", n))

        earn = n * 1
        add(user.id, "weed", -n)
        add(user.id, "money", earn)
        return bot.reply_to(
            message,
            f"🤝 Впарил травку {n} г.\n💶 +{earn} {money_word(earn)}"
        )

    # -------- ПРОДАТЬ КЕКСЫ --------
    if text.startswith("продать кексы"):
        parts = text.split()
        if len(parts) != 3 or not parts[2].isdigit():
            return bot.reply_to(message, "❌ Пример: продать кексы 5")

        n = int(parts[2])
        if cakes < n:
            return bot.reply_to(
                message,
                f"❌ Не хватает {n - cakes} кексов"
            )

        if random.random() < 0.12:
            add(user.id, "cakes", -n)
            return bot.reply_to(message, failed_deal("кексов", n))

        earn = n * 5
        add(user.id, "cakes", -n)
        add(user.id, "money", earn)
        return bot.reply_to(
            message,
            f"🥮 Спихнул {n} кексов\n💶 +{earn} {money_word(earn)}"
        )

    # -------- ПРОДАТЬ КОСЯКИ --------
    if text.startswith("продать косяки"):
        parts = text.split()
        if len(parts) != 3 or not parts[2].isdigit():
            return bot.reply_to(message, "❌ Пример: продать косяки 3")

        n = int(parts[2])
        if joints < n:
            return bot.reply_to(
                message,
                f"❌ Не хватает {n - joints} косяков"
            )

        if random.random() < 0.15:
            add(user.id, "joints", -n)
            return bot.reply_to(message, failed_deal("косяков", n))

        earn = n * 3
        add(user.id, "joints", -n)
        add(user.id, "money", earn)
        return bot.reply_to(
            message,
            f"🚬 Загнал {n} косяков\n💶 +{earn} {money_word(earn)}"
        )

    # -------- ИСПЕЧЬ --------
    if text.startswith("испечь"):
        n = int(text.split()[1])
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        baked = sum(1 for _ in range(n) if random.random() > 0.4)
        burned = n - baked
        add(user.id, "weed", -n)
        add(user.id, "cakes", baked)
        return bot.reply_to(
            message,
            f"🥮 Получилось {baked}\n🔥 Сгорело {burned}"
        )

    # -------- КРАФТ --------
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        made = sum(1 for _ in range(n) if random.random() > 0.2)
        trash = n - made
        add(user.id, "weed", -n)
        add(user.id, "joints", made)
        return bot.reply_to(
            message,
            f"🚬 Скрутил {made}\n💩 Запорол {trash}"
        )

    # -------- ДУНУТЬ --------
    if text == "дунуть":
        if joints <= 0:
            return bot.reply_to(message, "❌ Нет косяков")

        if not cooldown(u[10], 1):
            return bot.reply_to(message, "⏳ Можно раз в час")

        add(user.id, "joints", -1)

        if random.random() < 0.7:
            effect = random.randint(1, 5)
            add(user.id, "high", effect)
            msg = f"😵‍💫 Накрыло\nКайф +{effect}"
        else:
            effect = random.randint(1, 3)
            add(user.id, "high", -effect)
            msg = f"🤢 Подавился дымом\nКайф −{effect}"

        set_time(user.id, "last_smoke")
        return bot.reply_to(message, msg)