import sqlite3, random
from datetime import datetime, timedelta
from plugins.common import get_name

DB_FILE = "data/data.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# ================== USERS ==================
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
    last_time = u[9] if field == "last_collect" else u[10] if field == "last_eat" else u[11]
    if not last_time:
        return True
    now = datetime.now()
    last = datetime.fromisoformat(last_time)
    return now - last >= timedelta(hours=hours)

# ================== COMMANDS ==================
def handle(bot, message):
    user = message.from_user
    text = message.text.lower()

    if text.startswith("баланс"):
        handle_balance(bot, message)
    elif text.startswith("купить"):
        handle_buy(bot, message)
    elif text.startswith("собрать"):
        handle_collect(bot, message)
    elif text.startswith("продать"):
        handle_sell(bot, message)
    elif text.startswith("испечь"):
        handle_bake(bot, message)
    elif text.startswith("крафт"):
        handle_craft(bot, message)
    elif text.startswith("съесть"):
        handle_eat(bot, message)
    elif text.startswith("дунуть") or text.startswith("подымить"):
        handle_smoke(bot, message)

# ================== ECONOMY ==================
def handle_balance(bot, message):
    u = get_user(message.from_user)
    txt = (
        f"🌿 {u[1]}\n"
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
    u = get_user(message.from_user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    cost = n * 10
    if u[2] < cost:
        return bot.reply_to(message, "❌ Не хватает коинов")
    update_user(u[0], "coins", -cost)
    update_user(u[0], "bushes", n)
    bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

def handle_collect(bot, message):
    user = message.from_user
    u = get_user(user)
    if not can_use_timer(user, "last_collect"):
        return bot.reply_to(message, "⏳ Собирай раз в час!")
    gain = random.randint(0, u[3])
    update_user(u[0], "weed", gain)
    set_user_time(u[0], "last_collect")
    bot.reply_to(message, f"🌿 Собрано {gain} конопли")

def handle_sell(bot, message):
    user = message.from_user
    u = get_user(user)
    parts = message.text.split()
    if "кексы" in text:
        n = int(parts[2])
        if u[5] < n: return bot.reply_to(message, "❌ Нет кексов")
        earned = n // 5
        update_user(u[0], "cakes", -n)
        update_user(u[0], "coins", earned)
        bot.reply_to(message, f"💰 Продал {n} кексов → +{earned} коинов")
    elif "косяки" in text:
        n = int(parts[1])
        if u[6] < n: return bot.reply_to(message, "❌ Нет косяков")
        earned = n // 2
        update_user(u[0], "joints", -n)
        update_user(u[0], "coins", earned)
        bot.reply_to(message, f"💰 Продал {n} косяков → +{earned} коинов")
    else:  # Конопля
        n = int(parts[1])
        if u[4] < n: return bot.reply_to(message, "❌ Нет конопли")
        earned = n // 10
        update_user(u[0], "weed", -n)
        update_user(u[0], "coins", earned)
        bot.reply_to(message, f"💰 Продал {n} конопли → +{earned} коинов")

def handle_bake(bot, message):
    u = get_user(message.from_user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    if u[4] < n: return bot.reply_to(message, "❌ Нет конопли")
    burned, baked = 0, 0
    for _ in range(n):
        if random.random() < 0.3: burned += 1
        else: baked += 1
    update_user(u[0], "weed", -n)
    update_user(u[0], "cakes", baked)
    bot.reply_to(message, f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

def handle_craft(bot, message):
    u = get_user(message.from_user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    if u[4] < n: return bot.reply_to(message, "❌ Нет конопли")
    update_user(u[0], "weed", -n)
    update_user(u[0], "joints", n)
    bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

def handle_eat(bot, message):
    user = message.from_user
    u = get_user(user)
    if not can_use_timer(user, "last_eat"): return bot.reply_to(message, "⏳ Можно есть раз в час")
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    if u[5] < n: return bot.reply_to(message, "❌ Нет кексов")
    update_user(u[0], "cakes", -n)
    update_user(u[0], "hunger", n)
    set_user_time(u[0], "last_eat")
    bot.reply_to(message, f"❤️ Сытость +{n}")

def handle_smoke(bot, message):
    user = message.from_user
    u = get_user(user)
    if not can_use_timer(user, "last_smoke"): return bot.reply_to(message, "⏳ Можно дунуть раз в час")
    if u[6] <= 0: return bot.reply_to(message, "❌ Нет косяков")
    effect = random.randint(-3,5)
    update_user(u[0], "joints", -1)
    update_user(u[0], "high", effect)
    set_user_time(u[0], "last_smoke")
    if effect > 0: bot.reply_to(message, f"🔥 Ты кайфанул +{effect}")
    elif effect < 0: bot.reply_to(message, f"🤢 Подавился -{abs(effect)}")
    else: bot.reply_to(message, "😐 Ничего не произошло")