import sqlite3, time, random
from plugins.common import get_name

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

# =========================
# TABLES
# =========================
cur.executescript("""
CREATE TABLE IF NOT EXISTS mercs(
 chat_id TEXT,
 user_id TEXT,
 hp INTEGER,
 attack INTEGER,
 defense INTEGER,
 level INTEGER
);

CREATE TABLE IF NOT EXISTS cana_timers(
 chat_id TEXT,
 user_id TEXT,
 action TEXT,
 last_time INTEGER,
 PRIMARY KEY(chat_id, user_id, action)
);
""")
conn.commit()

# =========================
# UTILS
# =========================
def ensure(chat, user):
    cur.execute(
        "INSERT OR IGNORE INTO users(chat_id,user_id,name) VALUES (?,?,?)",
        (chat, user.id, get_name(user))
    )
    conn.commit()

def cooldown(chat, user, action, seconds):
    now = int(time.time())
    cur.execute(
        "SELECT last_time FROM cana_timers WHERE chat_id=? AND user_id=? AND action=?",
        (chat, user.id, action)
    )
    row = cur.fetchone()
    if row and now - row[0] < seconds:
        return seconds - (now - row[0])
    cur.execute(
        "REPLACE INTO cana_timers VALUES (?,?,?,?)",
        (chat, user.id, action, now)
    )
    conn.commit()
    return 0

# =========================
# GAME LOGIC
# =========================
def collect(bot, m):
    chat = str(m.chat.id)
    user = m.from_user
    ensure(chat, user)

    cd = cooldown(chat, user, "collect", 3600)
    if cd:
        return bot.reply_to(m, f"⏳ Сбор через {cd//60} мин")

    gain = random.randint(1, 5)
    cur.execute(
        "UPDATE users SET bushes=bushes+?, high=high+1 WHERE chat_id=? AND user_id=?",
        (gain, chat, user.id)
    )
    conn.commit()
    bot.reply_to(m, f"🌱 Ты собрал {gain} кустов\n😵 Кайф +1")

def smoke(bot, m):
    chat = str(m.chat.id)
    user = m.from_user
    ensure(chat, user)

    cur.execute("SELECT joints FROM users WHERE chat_id=? AND user_id=?", (chat, user.id))
    if (cur.fetchone()[0] or 0) <= 0:
        return bot.reply_to(m, "🚬 Косяков нет")

    cur.execute("""
    UPDATE users SET joints=joints-1, high=high+3, full=full-2
    WHERE chat_id=? AND user_id=?
    """, (chat, user.id))
    conn.commit()
    bot.reply_to(m, "🚬 Ты покурил\n😵 Кайф +3")

def hire(bot, m):
    chat = str(m.chat.id)
    user = m.from_user
    ensure(chat, user)

    cd = cooldown(chat, user, "hire", 1800)
    if cd:
        return bot.reply_to(m, f"⏳ Найм через {cd//60} мин")

    cur.execute("SELECT coins FROM users WHERE chat_id=? AND user_id=?", (chat, user.id))
    if (cur.fetchone()[0] or 0) < 50:
        return bot.reply_to(m, "💰 Нужно 50 коинов")

    cur.execute("UPDATE users SET coins=coins-50 WHERE chat_id=? AND user_id=?", (chat, user.id))
    cur.execute("INSERT INTO mercs VALUES (?,?,?,?,?,?)", (chat, user.id, 10, 2, 2, 1))
    conn.commit()
    bot.reply_to(m, "🧑‍🚀 Наёмник нанят")

# =========================
# HANDLER
# =========================
def handle(bot, m):
    t = (m.text or "").lower()
    if t in ("собрать", "сбор"):
        collect(bot, m)
    elif t in ("курить", "косяк"):
        smoke(bot, m)
    elif t in ("нанять", "наем"):
        hire(bot, m)