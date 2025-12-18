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