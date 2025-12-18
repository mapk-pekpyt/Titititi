import sqlite3, random
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.common import get_name

DB_FILE = "data/data.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# ================== TABLES ==================
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS army (
    user_id TEXT,
    type TEXT,
    count INTEGER,
    level INTEGER,
    PRIMARY KEY (user_id, type)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clans (
    clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    leader_id TEXT,
    co_leaders TEXT,
    officers TEXT,
    bank INTEGER DEFAULT 0,
    total_bushes INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clan_members (
    clan_id INTEGER,
    user_id TEXT,
    role TEXT,
    PRIMARY KEY (clan_id, user_id)
)
""")
conn.commit()

# ================== HELPERS ==================
def ensure_user(user):
    cursor.execute("INSERT OR IGNORE INTO cannabis(user_id,name) VALUES (?,?)",
                   (str(user.id), get_name(user)))
    cursor.execute("UPDATE cannabis SET name=? WHERE user_id=?", (get_name(user), str(user.id)))
    conn.commit()

def get_user(user):
    ensure_user(user)
    cursor.execute("SELECT * FROM cannabis WHERE user_id=?", (str(user.id),))
    return cursor.fetchone()

def update_user(user_id, field, delta):
    cursor.execute(f"UPDATE cannabis SET {field}={field}+? WHERE user_id=?", (delta, str(user_id)))
    conn.commit()

def set_user_time(user_id, field):
    cursor.execute(f"UPDATE cannabis SET {field}=? WHERE user_id=?", (datetime.now().isoformat(), str(user_id)))
    conn.commit()

def can_use_timer(user, field, hours=1):
    u = get_user(user)
    field_idx = {"last_collect":9, "last_eat":10, "last_smoke":11}[field]
    last_time = u[field_idx]
    if not last_time:
        return True
    now = datetime.now()
    last = datetime.fromisoformat(last_time)
    return now - last >= timedelta(hours=hours)

# ================== ECONOMY & CANNABIS ==================
def handle_balance(bot, message):
    user = message.from_user
    u = get_user(user)
    txt = (
        f"🌿 {u[1]}\n\n"
        f"💰 Коинов: {u[2]}\n"
        f"🌱 Кусты: {u[3]}\n"
        f"🌿 Конопля: {u[4]}\n"
        f"🥮 Кексы: {u[5]}\n"
        f"🚬 Косяки: {u[6]}\n"
        f"❤️ Сытость: {u[7]}\n"
        f"😵 Кайф: {u[8]}"
    )
    bot.reply_to(message, txt)

def handle_buy(bot, message):
    user = message.from_user
    u = get_user(user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    cost = n * 10
    if u[2] < cost:
        return bot.reply_to(message, "❌ Не хватает коинов")
    update_user(user.id, "coins", -cost)
    update_user(user.id, "bushes", n)
    bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

def handle_collect(bot, message):
    user = message.from_user
    if not can_use_timer(user, "last_collect"):
        u = get_user(user)
        last = datetime.fromisoformat(u[9])
        mins = int((timedelta(hours=1)-(datetime.now()-last)).seconds/60)
        return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
    u = get_user(user)
    gain = random.randint(0, u[3])
    update_user(user.id, "weed", gain)
    set_user_time(user.id, "last_collect")
    bot.reply_to(message, f"🌿 Собрано {gain} конопли")

def handle_sell(bot, message):
    user = message.from_user
    u = get_user(user)
    parts = message.text.split()
    if "кексы" in message.text:
        n = int(parts[2])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        earned = n // 5
        update_user(user.id, "cakes", -n)
        update_user(user.id, "coins", earned)
        bot.reply_to(message, f"💰 Продал {n} кексов → +{earned} коинов")
    elif "косяки" in message.text:
        n = int(parts[1])
        if u[6] < n:
            return bot.reply_to(message, "❌ Нет косяков")
        earned = n // 2
        update_user(user.id, "joints", -n)
        update_user(user.id, "coins", earned)
        bot.reply_to(message, f"💰 Продал {n} косяков → +{earned} коинов")
    else:
        n = int(parts[1])
        if u[4] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        earned = n // 10
        update_user(user.id, "weed", -n)
        update_user(user.id, "coins", earned)
        bot.reply_to(message, f"💰 Продал {n} конопли → +{earned} коинов")

def handle_bake(bot, message):
    user = message.from_user
    u = get_user(user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    if u[4] < n:
        return bot.reply_to(message, "❌ Нет конопли")
    burned = 0
    baked = 0
    for _ in range(n):
        if random.random() < 0.3:
            burned += 1
        else:
            baked += 1
    update_user(user.id, "weed", -n)
    update_user(user.id, "cakes", baked)
    bot.reply_to(message, f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

def handle_craft(bot, message):
    user = message.from_user
    u = get_user(user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    if u[4] < n:
        return bot.reply_to(message, "❌ Нет конопли")
    update_user(user.id, "weed", -n)
    update_user(user.id, "joints", n)
    bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

def handle_eat(bot, message):
    user = message.from_user
    if not can_use_timer(user, "last_eat"):
        u = get_user(user)
        last = datetime.fromisoformat(u[10])
        mins = int((timedelta(hours=1)-(datetime.now()-last)).seconds/60)
        return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
    u = get_user(user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    if u[5] < n:
        return bot.reply_to(message, "❌ Нет кексов")
    update_user(user.id, "cakes", -n)
    update_user(user.id, "hunger", n)
    set_user_time(user.id, "last_eat")
    bot.reply_to(message, f"❤️ Сытость +{n}")

def handle_smoke(bot, message):
    user = message.from_user
    if not can_use_timer(user, "last_smoke"):
        u = get_user(user)
        last = datetime.fromisoformat(u[11])
        mins = int((timedelta(hours=1)-(datetime.now()-last)).seconds/60)
        return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
    u = get_user(user)
    if u[6] <= 0:
        return bot.reply_to(message, "❌ Нет косяков")
    effect = random.choice([-5,-3,-2,-1,0,1,2,3,4,5])
    update_user(user.id, "joints", -1)
    update_user(user.id, "high", effect)
    set_user_time(user.id, "last_smoke")
    if effect > 0:
        bot.reply_to(message, f"🔥 Ты кайфанул 😵‍💫\nКайф +{effect}")
    elif effect < 0:
        bot.reply_to(message, f"🤢 Ты подавился\nКайф {effect}")
    else:
        bot.reply_to(message, "😐 Ни рыба ни мясо")