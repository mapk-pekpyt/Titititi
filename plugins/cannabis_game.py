# plugins/cannabis_game.py
import sqlite3, random
from datetime import datetime, timedelta
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

def update_user(user_id, **fields):
    set_expr = ", ".join([f"{k}={k}+?" for k in fields])
    values = list(fields.values())
    values.append(str(user_id))
    cursor.execute(f"UPDATE cannabis SET {set_expr} WHERE user_id=?", values)
    conn.commit()

def set_user_time(user_id, field):
    cursor.execute(f"UPDATE cannabis SET {field}=? WHERE user_id=?", (datetime.now().isoformat(), str(user_id)))
    conn.commit()

def can_use_timer(user, field, hours=1):
    cursor.execute(f"SELECT {field} FROM cannabis WHERE user_id=?", (str(user.id),))
    row = cursor.fetchone()
    if not row or not row[0]:
        return True
    last_time = datetime.fromisoformat(row[0])
    return datetime.now() - last_time >= timedelta(hours=hours)

# ================== COMMANDS ==================
def handle(bot, message):
    text = (message.text or "").lower()
    user = message.from_user

    if text.startswith("баланс"):
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
        return

    # ---------- Купить кусты ----------
    if text.startswith("купить"):
        parts = text.split()
        n = int(parts[1]) if len(parts) > 1 else 1
        u = get_user(user)
        cost = n*10
        if u[2] < cost:
            return bot.reply_to(message, f"❌ Не хватает коинов ({cost} нужно)")
        update_user(user.id, coins=-cost, bushes=n)
        bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")
        return

    # ---------- Собрать ----------
    if text.startswith("собрать"):
        if not can_use_timer(user, "last_collect", 1):
            cursor.execute("SELECT last_collect FROM cannabis WHERE user_id=?", (str(user.id),))
            last = datetime.fromisoformat(cursor.fetchone()[0])
            mins = int((timedelta(hours=1)-(datetime.now()-last)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        u = get_user(user)
        gain = random.randint(0, u[3])
        update_user(user.id, weed=gain)
        set_user_time(user.id, "last_collect")
        bot.reply_to(message, f"🌿 Собрано {gain} конопли")
        return

    # ---------- Продать ----------
    if text.startswith("продать"):
        u = get_user(user)
        parts = text.split()
        if "кексы" in text:
            n = int(parts[2])
            if u[5]<n: return bot.reply_to(message, "❌ Нет кексов")
            earned = n//5
            update_user(user.id, cakes=-n, coins=earned)
            bot.reply_to(message, f"💰 Продал {n} кексов → +{earned} коинов")
        elif "косяки" in text:
            n = int(parts[1])
            if u[6]<n: return bot.reply_to(message, "❌ Нет косяков")
            earned = n//2
            update_user(user.id, joints=-n, coins=earned)
            bot.reply_to(message, f"💰 Продал {n} косяков → +{earned} коинов")
        else:
            n = int(parts[1])
            if u[4]<n: return bot.reply_to(message, "❌ Нет конопли")
            earned = n//10
            update_user(user.id, weed=-n, coins=earned)
            bot.reply_to(message, f"💰 Продал {n} конопли → +{earned} коинов")
        return

    # ---------- Испечь ----------
    if text.startswith("испечь"):
        u = get_user(user)
        parts = text.split()
        n = int(parts[1]) if len(parts)>1 else 1
        if u[4]<n: return bot.reply_to(message, "❌ Нет конопли")
        burned = 0; baked = 0
        for _ in range(n):
            if random.random()<0.3: burned+=1
            else: baked+=1
        update_user(user.id, weed=-n, cakes=baked)
        bot.reply_to(message, f"🥮 Испёк {baked}, 🔥 сгорело {burned}")
        return

    # ---------- Крафт ----------
    if text.startswith("крафт"):
        u = get_user(user)
        parts = text.split()
        n = int(parts[1]) if len(parts)>1 else 1
        if u[4]<n: return bot.reply_to(message, "❌ Нет конопли")
        update_user(user.id, weed=-n, joints=n)
        bot.reply_to(message, f"🚬 Скрафтил {n} косяков")
        return

    # ---------- Съесть ----------
    if text.startswith("съесть"):
        if not can_use_timer(user,"last_eat",1):
            cursor.execute("SELECT last_eat FROM cannabis WHERE user_id=?", (str(user.id),))
            last = datetime.fromisoformat(cursor.fetchone()[0])
            mins = int((timedelta(hours=1)-(datetime.now()-last)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        u = get_user(user)
        parts = text.split()
        n = int(parts[1]) if len(parts)>1 else 1
        if u[5]<n: return bot.reply_to(message, "❌ Нет кексов")
        update_user(user.id, cakes=-n, hunger=n)
        set_user_time(user.id, "last_eat")
        bot.reply_to(message, f"❤️ Сытость +{n}")
        return

    # ---------- Дунуть ----------
    if text.startswith("дунуть"):
        if not can_use_timer(user,"last_smoke",1):
            cursor.execute("SELECT last_smoke FROM cannabis WHERE user_id=?", (str(user.id),))
            last = datetime.fromisoformat(cursor.fetchone()[0])
            mins = int((timedelta(hours=1)-(datetime.now()-last)).seconds/60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        u = get_user(user)
        if u[6]<=0: return bot.reply_to(message,"❌ Нет косяков")
        effect = random.randint(1,5)
        update_user(user.id, joints=-1, high=effect)
        set_user_time(user.id,"last_smoke")
        bot.reply_to(message,f"🔥 Ты кайфанул 😵‍💫\nКайф +{effect}")
        return