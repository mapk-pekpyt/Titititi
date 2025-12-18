import sqlite3, random
from datetime import datetime, timedelta
from plugins.common import get_name
from plugins import top_plugin

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

# ================== TABLE ==================
cursor.execute("""
CREATE TABLE IF NOT EXISTS cannabis (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    coins INTEGER DEFAULT 1000,
    bushes INTEGER DEFAULT 0,
    weed INTEGER DEFAULT 0,
    cakes INTEGER DEFAULT 0,
    joints INTEGER DEFAULT 0,
    hunger INTEGER DEFAULT 0,
    high INTEGER DEFAULT 0,
    last_collect TEXT,
    last_eat TEXT,
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
    cursor.execute(
        "SELECT * FROM cannabis WHERE user_id=?",
        (str(user.id),)
    )
    return cursor.fetchone()

def set_time(user_id, field):
    cursor.execute(f"UPDATE cannabis SET {field}=? WHERE user_id=?", (datetime.now().isoformat(), str(user_id)))
    conn.commit()

def cooldown(last_time, hours=1):
    if not last_time:
        return True
    return datetime.now() - datetime.fromisoformat(last_time) >= timedelta(hours=hours)

# ================== GAME ==================
def handle(bot, message):
    user = message.from_user
    name = get_name(user)
    text = (message.text or "").lower().strip()
    u = get(user)

    # -------- БАЛАНС --------
    if text == "баланс":
        return bot.reply_to(
            message,
            f"🌿 {name}\n\n"
            f"💰 Коины: {u[2]}\n"
            f"🌱 Кусты: {u[3]}\n"
            f"🌿 Конопля: {u[4]}\n"
            f"🥮 Кексы: {u[5]}\n"
            f"🚬 Косяки: {u[6]}\n"
            f"❤️ Сытость: {u[7]}\n"
            f"😵‍💫 Кайф: {u[8]}"
        )

    # -------- КУПИТЬ --------
    if text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split()) > 1 else 1
        cost = n * 10
        if u[2] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")
        cursor.execute(
            "UPDATE cannabis SET coins=coins-?, bushes=bushes+? WHERE user_id=?",
            (cost, n, str(user.id))
        )
        conn.commit()
        top_plugin.update_stat("global", user, "bushes", n)
        return bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

    # -------- СОБРАТЬ (раз в час) --------
    if text == "собрать":
        if not cooldown(u[9]):
            mins = int((timedelta(hours=1)-(datetime.now()-datetime.fromisoformat(u[9]))).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        if u[3] <= 0:
            return bot.reply_to(message, "❌ У тебя нет кустов")
        gain = random.randint(1, u[3])
        cursor.execute(
            "UPDATE cannabis SET weed=weed+? WHERE user_id=?",
            (gain, str(user.id))
        )
        conn.commit()
        set_time(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ --------
    if text.startswith("продать ") and not text.startswith("продать кексы"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        earned = n // 10
        cursor.execute(
            "UPDATE cannabis SET weed=weed-?, coins=coins+? WHERE user_id=?",
            (n, earned, str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"💰 Продал {n} → +{earned} коинов")

    # -------- ИСПЕЧЬ --------
    if text.startswith("испечь"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        baked, burned = 0, 0
        for _ in range(n):
            if random.random() < 0.3:
                burned += 1
            else:
                baked += 1
        cursor.execute(
            "UPDATE cannabis SET weed=weed-?, cakes=cakes+? WHERE user_id=?",
            (n, baked, str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

    # -------- СЪЕСТЬ (раз в час) --------
    if text.startswith("съесть"):
        if not cooldown(u[10]):
            mins = int((timedelta(hours=1)-(datetime.now()-datetime.fromisoformat(u[10]))).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        cursor.execute(
            "UPDATE cannabis SET cakes=cakes-?, hunger=hunger+? WHERE user_id=?",
            (n, n, str(user.id))
        )
        conn.commit()
        set_time(user.id, "last_eat")
        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # -------- ПРОДАТЬ КЕКСЫ --------
    if text.startswith("продать кексы"):
        n = int(text.split()[2])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        earned = n // 5
        cursor.execute(
            "UPDATE cannabis SET cakes=cakes-?, coins=coins+? WHERE user_id=?",
            (n, earned, str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"💰 Продал {n} кексов → +{earned} коинов")

    # -------- КРАФТ --------
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        cursor.execute(
            "UPDATE cannabis SET weed=weed-?, joints=joints+? WHERE user_id=?",
            (n, n, str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

    # -------- ПОДЫМИТЬ (раз в час) --------
    if text == "дунуть":
        if u[6] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        if not cooldown(u[11]):
            mins = int((timedelta(hours=1)-(datetime.now()-datetime.fromisoformat(u[11]))).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        effect = random.randint(1,5)
        cursor.execute(
            "UPDATE cannabis SET joints=joints-1, high=high+? WHERE user_id=?",
            (effect, str(user.id))
        )
        conn.commit()
        set_time(user.id, "last_smoke")
        return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")