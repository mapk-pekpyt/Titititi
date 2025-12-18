import sqlite3, random
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.common import get_name

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

# ================== TABLES ==================
cursor.execute("""
CREATE TABLE IF NOT EXISTS cannabis_players (
    chat_id TEXT,
    user_id TEXT,
    name TEXT,
    coins INTEGER DEFAULT 10,
    bushes INTEGER DEFAULT 0,
    weed INTEGER DEFAULT 0,
    cakes INTEGER DEFAULT 0,
    joints INTEGER DEFAULT 0,
    hunger INTEGER DEFAULT 0,
    high INTEGER DEFAULT 0,
    last_collect TEXT,
    last_high TEXT,
    clan_id INTEGER,
    PRIMARY KEY (chat_id, user_id)
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS soldier_groups (
    chat_id TEXT,
    user_id TEXT,
    group_type TEXT,
    level INTEGER,
    count INTEGER,
    hp INTEGER,
    PRIMARY KEY(chat_id,user_id,group_type)
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS clans (
    clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    leader TEXT,
    bank INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS clan_members (
    clan_id INTEGER,
    user_id TEXT,
    role TEXT,
    PRIMARY KEY(clan_id,user_id)
)
""")
conn.commit()

# ================== HELPERS ==================
def player(chat, user):
    cursor.execute("INSERT OR IGNORE INTO cannabis_players(chat_id,user_id,name) VALUES (?,?,?)",
                   (str(chat), str(user.id), get_name(user)))
    cursor.execute("UPDATE cannabis_players SET name=? WHERE chat_id=? AND user_id=?",
                   (get_name(user), str(chat), str(user.id)))
    conn.commit()
    cursor.execute("SELECT * FROM cannabis_players WHERE chat_id=? AND user_id=?",
                   (str(chat), str(user.id)))
    return cursor.fetchone()

def group_power(g):
    return g[3] * g[4] * g[5] // 100  # пример формулы: level*count*hp/100

def army_power(user_id, p=None):
    if not p:
        cursor.execute("SELECT * FROM cannabis_players WHERE user_id=?", (user_id,))
        p = cursor.fetchone()
    cursor.execute("SELECT * FROM soldier_groups WHERE user_id=?", (user_id,))
    groups = cursor.fetchall()
    return sum(group_power(g) for g in groups)

# ================== ECONOMY ==================
def handle_economy(bot, message):
    chat = message.chat.id
    user = message.from_user
    p = player(chat, user)
    text = (message.text or "").lower().strip()
    now = datetime.now()

    # --- BALANCE ---
    if text=="баланс":
        bot.reply_to(message,
            f"🌿 {p[2]}\n💰 Коины: {p[3]}\n🌱 Кусты: {p[4]}\n🌿 Конопля: {p[5]}\n🥮 Кексы: {p[6]}\n🚬 Косяки: {p[7]}\n❤️ Сытость: {p[8]}\n😵‍💫 Кайф: {p[9]}"
        )
        return

    # --- COLLECT ---
    if text=="собрать":
        if p[10]:
            last = datetime.fromisoformat(p[10])
            if now-last<timedelta(hours=1):
                bot.reply_to(message,"⏳ Рано, подожди")
                return
        gain = random.randint(0,p[4])
        cursor.execute("UPDATE cannabis_players SET weed=weed+?, last_collect=? WHERE chat_id=? AND user_id=?",
                       (gain, now.isoformat(), str(chat), str(user.id)))
        conn.commit()
        bot.reply_to(message,f"🌿 Собрано {gain} конопли")
        return

    # --- BAKE ---
    if text.startswith("испечь"):
        n = int(text.split()[1])
        if p[5]<n:
            bot.reply_to(message,"❌ Нет конопли")
            return
        burned = sum(1 for _ in range(n) if random.random()<0.3)
        baked = n-burned
        cursor.execute("UPDATE cannabis_players SET weed=weed-?, cakes=cakes+? WHERE chat_id=? AND user_id=?",
                       (n,baked,str(chat),str(user.id)))
        conn.commit()
        bot.reply_to(message,f"🥮 Испёк {baked}, 🔥 сгорело {burned}")
        return

    # --- CRAFT JOINT ---
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if p[5]<n:
            bot.reply_to(message,"❌ Нет конопли")
            return
        cursor.execute("UPDATE cannabis_players SET weed=weed-?, joints=joints+? WHERE chat_id=? AND user_id=?",
                       (n,n,str(chat),str(user.id)))
        conn.commit()
        bot.reply_to(message,f"🚬 Скрафтил {n} косяков")
        return

    # --- EAT CAKE ---
    if text.startswith("съесть"):
        n = int(text.split()[1])
        if p[6]<n:
            bot.reply_to(message,"❌ Нет кексов")
            return
        cursor.execute("UPDATE cannabis_players SET cakes=cakes-?, hunger=hunger+? WHERE chat_id=? AND user_id=?",
                       (n,n,str(chat),str(user.id)))
        conn.commit()
        bot.reply_to(message,f"❤️ Сытость +{n}")
        return

# ================== SOLDIERS ==================
def handle_soldiers(bot,message):
    chat = message.chat.id
    user = message.from_user
    text = (message.text or "").lower().strip()
    p = player(chat, user)

    # --- HIRE ---
    if text.startswith("нанять"):
        # нанять случайную группу, ограничение 30 мин
        return

    # --- HEAL GROUP ---
    if text.startswith("лечить "):
        return

    # --- HEAL ALL ---
    if text=="лечить всех":
        return

# ================== RAID ==================
def handle_raid(bot,message):
    chat = message.chat.id
    user = message.from_user
    text = (message.text or "").lower().strip()
    p = player(chat,user)
    # рейд на сообщение или случайный
    return

# ================== CLANS ==================
def handle_clan(bot,message):
    chat = message.chat.id
    user = message.from_user
    text = (message.text or "").lower().strip()
    p = player(chat,user)

    # создать
    if text.startswith("создать клан "):
        return
    # вступить
    if text.startswith("вступить клан "):
        return
    # показать клан
    if text=="клан":
        return
    # роли
    if text.startswith("назначить "):
        return
    # лидер выдает ресурс
    if text.startswith("выдать "):
        return

# ================== WAR ==================
def handle_war(bot,message):
    chat = message.chat.id
    user = message.from_user
    text = (message.text or "").lower().strip()
    p = player(chat,user)
    if text=="кв+":
        return

# ================== MAIN HANDLE ==================
def handle(bot,message):
    if not message.text:
        return
    text = message.text.lower().strip()
    handle_economy(bot,message)
    handle_soldiers(bot,message)
    handle_raid(bot,message)
    handle_clan(bot,message)
    handle_war(bot,message)

# ================== TOP INTERFACE ==================
def load_users_top(chat_id):
    cursor.execute("SELECT * FROM cannabis_players WHERE chat_id=?", (chat_id,))
    return cursor.fetchall()

def handle_top(bot,message):
    chat_id = message.chat.id
    users = load_users_top(chat_id)
    top_list = sorted(users,key=lambda x:x[4],reverse=True)[:10]
    txt = "🏆 Топ Ферм:\n"
    for i,u in enumerate(top_list):
        txt+=f"{i+1}. {u[2]} — {u[4]} 🌱\n"
    bot.send_message(chat_id,txt)