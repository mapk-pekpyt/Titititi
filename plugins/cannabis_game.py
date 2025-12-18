import sqlite3, random, os, threading
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.common import get_name

DB_FILE = "data/data.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# =========================
# =========================
# CREATE TABLES
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    coins INTEGER DEFAULT 100,
    bushes INTEGER DEFAULT 0,
    weed INTEGER DEFAULT 0,
    cakes INTEGER DEFAULT 0,
    joints INTEGER DEFAULT 0,
    hunger INTEGER DEFAULT 0,
    high INTEGER DEFAULT 0,
    last_collect TEXT,
    last_high TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS armies (
    user_id TEXT,
    group_type TEXT,
    level INTEGER,
    count INTEGER,
    hp INTEGER,
    PRIMARY KEY (user_id, group_type)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clans (
    clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    leader TEXT,
    co_leaders TEXT,
    officers TEXT,
    bank INTEGER DEFAULT 0,
    power INTEGER DEFAULT 0
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS clan_planations (
    clan_id INTEGER,
    bushes INTEGER DEFAULT 0
)
""")

conn.commit()

# =========================
# HELPERS
# =========================
def ensure_player(user):
    uid = str(user.id)
    name = get_name(user)
    cursor.execute("INSERT OR IGNORE INTO players(user_id,name) VALUES (?,?)", (uid, name))
    cursor.execute("UPDATE players SET name=? WHERE user_id=?", (name, uid))
    conn.commit()

def get_player(user):
    ensure_player(user)
    cursor.execute("SELECT * FROM players WHERE user_id=?", (str(user.id),))
    return cursor.fetchone()

def update_player(user, **kwargs):
    uid = str(user.id)
    for k, v in kwargs.items():
        cursor.execute(f"UPDATE players SET {k}=? WHERE user_id=?", (v, uid))
    conn.commit()

def add_player_resource(user, key, amount):
    uid = str(user.id)
    cursor.execute(f"UPDATE players SET {key}={key}+? WHERE user_id=?", (amount, uid))
    conn.commit()

def collect_ready(u):
    if not u[9]:
        return True
    last = datetime.fromisoformat(u[9])
    return datetime.now() - last >= timedelta(hours=1)

# =========================
# COMMANDS
# =========================
def command_balance(bot, message):
    user = message.from_user
    u = get_player(user)
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

def command_buy_bush(bot, message):
    user = message.from_user
    args = (message.text or "").split()
    n = int(args[1]) if len(args) > 1 else 1
    cost = n*10
    u = get_player(user)
    if u[2] < cost:
        return bot.reply_to(message, "❌ Не хватает коинов")
    add_player_resource(user,"coins",-cost)
    add_player_resource(user,"bushes",n)
    bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

def command_collect(bot, message):
    user = message.from_user
    u = get_player(user)
    if not collect_ready(u):
        last = datetime.fromisoformat(u[9])
        mins = int((timedelta(hours=1)-(datetime.now()-last)).seconds/60)
        return bot.reply_to(message,f"⏳ Рано, подожди {mins} мин")
    gain = random.randint(0,u[3])
    add_player_resource(user,"weed",gain)
    update_player(user,last_collect=datetime.now().isoformat())
    bot.reply_to(message,f"🌿 Собрано {gain} конопли")

def command_sell(bot, message):
    user = message.from_user
    args = (message.text or "").split()
    if len(args)<3:
        return
    item = args[1]
    n = int(args[2])
    u = get_player(user)
    if item=="конопля":
        if u[4]<n: return bot.reply_to(message,"❌ Нет конопли")
        earned = n//10
        add_player_resource(user,"weed",-n)
        add_player_resource(user,"coins",earned)
        bot.reply_to(message,f"💰 Продал {n} конопли → +{earned} коинов")
    elif item=="кекс":
        if u[5]<n: return bot.reply_to(message,"❌ Нет кексов")
        earned = n//5
        add_player_resource(user,"cakes",-n)
        add_player_resource(user,"coins",earned)
        bot.reply_to(message,f"💰 Продал {n} кексов → +{earned} коинов")
    elif item=="косяк":
        if u[6]<n: return bot.reply_to(message,"❌ Нет косяков")
        earned = n//3
        add_player_resource(user,"joints",-n)
        add_player_resource(user,"coins",earned)
        bot.reply_to(message,f"💰 Продал {n} косяков → +{earned} коинов")

def command_bake(bot, message):
    user = message.from_user
    args = (message.text or "").split()
    n = int(args[1]) if len(args)>1 else 1
    u = get_player(user)
    if u[4]<n: return bot.reply_to(message,"❌ Нет конопли")
    baked = 0
    burned = 0
    for _ in range(n):
        if random.random()<0.3:
            burned+=1
        else:
            baked+=1
    add_player_resource(user,"weed",-n)
    add_player_resource(user,"cakes",baked)
    bot.reply_to(message,f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

def command_craft(bot,message):
    user = message.from_user
    args = (message.text or "").split()
    n=int(args[1]) if len(args)>1 else 1
    u = get_player(user)
    if u[4]<n: return bot.reply_to(message,"❌ Нет конопли")
    add_player_resource(user,"weed",-n)
    add_player_resource(user,"joints",n)
    bot.reply_to(message,f"🚬 Скрафтил {n} косяков")

def command_smoke(bot,message):
    user = message.from_user
    u=get_player(user)
    if u[6]<=0: return bot.reply_to(message,"❌ Нет косяков")
    effect=random.randint(1,5)
    add_player_resource(user,"joints",-1)
    add_player_resource(user,"high",effect)
    bot.reply_to(message,f"🔥 Ты кайфанул 😵‍💫 Кайф +{effect}")

# =========================
# НАЕМНИКИ
# =========================
def command_hire(bot,message):
    user=message.from_user
    cursor.execute("SELECT * FROM armies WHERE user_id=?",(str(user.id),))
    rows=cursor.fetchall()
    txt="💂 Наёмники:\n"
    if not rows:
        txt+="Пока нет групп"
    else:
        for r in rows:
            txt+=f"Группа {r[1]} — уровень {r[2]} — {r[3]} шт — HP {r[4]}\n"
    bot.reply_to(message,txt)

# =========================
# TOP INTEGRATION
# =========================
def get_top():
    cursor.execute("SELECT name,bushes FROM players ORDER BY bushes DESC LIMIT 10")
    return cursor.fetchall()

# =========================
# ARMY TRAINING
# =========================
def train_group(user, group_type, levels):
    cursor.execute("SELECT * FROM armies WHERE user_id=? AND group_type=?",(str(user.id),group_type))
    r=cursor.fetchone()
    if r:
        new_level=min(r[2]+levels,15)
        cursor.execute("UPDATE armies SET level=?,hp=? WHERE user_id=? AND group_type=?",(new_level,r[4],str(user.id),group_type))
    else:
        cursor.execute("INSERT INTO armies(user_id,group_type,level,count,hp) VALUES (?,?,?,?,?)",(str(user.id),group_type,1,1,100))
    conn.commit()

# =========================
# MAIN HANDLE
# =========================
def handle(bot,message):
    text=(message.text or "").lower().strip()
    if text=="баланс":
        command_balance(bot,message)
    elif text.startswith("купить"):
        command_buy_bush(bot,message)
    elif text=="собрать":
        command_collect(bot,message)
    elif text.startswith("продать"):
        command_sell(bot,message)
    elif text.startswith("испечь"):
        command_bake(bot,message)
    elif text.startswith("крафт"):
        command_craft(bot,message)
    elif text=="дунуть":
        command_smoke(bot,message)
    elif text=="наемники":
        command_hire(bot,message)

# =========================
# POLLING THREAD
# =========================
# Пример интеграции с основным ботом:
# from main import bot
# @bot.message_handler(content_types=["text"])
# def all_messages(message):
#     handle(bot,message)

# =====================================================
# ===================== КЛАНЫ =========================
# =====================================================

def ensure_clan(name, leader_id):
    cursor.execute(
        "INSERT INTO clans(name, leader, co_leaders, officers) VALUES (?,?,?,?)",
        (name, leader_id, "", "")
    )
    clan_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO clan_members(clan_id, user_id, role) VALUES (?,?,?)",
        (clan_id, leader_id, "leader")
    )
    cursor.execute(
        "INSERT INTO clan_planations(clan_id, bushes) VALUES (?,0)",
        (clan_id,)
    )
    conn.commit()
    return clan_id


def get_player_clan(user_id):
    cursor.execute(
        """SELECT c.clan_id, c.name, cm.role
           FROM clan_members cm
           JOIN clans c ON c.clan_id = cm.clan_id
           WHERE cm.user_id=?""",
        (user_id,)
    )
    return cursor.fetchone()


def command_clan_create(bot, message):
    user = message.from_user
    name = " ".join(message.text.split()[1:])
    if not name:
        return bot.reply_to(message, "❌ Укажи название клана")
    if get_player_clan(str(user.id)):
        return bot.reply_to(message, "❌ Ты уже в клане")
    try:
        ensure_clan(name, str(user.id))
        bot.reply_to(message, f"🏴 Клан «{name}» создан!")
    except:
        bot.reply_to(message, "❌ Такое имя уже занято")


def command_clan_info(bot, message):
    user = message.from_user
    clan = get_player_clan(str(user.id))
    if not clan:
        return bot.reply_to(message, "❌ Ты не в клане")
    clan_id, name, role = clan
    cursor.execute("SELECT bank, power FROM clans WHERE clan_id=?", (clan_id,))
    bank, power = cursor.fetchone()
    cursor.execute("SELECT bushes FROM clan_planations WHERE clan_id=?", (clan_id,))
    bushes = cursor.fetchone()[0]
    bot.reply_to(
        message,
        f"🏴 Клан: {name}\n"
        f"👑 Твоя роль: {role}\n"
        f"💰 Банк: {bank}\n"
        f"🌱 Клановые кусты: {bushes}\n"
        f"⚔️ Сила клана: {power}"
    )


def command_clan_give(bot, message):
    user = message.from_user
    args = message.text.split()
    if len(args) < 3:
        return
    clan = get_player_clan(str(user.id))
    if not clan:
        return
    clan_id, _, role = clan
    if role != "leader":
        return bot.reply_to(message, "❌ Только лидер может выдавать")
    amount = int(args[1])
    resource = args[2]
    cursor.execute("UPDATE players SET {} = {} + ? WHERE user_id=?".format(resource, resource),
                   (amount, str(user.id)))
    conn.commit()
    bot.reply_to(message, f"🎁 Выдано {amount} {resource}")


# =====================================================
# ===================== РЕЙДЫ =========================
# =====================================================

def command_raid(bot, message):
    user = message.from_user
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        return bot.reply_to(message, "❌ Ответь на сообщение для рейда")
    ensure_player(user)
    ensure_player(target)
    u = get_player(user)
    t = get_player(target)
    atk = u[8] + random.randint(1, 10)
    dfs = t[8] + random.randint(1, 10)
    if atk > dfs:
        stolen = t[3] // 2
        add_player_resource(target, "bushes", -stolen)
        add_player_resource(user, "bushes", stolen)
        bot.reply_to(message, f"⚔️ Победа! Украдено {stolen} кустов")
    else:
        lost = u[3] // 2
        add_player_resource(user, "bushes", -lost)
        bot.reply_to(message, f"💀 Поражение! Потеряно {lost} кустов")


# =====================================================
# ================= КЛАНОВАЯ ВОЙНА ====================
# =====================================================

def clan_war():
    cursor.execute("SELECT clan_id, power FROM clans")
    clans = cursor.fetchall()
    if len(clans) < 2:
        return
    clans.sort(key=lambda x: x[1])
    for i in range(0, len(clans) - 1, 2):
        a, b = clans[i], clans[i + 1]
        winner = a if random.random() < 0.5 else b
        loser = b if winner == a else a

        cursor.execute("SELECT bank FROM clans WHERE clan_id=?", (loser[0],))
        loser_bank = cursor.fetchone()[0]
        loot = int(loser_bank * 0.5)

        cursor.execute("UPDATE clans SET bank = bank - ? WHERE clan_id=?", (loot, loser[0]))
        cursor.execute("UPDATE clans SET bank = bank + ? WHERE clan_id=?", (loot, winner[0]))
        conn.commit()


def clan_war_scheduler():
    while True:
        now = datetime.now()
        if now.weekday() == 6 and now.hour == 19:
            clan_war()
        time.sleep(3600)


threading.Thread(target=clan_war_scheduler, daemon=True).start()


# =====================================================
# ================== РАСШИРЕНИЕ HANDLE ================
# =====================================================

def handle(bot, message):
    text = (message.text or "").lower().strip()

    if text == "баланс":
        command_balance(bot, message)
    elif text.startswith("купить"):
        command_buy_bush(bot, message)
    elif text == "собрать":
        command_collect(bot, message)
    elif text.startswith("продать"):
        command_sell(bot, message)
    elif text.startswith("испечь"):
        command_bake(bot, message)
    elif text.startswith("крафт"):
        command_craft(bot, message)
    elif text == "дунуть":
        command_smoke(bot, message)
    elif text == "наемники":
        command_hire(bot, message)

    # кланы
    elif text.startswith("клан создать"):
        command_clan_create(bot, message)
    elif text == "клан":
        command_clan_info(bot, message)
    elif text.startswith("клан выдать"):
        command_clan_give(bot, message)

    # рейды
    elif text.startswith("рейд"):
        command_raid(bot, message)