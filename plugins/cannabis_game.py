import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name

DB_FILE = "data/data.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# =====================================================
# ТАБЛИЦЫ
# =====================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    coins INTEGER DEFAULT 1000,
    bushes INTEGER DEFAULT 0,
    weed INTEGER DEFAULT 0,
    cakes INTEGER DEFAULT 0,
    joints INTEGER DEFAULT 0,
    hunger INTEGER DEFAULT 10,
    high INTEGER DEFAULT 0,
    last_collect TEXT,
    last_eat TEXT,
    last_smoke TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS merc_groups (
    user_id TEXT,
    type TEXT,
    level INTEGER,
    count INTEGER,
    hp INTEGER,
    PRIMARY KEY (user_id, type, level)
)
""")

conn.commit()

# =====================================================
# ХЕЛПЕРЫ
# =====================================================

def now():
    return datetime.utcnow()

def ensure_player(user):
    cursor.execute(
        "INSERT OR IGNORE INTO players(user_id, name) VALUES (?,?)",
        (str(user.id), get_name(user))
    )
    cursor.execute(
        "UPDATE players SET name=? WHERE user_id=?",
        (get_name(user), str(user.id))
    )
    conn.commit()

def get_player(user):
    ensure_player(user)
    cursor.execute("SELECT * FROM players WHERE user_id=?", (str(user.id),))
    return cursor.fetchone()

def can_do(last_time, minutes=60):
    if not last_time:
        return True
    return now() - datetime.fromisoformat(last_time) >= timedelta(minutes=minutes)

def set_time(user_id, field):
    cursor.execute(
        f"UPDATE players SET {field}=? WHERE user_id=?",
        (now().isoformat(), user_id)
    )
    conn.commit()

# =====================================================
# ЭКОНОМИКА
# =====================================================

BUSH_PRICE = 10          # коинов
WEED_SELL = 10           # 10 травы = 1 коин
CAKE_SELL = 5            # 5 кексов = 1 коин
JOINT_SELL = 2           # 1 косяк = 2 коина

# =====================================================
# ОСНОВНОЙ HANDLE
# =====================================================

def handle(bot, message):
    if not message.text:
        return

    text = message.text.lower().strip()
    user = message.from_user
    ensure_player(user)
    p = get_player(user)

    # -------------------------------------------------
    # БАЛАНС
    # -------------------------------------------------
    if text == "баланс":
        return bot.reply_to(
            message,
            f"🌿 {p[1]}\n\n"
            f"💰 Коины: {p[2]}\n"
            f"🌱 Кусты: {p[3]}\n"
            f"🌿 Трава: {p[4]}\n"
            f"🥮 Кексы: {p[5]}\n"
            f"🚬 Косяки: {p[6]}\n"
            f"❤️ Сытость: {p[7]}\n"
            f"😵 Кайф: {p[8]}"
        )

    # -------------------------------------------------
    # КУПИТЬ КУСТЫ
    # -------------------------------------------------
    if text.startswith("купить куст"):
        try:
            n = int(text.split()[-1])
        except:
            n = 1

        cost = n * BUSH_PRICE
        if p[2] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")

        cursor.execute(
            "UPDATE players SET coins=coins-?, bushes=bushes+? WHERE user_id=?",
            (cost, n, str(user.id))
        )
        conn.commit()
        return bot.reply_to(
            message,
            f"🌱 Куплено кустов: {n}\n💸 Потрачено: {cost}"
        )

    # -------------------------------------------------
    # СБОР УРОЖАЯ (1 РАЗ В ЧАС)
    # -------------------------------------------------
    if text == "собрать":
        if not can_do(p[9], 60):
            return bot.reply_to(message, "⏳ Урожай ещё не вырос")

        if p[3] <= 0:
            return bot.reply_to(message, "❌ У тебя нет кустов")

        gain = random.randint(p[3], p[3] * 3)
        cursor.execute(
            "UPDATE players SET weed=weed+? WHERE user_id=?",
            (gain, str(user.id))
        )
        set_time(str(user.id), "last_collect")

        return bot.reply_to(
            message,
            f"🌿 Ты собрал {gain} травы"
        )

    # -------------------------------------------------
    # ПРОДАТЬ
    # -------------------------------------------------
    if text.startswith("продать траву"):
        try:
            n = int(text.split()[-1])
        except:
            return bot.reply_to(message, "❌ Укажи количество")

        if p[4] < n:
            return bot.reply_to(message, "❌ Недостаточно травы")

        coins = n // WEED_SELL
        cursor.execute(
            "UPDATE players SET weed=weed-?, coins=coins+? WHERE user_id=?",
            (n, coins, str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"💰 +{coins} коинов")

    if text.startswith("продать кексы"):
        n = int(text.split()[-1])
        if p[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        coins = n // CAKE_SELL
        cursor.execute(
            "UPDATE players SET cakes=cakes-?, coins=coins+? WHERE user_id=?",
            (n, coins, str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"💰 +{coins} коинов")

    if text.startswith("продать косяки"):
        n = int(text.split()[-1])
        if p[6] < n:
            return bot.reply_to(message, "❌ Нет косяков")
        coins = n * JOINT_SELL
        cursor.execute(
            "UPDATE players SET joints=joints-?, coins=coins+? WHERE user_id=?",
            (n, coins, str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"💰 +{coins} коинов")

    # -------------------------------------------------
    # СЪЕСТЬ КЕКС (1 РАЗ В ЧАС)
    # -------------------------------------------------
    if text.startswith("съесть"):
        if not can_do(p[10], 60):
            return bot.reply_to(message, "⏳ Желудок ещё занят")

        try:
            n = int(text.split()[-1])
        except:
            n = 1

        if p[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")

        cursor.execute(
            "UPDATE players SET cakes=cakes-?, hunger=hunger+? WHERE user_id=?",
            (n, n, str(user.id))
        )
        set_time(str(user.id), "last_eat")
        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # -------------------------------------------------
    # ДУНУТЬ (1 РАЗ В ЧАС)
    # -------------------------------------------------
    if text == "дунуть":
        if not can_do(p[11], 60):
            return bot.reply_to(message, "⏳ Лёгкие ещё не отошли")

        if p[6] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")

        effect = random.randint(1, 5)
        cursor.execute(
            "UPDATE players SET joints=joints-1, high=high+? WHERE user_id=?",
            (effect, str(user.id))
        )
        set_time(str(user.id), "last_smoke")
        return bot.reply_to(
            message,
            f"😵‍💫 Ты дунул\nКайф +{effect}"
        )