import sqlite3, random
from datetime import datetime, timedelta
from plugins.common import get_name

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

def update_field(user_id, field, delta):
    # Не допускаем отрицательных значений
    cursor.execute(f"SELECT {field} FROM cannabis WHERE user_id=?", (str(user_id),))
    current = cursor.fetchone()[0]
    new_value = max(0, current + delta)
    cursor.execute(f"UPDATE cannabis SET {field}=? WHERE user_id=?", (new_value, str(user_id)))
    conn.commit()

def set_timer(user_id, field):
    cursor.execute(f"UPDATE cannabis SET {field}=? WHERE user_id=?", (datetime.now().isoformat(), str(user_id)))
    conn.commit()

def can_use(user, field, hours=1):
    cursor.execute(f"SELECT {field} FROM cannabis WHERE user_id=?", (str(user.id),))
    last = cursor.fetchone()[0]
    if not last:
        return True
    return datetime.now() - datetime.fromisoformat(last) >= timedelta(hours=hours)

# ================== GAME ==================
def handle(bot, message):
    user = message.from_user
    text = (message.text or "").lower().strip()
    name = get_name(user)
    u = get_user(user)

    # Индексы полей:
    # 0:user_id, 1:name, 2:coins, 3:bushes, 4:weed, 5:cakes, 6:joints, 7:hunger, 8:high

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

    # -------- КУПИТЬ КУСТЫ --------
    if text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split()) > 1 else 1
        cost = n * 10
        if u[2] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")
        update_field(user.id, "coins", -cost)
        update_field(user.id, "bushes", n)
        return bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

    # -------- СОБРАТЬ (РАЗ В ЧАС) --------
    if text == "собрать":
        if not can_use(user, "last_collect", hours=1):
            cursor.execute("SELECT last_collect FROM cannabis WHERE user_id=?", (str(user.id),))
            last = cursor.fetchone()[0]
            mins = int((timedelta(hours=1) - (datetime.now() - datetime.fromisoformat(last))).seconds / 60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        if u[3] <= 0:
            return bot.reply_to(message, "❌ У тебя нет кустов")
        gain = random.randint(1, u[3])
        update_field(user.id, "weed", gain)
        set_timer(user.id, "last_collect")
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ КОНПЛЮ --------
    if text.startswith("продать ") and not text.startswith("продать кексы"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        earned = n // 10
        update_field(user.id, "weed", -n)
        update_field(user.id, "coins", earned)
        return bot.reply_to(message, f"💰 Продано {n} конопли → +{earned} коинов")

    # -------- ИСПЕЧЬ --------
    if text.startswith("испечь"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        burned = 0
        baked = 0
        for _ in range(n):
            if random.random() < 0.3:
                burned += 1
            else:
                baked += 1
        update_field(user.id, "weed", -n)
        update_field(user.id, "cakes", baked)
        return bot.reply_to(message, f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

    # -------- СЪЕСТЬ --------
    if text.startswith("съесть"):
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        update_field(user.id, "cakes", -n)
        update_field(user.id, "hunger", n)
        set_timer(user.id, "last_eat")
        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # -------- ПРОДАТЬ КЕКСЫ --------
    if text.startswith("продать кексы"):
        n = int(text.split()[2])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        earned = n // 5
        update_field(user.id, "cakes", -n)
        update_field(user.id, "coins", earned)
        return bot.reply_to(message, f"💰 Продал {n} кексов → +{earned} коинов")

    # -------- КРАФТ КОСЯКОВ --------
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        update_field(user.id, "weed", -n)
        update_field(user.id, "joints", n)
        return bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

    # -------- ПОДЫМИТЬ (РАЗ В ЧАС) --------
    if text == "подымить":
        if u[6] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        if not can_use(user, "last_smoke", hours=1):
            cursor.execute("SELECT last_smoke FROM cannabis WHERE user_id=?", (str(user.id),))
            last = cursor.fetchone()[0]
            mins = int((timedelta(hours=1) - (datetime.now() - datetime.fromisoformat(last))).seconds / 60)
            return bot.reply_to(message, f"⏳ Подожди {mins} мин")
        effect = random.randint(1, 5)
        update_field(user.id, "joints", -1)
        update_field(user.id, "high", effect)
        set_timer(user.id, "last_smoke")
        return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")