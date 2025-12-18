import sqlite3, random
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.common import get_name

DB_FILE = "data/data.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# ================== TABLES ==================
# Пользователи
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

# Армия
cursor.execute("""
CREATE TABLE IF NOT EXISTS army (
    user_id TEXT,
    type TEXT,
    count INTEGER,
    level INTEGER,
    PRIMARY KEY (user_id, type)
)
""")

# Кланы
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
    last_time = getattr(get_user(user), field, None)
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
    u = get_user(user)
    last = u[9]
    now = datetime.now()
    if last:
        last_dt = datetime.fromisoformat(last)
        if now - last_dt < timedelta(hours=1):
            mins = int((timedelta(hours=1)-(now-last_dt)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
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
    u = get_user(user)
    now = datetime.now()
    last = u[10]
    if last:
        last_dt = datetime.fromisoformat(last)
        if now - last_dt < timedelta(hours=1):
            mins = int((timedelta(hours=1)-(now-last_dt)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
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
    u = get_user(user)
    now = datetime.now()
    last = u[11]
    if last:
        last_dt = datetime.fromisoformat(last)
        if now - last_dt < timedelta(hours=1):
            mins = int((timedelta(hours=1)-(now-last_dt)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
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
        # ================== ARMY & MERCENARIES ==================
def handle_hire(bot, message):
    user = message.from_user
    u = get_user(user)
    parts = message.text.split()
    n = int(parts[1]) if len(parts) > 1 else 1
    cost_per_unit = 50
    total_cost = cost_per_unit * n
    if u[2] < total_cost:
        return bot.reply_to(message, f"❌ Не хватает коинов, нужно {total_cost}")
    add_soldiers(user.id, "гопник", n)
    update_user(user.id, "coins", -total_cost)
    bot.reply_to(message, f"🪖 Нанято {n} гопников за {total_cost} коинов")

def handle_heal(bot, message):
    user = message.from_user
    u = get_user(user)
    parts = message.text.split()
    group_name = parts[1] if len(parts) > 1 else "all"
    auto = parts[-1] == "+" if len(parts) > 2 else False
    total_heal_cost = calculate_heal_cost(user.id, group_name)
    if auto:
        if u[5] < total_heal_cost:
            return bot.reply_to(message, "❌ Не хватает кексов")
        heal_group(user.id, group_name)
        update_user(user.id, "cakes", -total_heal_cost)
        bot.reply_to(message, f"❤️ {group_name} вылечена за {total_heal_cost} кексов")
    else:
        bot.reply_to(message, f"❤️ Лечение {group_name} стоит {total_heal_cost} кексов")

def handle_army(bot, message):
    user = message.from_user
    txt = get_army_status(user.id)
    bot.reply_to(message, txt)

# ================== RAID ==================
def handle_raid(bot, message):
    user = message.from_user
    parts = message.text.split()
    target_id = int(parts[1]) if len(parts) > 1 else None
    if not target_id:
        return bot.reply_to(message, "❌ Укажи цель рейда")
    result = perform_raid(user.id, target_id)
    bot.reply_to(message, result)

# ================== CLANS ==================
def handle_create_clan(bot, message):
    user = message.from_user
    parts = message.text.split()
    name = parts[1] if len(parts) > 1 else None
    if not name:
        return bot.reply_to(message, "❌ Укажи имя клана")
    create_clan(user.id, name)
    bot.reply_to(message, f"🏰 Клан '{name}' создан")

def handle_join_clan(bot, message):
    user = message.from_user
    parts = message.text.split()
    clan_name = parts[1] if len(parts) > 1 else None
    if not clan_name:
        return bot.reply_to(message, "❌ Укажи клан")
    join_clan(user.id, clan_name)
    bot.reply_to(message, f"✅ Вы вступили в клан '{clan_name}'")

def handle_clan(bot, message):
    user = message.from_user
    clan_name = get_user_clan(user.id)
    if not clan_name:
        return bot.reply_to(message, "❌ Вы не в клане")
    txt = get_clan_info(clan_name)
    bot.reply_to(message, txt)

def handle_assign(bot, message):
    parts = message.text.split()
    user = message.from_user
    target_id = int(parts[2])
    role = parts[1]
    assign_role(user.id, target_id, role)
    bot.reply_to(message, f"✅ {role} назначен")

def handle_give(bot, message):
    parts = message.text.split()
    user = message.from_user
    resource = parts[2]
    amount = int(parts[1])
    give_resource(user.id, resource, amount)
    bot.reply_to(message, f"💰 {amount} {resource} выдано")

# ================== CLAN WARS ==================
def handle_clan_war(bot, message):
    user = message.from_user
    start = start_clan_war(user.id)
    bot.reply_to(message, start)

