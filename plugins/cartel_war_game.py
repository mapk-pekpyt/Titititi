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
# ===== НАЙМ НАЁМНИКОВ (ИСПРАВЛЕНО) ====================
# =====================================================
def hire(bot, message, uid, u, text):
    parts = text.split()
    name = get_name(message.from_user)

    if len(parts) != 4:
        return bot.reply_to(
            message,
            f"{name}, говори нормально.\n"
            f"Нанять <защита|рейд|задания> <гопник|бандит|солдат> <число>"
        )

    role, merc, count = parts[1], parts[2], parts[3]

    if role not in ROLES:
        return bot.reply_to(message, f"{name}, такой роли нет.")
    if merc not in MERC_TYPES:
        return bot.reply_to(message, f"{name}, таких людей у меня не бывает.")
    if not count.isdigit() or int(count) <= 0:
        return bot.reply_to(message, f"{name}, число назови, а не херню.")

    count = int(count)
    cost = MERC_TYPES[merc]["cost"] * count

    if u["money"] < cost:
        need = cost - u["money"]
        can = u["money"] // MERC_TYPES[merc]["cost"]
        return bot.reply_to(
            message,
            f"{name}, ты пришёл ко мне без денег?\n"
            f"Не хватает {need} 💶.\n"
            f"Максимум можешь нанять: {can}"
        )

    # ⚠️ СНАЧАЛА ПРОБУЕМ СПИСАТЬ ДЕНЬГИ
    ok = add(uid, "money", -cost)
    if ok is False:
        return bot.reply_to(
            message,
            f"{name}, сделка не прошла.\n"
            f"Деньги у тебя мутные, иди разберись."
        )

    # ✅ ТОЛЬКО ПОСЛЕ ЭТОГО ДОБАВЛЯЕМ НАЁМНИКОВ
    cursor.execute("""
        INSERT INTO cartel_members (user_id, merc_type, role, count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, merc_type, role)
        DO UPDATE SET count = count + ?
    """, (uid, merc, role, count, count))
    conn.commit()

    u = get_user(message.from_user)

    return bot.reply_to(
        message,
        f"{name}, договор закрыт.\n"
        f"{count} {merc} теперь работают на тебя.\n"
        f"Роль: {role}.\n"
        f"Деньги остались: {u['money']} 💶"
    )
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

    txt = "💣 Твои отряды 💣\n"
    for role in ["рейд","защита","задания"]:
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

    txt = f"💣 Рейд на {tname} 💣\n\n"
    txt += f"🏆 Победитель: {'Ты' if result['winner']=='attacker' else tname}\n\n"
    if result['atk_report']:
        txt += "⚔ Потери твоих:\n" + "\n".join(result['atk_report']) + "\n"
    if result['def_report']:
        txt += "🛡 Потери противника:\n" + "\n".join(result['def_report']) + "\n"
    if result['escaped']:
        txt += "💨 Часть бойцов могла сбежать.\n"
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
        left = int((end - datetime.now()).total_seconds()//3600)
        return bot.reply_to(message, cartel_msg(message.from_user, f"Люди вернутся через {left} ч."))

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='задания'", (uid,))
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, cartel_msg(message.from_user, "Некого отправлять в задания."))

    cursor.execute("INSERT INTO missions (user_id, merc_type, count, start_time) VALUES (?, ?, ?, ?)",
                   (uid, row["merc_type"], row["count"], datetime.now().isoformat()))
    conn.commit()
    return bot.reply_to(message, cartel_msg(message.from_user, "💣 Люди ушли на задания. Вернутся через сутки."))
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