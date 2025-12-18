import sqlite3, random
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.common import get_name

DB_FILE = "data/data.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
conn.row_factory = sqlite3.Row
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
conn.commit()

# ================== HELPERS ==================
def ensure_user(user):
    cursor.execute("INSERT OR IGNORE INTO cannabis(user_id,name) VALUES (?,?)",
                   (str(user.id), get_name(user)))
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
    last_time = u[field]
    if not last_time:
        return True
    return datetime.now() - datetime.fromisoformat(last_time) >= timedelta(hours=hours)

# ================== ECONOMY & CANNABIS ==================
def handle_balance(bot, message):
    u = get_user(message.from_user)
    txt = (
        f"🌿 {u['name']}\n"
        f"💰 Коинов: {u['coins']}\n"
        f"🌱 Кусты: {u['bushes']}\n"
        f"🌿 Конопля: {u['weed']}\n"
        f"🥮 Кексы: {u['cakes']}\n"
        f"🚬 Косяки: {u['joints']}\n"
        f"❤️ Сытость: {u['hunger']}\n"
        f"😵 Кайф: {u['high']}"
    )
    bot.reply_to(message, txt)

def handle_buy(bot, message):
    u = get_user(message.from_user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    cost = n * 10
    if u["coins"] < cost:
        return bot.reply_to(message, "❌ Не хватает коинов")
    update_user(u["user_id"], "coins", -cost)
    update_user(u["user_id"], "bushes", n)
    bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

def handle_collect(bot, message):
    u = get_user(message.from_user)
    last = u["last_collect"]
    if last:
        last_dt = datetime.fromisoformat(last)
        if datetime.now() - last_dt < timedelta(hours=1):
            mins = int((timedelta(hours=1)-(datetime.now()-last_dt)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
    gain = random.randint(0, u["bushes"])
    update_user(u["user_id"], "weed", gain)
    set_user_time(u["user_id"], "last_collect")
    bot.reply_to(message, f"🌿 Собрано {gain} конопли")

def handle_sell(bot, message):
    u = get_user(message.from_user)
    parts = message.text.split()
    if "кексы" in message.text:
        n = int(parts[2])
        if u["cakes"] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        earned = n // 5
        update_user(u["user_id"], "cakes", -n)
        update_user(u["user_id"], "coins", earned)
        bot.reply_to(message, f"💰 Продал {n} кексов → +{earned} коинов")
    elif "косяки" in message.text:
        n = int(parts[1])
        if u["joints"] < n:
            return bot.reply_to(message, "❌ Нет косяков")
        earned = n // 2
        update_user(u["user_id"], "joints", -n)
        update_user(u["user_id"], "coins", earned)
        bot.reply_to(message, f"💰 Продал {n} косяков → +{earned} коинов")
    else:
        n = int(parts[1])
        if u["weed"] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        earned = n // 10
        update_user(u["user_id"], "weed", -n)
        update_user(u["user_id"], "coins", earned)
        bot.reply_to(message, f"💰 Продал {n} конопли → +{earned} коинов")

def handle_bake(bot, message):
    u = get_user(message.from_user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    if u["weed"] < n:
        return bot.reply_to(message, "❌ Нет конопли")
    baked, burned = 0, 0
    for _ in range(n):
        if random.random() < 0.3:
            burned += 1
        else:
            baked += 1
    update_user(u["user_id"], "weed", -n)
    update_user(u["user_id"], "cakes", baked)
    bot.reply_to(message, f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

def handle_craft(bot, message):
    u = get_user(message.from_user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    if u["weed"] < n:
        return bot.reply_to(message, "❌ Нет конопли")
    update_user(u["user_id"], "weed", -n)
    update_user(u["user_id"], "joints", n)
    bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

def handle_eat(bot, message):
    u = get_user(message.from_user)
    last = u["last_eat"]
    if last:
        last_dt = datetime.fromisoformat(last)
        if datetime.now() - last_dt < timedelta(hours=1):
            mins = int((timedelta(hours=1)-(datetime.now()-last_dt)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    if u["cakes"] < n:
        return bot.reply_to(message, "❌ Нет кексов")
    update_user(u["user_id"], "cakes", -n)
    update_user(u["user_id"], "hunger", n)
    set_user_time(u["user_id"], "last_eat")
    bot.reply_to(message, f"❤️ Сытость +{n}")

def handle_smoke(bot, message):
    u = get_user(message.from_user)
    last = u["last_smoke"]
    if last:
        last_dt = datetime.fromisoformat(last)
        if datetime.now() - last_dt < timedelta(hours=1):
            mins = int((timedelta(hours=1)-(datetime.now()-last_dt)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
    if u["joints"] <= 0:
        return bot.reply_to(message, "❌ Нет косяков")
    effect = random.choice([-5,-3,-2,-1,0,1,2,3,4,5])
    update_user(u["user_id"], "joints", -1)
    update_user(u["user_id"], "high", effect)
    set_user_time(u["user_id"], "last_smoke")
    if effect > 0:
        bot.reply_to(message, f"🔥 Ты кайфанул 😵‍💫\nКайф +{effect}")
    elif effect < 0:
        bot.reply_to(message, f"🤢 Ты подавился\nКайф {effect}")
    else:
        bot.reply_to(message, "😐 Ни рыба ни мясо")

# ================== MAIN HANDLE ==================
def handle(bot, message):
    text = (message.text or "").lower()
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
    elif text.startswith("подымить"):
        handle_smoke(bot, message)