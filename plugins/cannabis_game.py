import sqlite3, random
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
    last_eat TEXT,
    last_smoke TEXT
)
""")
conn.commit()

# ================== HELPERS ==================
def ensure_user(user):
    cursor.execute(
        "INSERT OR IGNORE INTO cannabis(user_id,name) VALUES (?,?)",
        (str(user.id), get_name(user))
    )
    cursor.execute(
        "UPDATE cannabis SET name=? WHERE user_id=?",
        (get_name(user), str(user.id))
    )
    conn.commit()

def get_user(user):
    ensure_user(user)
    cursor.execute("SELECT * FROM cannabis WHERE user_id=?", (str(user.id),))
    return cursor.fetchone()

def update_user(user_id, field, delta):
    cursor.execute(f"UPDATE cannabis SET {field} = {field} + ? WHERE user_id=?", (delta, str(user_id)))
    conn.commit()

def set_time(user_id, field):
    cursor.execute(f"UPDATE cannabis SET {field}=? WHERE user_id=?", (datetime.now().isoformat(), str(user_id)))
    conn.commit()

def can_use_timer(last_time_str, hours=1):
    if not last_time_str:
        return True
    last_time = datetime.fromisoformat(last_time_str)
    return datetime.now() - last_time >= timedelta(hours=hours)

# ================== PLUGIN ==================
def handle(bot, message):
    user = message.from_user
    text = (message.text or "").lower().strip()
    u = get_user(user)

    # -------- БАЛАНС --------
    if text == "баланс":
        return bot.reply_to(
            message,
            f"🌿 {get_name(user)}\n\n"
            f"💵 Зелёные: {u[2]}\n"
            f"🌱 Кусты: {u[3]}\n"
            f"🌿 Конопля: {u[4]}\n"
            f"🥮 Кексы: {u[5]}\n"
            f"🚬 Косяки: {u[6]}\n"
            f"❤️ Сытость: {u[7]}\n"
            f"😵‍💫 Кайф: {u[8]}"
        )

    # -------- КУПИТЬ КУСТЫ --------
    if text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split()) > 1 else 1
        cost = n * 10
        if u[2] < cost:
            return bot.reply_to(message, "❌ Не хватает 💵")
        update_user(user.id, "money", -cost)
        update_user(user.id, "bushes", n)
        return bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} 💵")

    # -------- СОБРАТЬ --------
    if text == "собрать":
        if u[3] <= 0:
            return bot.reply_to(message, "❌ У тебя нет кустов")
        gain = random.randint(1, u[3])
        update_user(user.id, "weed", gain)
        set_time(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ --------
    if text.startswith("продать ") and not text.startswith("продать кексы") and not text.startswith("продать косяки"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        earned = n * 1
        update_user(user.id, "weed", -n)
        update_user(user.id, "money", earned)
        return bot.reply_to(message, f"💰 Продано {n} конопли → +{earned} 💵")

    # -------- ПРОДАТЬ КЕКСЫ --------
    if text.startswith("продать кексы"):
        n = int(text.split()[2])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        earned = n * 5
        update_user(user.id, "cakes", -n)
        update_user(user.id, "money", earned)
        return bot.reply_to(message, f"💰 Продано {n} кексов → +{earned} 💵")

    # -------- ПРОДАТЬ КОСЯКИ --------
    if text.startswith("продать косяки"):
        n = int(text.split()[1])
        if u[6] < n:
            return bot.reply_to(message, "❌ Нет косяков")
        earned = n * 3
        update_user(user.id, "joints", -n)
        update_user(user.id, "money", earned)
        return bot.reply_to(message, f"💰 Продано {n} косяков → +{earned} 💵")

    # -------- ИСПЕЧЬ КЕКСЫ --------
    if text.startswith("испечь"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        baked = 0
        burned = 0
        for _ in range(n):
            if random.random() < 0.4:  # 40% шанс сгореть
                burned += 1
            else:
                baked += 1
        update_user(user.id, "weed", -n)
        update_user(user.id, "cakes", baked)
        return bot.reply_to(message, f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

    # -------- КРАФТ КОСЯКОВ --------
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        joints = 0
        broken = 0
        for _ in range(n):
            if random.random() < 0.2:  # 20% шанс сломаться
                broken += 1
            else:
                joints += 1
        update_user(user.id, "weed", -n)
        update_user(user.id, "joints", joints)
        return bot.reply_to(message, f"🚬 Скрафтил {joints}, 💀 сломалось {broken}")

    # -------- СЪЕСТЬ --------
    if text.startswith("съесть"):
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        update_user(user.id, "cakes", -n)
        update_user(user.id, "hunger", n)
        set_time(user.id, "last_eat")
        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # -------- ДУНУТЬ (раз в час) --------
    if text == "дунуть":
        if u[6] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        if not can_use_timer(u[11], 1):
            mins = int((timedelta(hours=1) - (datetime.now() - datetime.fromisoformat(u[11]))).seconds / 60)
            return bot.reply_to(message, f"⏳ Подожди {mins} мин")
        success = random.random() < 0.7  # 70% шанс кайфа
        if success:
            effect = random.randint(1, 5)
            update_user(user.id, "joints", -1)
            update_user(user.id, "high", effect)
            set_time(user.id, "last_smoke")
            return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")
        else:
            effect = random.randint(1, 3)
            update_user(user.id, "joints", -1)
            update_user(user.id, "high", -effect)
            set_time(user.id, "last_smoke")
            return bot.reply_to(message, f"🤢 Подавился! Кайф -{effect}")