import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name
from plugins.cannabis_game import get_user, add

DB = "data/cartel_game.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# =====================================================
# 📦 БАЗЫ ДАННЫХ
# =====================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS cartel_members (
    user_id TEXT,
    merc_type TEXT,
    role TEXT,
    count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, merc_type, role)
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS missions (
    user_id TEXT PRIMARY KEY,
    merc_type TEXT,
    count INTEGER,
    start_time TEXT
)
""")
conn.commit()

# =====================================================
# 🧠 КОНСТАНТЫ
# =====================================================
MERC_TYPES = {
    "гопник": {"hp": 100, "attack": 20, "cost": 500},
    "бандит": {"hp": 150, "attack": 40, "cost": 750},
    "солдат": {"hp": 350, "attack": 70, "cost": 1000},
}
ROLES = ["защита", "рейд", "задания"]
ADMIN_ID = "5791171535"

# =====================================================
# 🎩 СТИЛЬ СООБЩЕНИЙ
# =====================================================
def cartel_msg(user, text):
    return f"💣 Крестный отец 💣\n{get_name(user)}\n{text}"

# =====================================================
# ===== НАЁМНИКИ =====
# =====================================================
def hire(bot, message, uid, u, text):
    parts = text.split()
    name = get_name(message.from_user)
    if len(parts) != 4:
        return bot.reply_to(message, f"{name}, формулируй так:\nнанять <защита|рейд|задания> <гопник|бандит|солдат> <число>")

    role, merc, count = parts[1], parts[2], parts[3]
    if role not in ROLES:
        return bot.reply_to(message, f"{name}, роли семьи: {', '.join(ROLES)}")
    if merc not in MERC_TYPES:
        return bot.reply_to(message, f"{name}, таких людей я не нанимаю.")
    if not count.isdigit() or int(count)<=0:
        return bot.reply_to(message, f"{name}, количество должно быть числом больше нуля.")

    count = int(count)
    cost = MERC_TYPES[merc]["cost"] * count
    if u["money"] < cost:
        need = cost - u["money"]
        can = u["money"] // MERC_TYPES[merc]["cost"]
        return bot.reply_to(message,
            f"{name}, пришёл нанимать, но не взял достаточно денег.\nНе хватает {need} 💶.\nМожно нанять: {can}")

    # Добавляем наёмников
    cursor.execute("""
        INSERT INTO cartel_members (user_id, merc_type, role, count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, merc_type, role) DO UPDATE SET count=count+?
    """, (uid, merc, role, count, count))
    conn.commit()

    # Только после успешного найма списываем деньги
    add(uid, "money", -cost)
    u = get_user(message.from_user)

    return bot.reply_to(message,
        f"{name}, ты нанял {count} {merc}.\n"
        f"Роль: {role}\n"
        f"Относись к ним с уважением, они теперь часть семьи.\n"
        f"💶 Осталось: {u['money']}")

# =====================================================
# ===== ОТРЯДЫ =====
# =====================================================
def squads(bot, message, uid):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        return bot.reply_to(message, cartel_msg(message.from_user, "У тебя пока нет наёмников."))

    roles = {"рейд":[], "защита":[], "задания":[]}
    for r in rows:
        if r["count"] > 0:
            roles[r["role"]].append(f"{r['merc_type']} {r['count']}")

    txt = ""
    for role in ["рейд", "защита", "задания"]:
        if roles[role]:
            txt += f"{role.capitalize()}:\n" + "\n".join(roles[role]) + "\n"

    return bot.reply_to(message, cartel_msg(message.from_user, txt.strip()))

# =====================================================
# ===== РЕЙД =====
# =====================================================
def raid(bot, message, uid):
    attacker = message.from_user
    aname = get_name(attacker)
    if not message.reply_to_message:
        return bot.reply_to(message, f"{aname}, рейд делается ответом на сообщение.")

    target = message.reply_to_message.from_user
    tid = str(target.id)
    tname = get_name(target)

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='рейд'", (uid,))
    atk = cursor.fetchall()
    if not atk:
        return bot.reply_to(message, f"{aname}, у тебя нет бойцов для рейда.")

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='защита'", (tid,))
    dfn = cursor.fetchall()

    result = resolve_battle(atk, dfn, uid, tid)
    if not result:
        return bot.reply_to(message, f"{aname}, бой не состоялся.")

    # Формируем красивый отчет
    txt = f"💥 Рейд на {tname} 💥\n\n"
    txt += f"🏆 Победитель: {'Ты' if result['winner']=='attacker' else tname}\n\n"
    txt += "⚔ Потери твоих:\n" + "\n".join(result['atk_report']) + "\n\n" if result['atk_report'] else ""
    txt += "🛡 Потери противника:\n" + "\n".join(result['def_report']) + "\n\n" if result['def_report'] else ""
    if result['escaped']:
        txt += "Часть бойцов могла сбежать.\n"
    if result['winner']=='attacker':
        tu = get_user(target)
        loot = int(tu["money"]*0.5)
        add(uid, "money", loot)
        add(tid, "money", -loot)
        txt += f"💰 Ты забрал {loot} 💶 у {tname}"

    return bot.reply_to(message, cartel_msg(attacker, txt.strip()))

# =====================================================
# ===== МИССИИ =====
# =====================================================
def missions(bot, message, uid):
    cursor.execute("SELECT * FROM missions WHERE user_id=?", (uid,))
    m = cursor.fetchone()

    if m:
        start = datetime.fromisoformat(m["start_time"])
        end = start + timedelta(hours=24)
        if datetime.now() < end:
            left = int((end - datetime.now()).total_seconds()//3600)
            return bot.reply_to(message, cartel_msg(message.from_user, f"Люди вернутся через {left} ч."))
        cursor.execute("DELETE FROM missions WHERE user_id=?", (uid,))
        conn.commit()
        reward = random.randint(500,1500)
        add(uid, "money", reward) if random.random() < 0.6 else None
        msg = f"Дело завершено.\n{'Вы получили '+str(reward)+' 💶' if random.random()<0.6 else 'Кто-то не вернулся'}"
        return bot.reply_to(message, cartel_msg(message.from_user, msg))

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='задания'", (uid,))
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, cartel_msg(message.from_user, "Некого отправлять в задания."))

    cursor.execute("INSERT INTO missions (user_id, merc_type, count, start_time) VALUES (?, ?, ?, ?)",
                   (uid, row["merc_type"], row["count"], datetime.now().isoformat()))
    conn.commit()
    return bot.reply_to(message, cartel_msg(message.from_user, "Люди ушли на задания. Вернутся через сутки."))

# =====================================================
# ===== АККРЕДИТАЦИЯ =====
# =====================================================
def accreditation(bot, message, uid, text):
    if uid != ADMIN_ID:
        return
    parts = text.split()
    if len(parts)==2 and parts[1].isdigit():
        add(uid, "money", int(parts[1]))
        return bot.reply_to(message, cartel_msg(message.from_user, f"Средства выданы."))

# =====================================================
# ===== HANDLE (под твой MAIN) =====
# =====================================================
def handle(bot, message):
    uid = str(message.from_user.id)
    text = (message.text or "").lower().strip()
    u = get_user(message.from_user)
    if text.startswith("нанять"):
        return hire(bot, message, uid, u, text)
    if text=="отряд":
        return squads(bot, message, uid)
    if text.startswith("рейд"):
        return raid(bot, message, uid)
    if text=="миссии":
        return missions(bot, message, uid)
    if text.startswith("аккредитация"):
        return accreditation(bot, message, uid, text)

# =====================================================
# ===== BLOCK: КАРТЕЛИ ===============================
# =====================================================

# =====================================================
# ===== BLOCK: КВ — ВОЙНЫ КАРТЕЛЕЙ ====================
# =====================================================

# =====================================================
# ===== BLOCK: КОЛОНИИ И КРЫША ========================
# =====================================================