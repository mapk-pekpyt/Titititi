import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

# ======================================================
# DATABASE + MIGRATION
# ======================================================
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

def ensure_user(user):
    cursor.execute("SELECT user_id FROM cannabis WHERE user_id=?", (str(user.id),))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO cannabis VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            str(user.id),
            get_name(user),
            1000,  # старт
            0, 0, 0, 0, 0, 0,
            None,
            None
        ))
        conn.commit()
    else:
        cursor.execute(
            "UPDATE cannabis SET name=? WHERE user_id=?",
            (get_name(user), str(user.id))
        )
        conn.commit()

def get_user(user):
    ensure_user(user)
    cursor.execute("SELECT * FROM cannabis WHERE user_id=?", (str(user.id),))
    return cursor.fetchone()

# ======================================================
# MAIN HANDLER
# ======================================================
def handle(bot, message):
    if message.content_type != "text":
        return

    text = message.text.lower().strip()
    user = message.from_user
    now = datetime.now()

    u = get_user(user)

    money   = u[2]
    bushes  = u[3]
    weed    = u[4]
    cakes   = u[5]
    joints  = u[6]
    hunger  = u[7]
    high    = u[8]
    last_collect = u[9]
    last_smoke   = u[10]

    # ==================================================
    # БАЛАНС
    # ==================================================
    if text == "баланс":
        return bot.reply_to(
            message,
            f"🌿 {u[1]}\n\n"
            f"💶 Еврейчики: {money}\n"
            f"🌱 Кусты: {bushes}\n"
            f"🌿 Конопля: {weed}\n"
            f"🥮 Кексы: {cakes}\n"
            f"🚬 Косяки: {joints}\n"
            f"❤️ Сытость: {hunger}\n"
            f"😵‍💫 Кайф: {high}"
        )

    # ==================================================
    # КУПИТЬ КУСТЫ
    # ==================================================
    if text.startswith("купить"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "Пример: купить 5")

        n = int(parts[1])
        price = n * 10

        if money < price:
            return bot.reply_to(message, "❌ Не хватает еврейчиков")

        cursor.execute("""
            UPDATE cannabis
            SET money = money - ?, bushes = bushes + ?
            WHERE user_id=?
        """, (price, n, str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"🌱 Куплено {n} кустов за {price} 💶")

    # ==================================================
    # СОБРАТЬ
    # ==================================================
    if text == "собрать":
        if bushes <= 0:
            return bot.reply_to(message, "❌ Нечего собирать")

        if last_collect:
            last = datetime.fromisoformat(last_collect)
            if now - last < timedelta(minutes=5):
                return bot.reply_to(message, "⏳ Кусты ещё не выросли")

        gain = random.randint(1, bushes)

        cursor.execute("""
            UPDATE cannabis
            SET weed = weed + ?, last_collect = ?
            WHERE user_id=?
        """, (gain, now.isoformat(), str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"🌿 Собрал {gain} конопли")

    # ==================================================
    # ПРОДАТЬ КОНОПЛЮ
    # ==================================================
    if text.startswith("продать ") and not text.startswith("продать кексы"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "Пример: продать 10")

        n = int(parts[1])
        if weed < n:
            return bot.reply_to(message, "❌ Нет столько конопли")

        earn = n * 1

        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, money = money + ?
            WHERE user_id=?
        """, (n, earn, str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"💶 Продал {n} → +{earn}")

    # ==================================================
    # ИСПЕЧЬ КЕКСЫ
    # ==================================================
    if text.startswith("испечь"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "Пример: испечь 5")

        n = int(parts[1])
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        baked = 0
        burned = 0
        for _ in range(n):
            if random.random() < 0.4:
                burned += 1
            else:
                baked += 1

        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, cakes = cakes + ?
            WHERE user_id=?
        """, (n, baked, str(user.id)))
        conn.commit()

        return bot.reply_to(
            message,
            f"🥮 Испёк {baked}\n🔥 Сгорело {burned}"
        )

    # ==================================================
    # ПРОДАТЬ КЕКСЫ
    # ==================================================
    if text.startswith("продать кексы"):
        parts = text.split()
        if len(parts) != 3 or not parts[2].isdigit():
            return bot.reply_to(message, "Пример: продать кексы 5")

        n = int(parts[2])
        if cakes < n:
            return bot.reply_to(message, "❌ Нет кексов")

        earn = n * 5

        cursor.execute("""
            UPDATE cannabis
            SET cakes = cakes - ?, money = money + ?
            WHERE user_id=?
        """, (n, earn, str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"💶 Продал кексы: +{earn}")

    # ==================================================
    # КРАФТ КОСЯКОВ
    # ==================================================
    if text.startswith("крафт"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return bot.reply_to(message, "Пример: крафт 3")

        n = int(parts[1])
        if weed < n:
            return bot.reply_to(message, "❌ Нет конопли")

        good = 0
        fail = 0
        for _ in range(n):
            if random.random() < 0.3:
                fail += 1
            else:
                good += 1

        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, joints = joints + ?
            WHERE user_id=?
        """, (n, good, str(user.id)))
        conn.commit()

        return bot.reply_to(
            message,
            f"🚬 Скрутил {good}\n💩 Запорол {fail}"
        )

    # ==================================================
    # ДУНУТЬ
    # ==================================================
    if text == "дунуть":
        if joints <= 0:
            return bot.reply_to(message, "❌ Нет косяков")

        if last_smoke:
            last = datetime.fromisoformat(last_smoke)
            if now - last < timedelta(minutes=2):
                return bot.reply_to(message, "⏳ Рано ещё")

        effect = random.randint(-5, 5)

        cursor.execute("""
            UPDATE cannabis
            SET joints = joints - 1,
                high = MAX(high + ?, 0),
                last_smoke = ?
            WHERE user_id=?
        """, (effect, now.isoformat(), str(user.id)))
        conn.commit()

        if effect > 0:
            return bot.reply_to(message, f"🔥 Кайф +{effect}")
        elif effect < 0:
            return bot.reply_to(message, f"🤢 Подавился дымом\nКайф {effect}")
        else:
            return bot.reply_to(message, "😐 Ни о чём")