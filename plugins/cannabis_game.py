import sqlite3, random
from datetime import datetime, timedelta
from plugins.common import get_name

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
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
    user_id TEXT PRIMARY KEY,
    gopniks_level1 INTEGER DEFAULT 0,
    gopniks_level2 INTEGER DEFAULT 0,
    gopniks_level3 INTEGER DEFAULT 0,
    hp_group1 INTEGER DEFAULT 0,
    hp_group2 INTEGER DEFAULT 0,
    hp_group3 INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS clans (
    clan_id TEXT PRIMARY KEY,
    name TEXT,
    leader TEXT,
    coleaders TEXT,
    officers TEXT,
    bank INTEGER DEFAULT 0,
    bushes INTEGER DEFAULT 0
)
""")
conn.commit()

# ================== HELPERS ==================
def ensure_user(user):
    cursor.execute("INSERT OR IGNORE INTO cannabis(user_id,name) VALUES (?,?)",(str(user.id),get_name(user)))
    cursor.execute("INSERT OR IGNORE INTO army(user_id) VALUES (?)",(str(user.id),))
    conn.commit()

def get_user(user):
    ensure_user(user)
    cursor.execute("SELECT * FROM cannabis WHERE user_id=?",(str(user.id),))
    return cursor.fetchone()

def update_user_field(user, field, value):
    cursor.execute(f"UPDATE cannabis SET {field}=? WHERE user_id=?",(value,str(user.id)))
    conn.commit()

def now():
    return datetime.now()

def can_collect(last_time):
    if not last_time:
        return True
    return now() - datetime.fromisoformat(last_time) > timedelta(hours=1)

def can_eat(last_time):
    if not last_time:
        return True
    return now() - datetime.fromisoformat(last_time) > timedelta(hours=1)

def can_smoke(last_time):
    if not last_time:
        return True
    return now() - datetime.fromisoformat(last_time) > timedelta(hours=1)

# ================== HANDLE ==================
def handle(bot,message):
    text = (message.text or "").lower().strip()
    user = message.from_user
    ensure_user(user)
    u = get_user(user)

    # --- ЭКОНОМИКА ---
    if text == "баланс":
        bot.reply_to(message,
            f"🌿 {get_name(user)}\n"
            f"💰 Коинов: {u[2]}\n"
            f"🌱 Кустов: {u[3]}\n"
            f"🌿 Конопли: {u[4]}\n"
            f"🥮 Кексов: {u[5]}\n"
            f"🚬 Косяков: {u[6]}\n"
            f"❤️ Сытость: {u[7]}\n"
            f"😵 Кайф: {u[8]}"
        )

    elif text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split())>1 else 1
        cost = n*10
        if u[2]<cost:
            return bot.reply_to(message,"❌ Недостаточно коинов")
        update_user_field(user,"coins",u[2]-cost)
        update_user_field(user,"bushes",u[3]+n)
        bot.reply_to(message,f"🌱 Куплено {n} кустов за {cost} коинов")

    elif text == "собрать":
        if not can_collect(u[9]):
            return bot.reply_to(message,"⏳ Рано, подожди 1 час")
        gain = random.randint(0,u[3])
        update_user_field(user,"weed",u[4]+gain)
        update_user_field(user,"last_collect",now().isoformat())
        bot.reply_to(message,f"🌿 Собрано {gain} конопли")

    elif text.startswith("продать кексы"):
        n = int(text.split()[2])
        if u[5]<n:
            return bot.reply_to(message,"❌ Нет кексов")
        earned = n//5
        update_user_field(user,"cakes",u[5]-n)
        update_user_field(user,"coins",u[2]+earned)
        bot.reply_to(message,f"💰 Продал {n} кексов → +{earned} коинов")

    elif text.startswith("продать"):
        n = int(text.split()[1])
        if u[4]<n:
            return bot.reply_to(message,"❌ Нет конопли")
        earned = n//10
        update_user_field(user,"weed",u[4]-n)
        update_user_field(user,"coins",u[2]+earned)
        bot.reply_to(message,f"💰 Продал {n} конопли → +{earned} коинов")

    elif text.startswith("испечь"):
        n = int(text.split()[1])
        if u[4]<n:
            return bot.reply_to(message,"❌ Нет конопли")
        burned = 0
        baked = 0
        for _ in range(n):
            if random.random()<0.3:
                burned+=1
            else:
                baked+=1
        update_user_field(user,"weed",u[4]-n)
        update_user_field(user,"cakes",u[5]+baked)
        bot.reply_to(message,f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

    elif text.startswith("крафт"):
        n = int(text.split()[1])
        if u[4]<n:
            return bot.reply_to(message,"❌ Нет конопли")
        update_user_field(user,"weed",u[4]-n)
        update_user_field(user,"joints",u[6]+n)
        bot.reply_to(message,f"🚬 Скрафтил {n} косяков")

    elif text.startswith("съесть"):
        n = int(text.split()[1])
        if not can_eat(u[10]):
            return bot.reply_to(message,"⏳ Можно есть раз в час")
        if u[5]<n:
            return bot.reply_to(message,"❌ Нет кексов")
        update_user_field(user,"cakes",u[5]-n)
        update_user_field(user,"hunger",u[7]+n)
        update_user_field(user,"last_eat",now().isoformat())
        bot.reply_to(message,f"❤️ Сытость +{n}")

    elif text.startswith("дунуть"):
        n = int(text.split()[1])
        if not can_smoke(u[11]):
            return bot.reply_to(message,"⏳ Можно дунуть раз в час")
        if u[6]<n:
            return bot.reply_to(message,"❌ Нет косяков")
        effect = random.randint(1,5)
        update_user_field(user,"joints",u[6]-n)
        update_user_field(user,"high",u[8]+effect)
        update_user_field(user,"last_smoke",now().isoformat())
        bot.reply_to(message,f"🔥 Ты кайфанул 😵‍💫\nКайф +{effect}")

# ================== КОМАНДЫ АРМИИ, КЛАНОВ, РЕЙДОВ ==================
# Должны быть реализованы аналогично, через elif text.startswith("...")...