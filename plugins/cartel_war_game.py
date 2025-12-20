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
# 🎩 СТИЛЬ
# =====================================================
def cartel_msg(user, text):
    return f"🕴 {get_name(user)}\n{text}"

# =====================================================
# ===== БОЁВКА =====
# =====================================================
def calc_army(rows):
    total_hp = sum(MERC_TYPES[r["merc_type"]]["hp"] * r["count"] for r in rows)
    total_attack = sum(MERC_TYPES[r["merc_type"]]["attack"] * r["count"] for r in rows)
    total_units = sum(r["count"] for r in rows)
    return total_hp, total_attack, total_units

def apply_losses(rows, loss_units, user_id, role):
    remaining_loss = loss_units
    report = []
    for r in rows:
        if remaining_loss <= 0:
            break
        lost = min(r["count"], remaining_loss)
        remaining_loss -= lost
        cursor.execute(
            "UPDATE cartel_members SET count = count - ? WHERE user_id=? AND merc_type=? AND role=?",
            (lost, user_id, r["merc_type"], role)
        )
        report.append(f"{lost} {r['merc_type']}")
    conn.commit()
    return report

def resolve_battle(atk_rows, def_rows, atk_id, def_id):
    atk_hp, atk_attack, atk_units = calc_army(atk_rows)
    def_hp, def_attack, def_units = calc_army(def_rows)

    if atk_attack <= 0 or def_attack <= 0:
        return None

    atk_time = def_hp / atk_attack
    def_time = atk_hp / def_attack

    if atk_time < def_time:
        winner = "attacker"
        atk_loss = int(atk_units * random.uniform(0.2,0.5))
        def_loss = def_units
    else:
        winner = "defender"
        def_loss = int(def_units * random.uniform(0.2,0.5))
        atk_loss = atk_units

    # 50% шанс побега половины проигравших
    escaped = False
    if random.random() < 0.5:
        escaped = True
        if winner == "attacker":
            def_loss = int(def_loss*0.5)
        else:
            atk_loss = int(atk_loss*0.5)

    atk_report = apply_losses(atk_rows, atk_loss, atk_id, "рейд")
    def_report = apply_losses(def_rows, def_loss, def_id, "защита")

    return {
        "winner": winner,
        "atk_lost": atk_loss,
        "def_lost": def_loss,
        "atk_report": atk_report,
        "def_report": def_report,
        "escaped": escaped
    }

# =====================================================
# ===== НАЁМНИКИ =====
# =====================================================
def hire(bot, message, uid, u, text):
    parts = text.split()
    name = get_name(message.from_user)
    if len(parts) != 4:
        return bot.reply_to(message, f"{name}, говори чётко: нанять <роль> <тип> <кол-во>")

    role, merc, count = parts[1], parts[2], parts[3]
    if role not in ROLES:
        return bot.reply_to(message, f"{name}, роли: {', '.join(ROLES)}")
    if merc not in MERC_TYPES:
        return bot.reply_to(message, f"{name}, таких людей я не нанимаю.")
    if not count.isdigit() or int(count) <= 0:
        return bot.reply_to(message, f"{name}, количество должно быть числом.")

    count = int(count)
    cost = MERC_TYPES[merc]["cost"] * count
    if u["money"] < cost:
        need = cost - u["money"]
        can = u["money"] // MERC_TYPES[merc]["cost"]
        return bot.reply_to(message,
            f"{name}, пришёл нанимать, но денег мало. Не хватает {need} 💶. Можно нанять: {can}")

    add(uid, "money", -cost)
    cursor.execute("""
        INSERT INTO cartel_members (user_id, merc_type, role, count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, merc_type, role) DO UPDATE SET count=count+?
    """, (uid, merc, role, count, count))
    conn.commit()
    u = get_user(message.from_user)

    return bot.reply_to(message,
        f"{name}, ты нанял {count} {merc}.\nРоль: {role}\nОсталось 💶 {u['money']}")

# =====================================================
# ===== ОТРЯДЫ =====
# =====================================================
def squads(bot, message, uid):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        return bot.reply_to(message, cartel_msg(message.from_user, "У тебя пока нет наемников."))

    txt = "Твои отряды:\n"
    for r in rows:
        txt += f"• {r['merc_type']} | Роль: {r['role']} | Кол-во: {r['count']}\n"
    return bot.reply_to(message, cartel_msg(message.from_user, txt))

# =====================================================
# ===== РЕЙД =====
# =====================================================
def raid(bot, message, uid):
    if not message.reply_to_message:
        return bot.reply_to(message, "Рейд делается ответом на сообщение.")
    target = message.reply_to_message.from_user
    tid = str(target.id)
    tname = get_name(target)

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='рейд'", (uid,))
    atk = cursor.fetchall()
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='защита'", (tid,))
    dfn = cursor.fetchall()
    if not atk:
        return bot.reply_to(message, "Тебе некого отправлять.")

    result = resolve_battle(atk, dfn, uid, tid)
    if not result:
        return bot.reply_to(message, "Бой не состоялся.")

    msg = f"Рейд против {tname}\nПобедил: {'Ты' if result['winner']=='attacker' else tname}\n"
    msg += f"Твои потери: {result['atk_lost']}\nПотери врага: {result['def_lost']}\n"
    if result['escaped']:
        msg += "Часть бойцов могла сбежать.\n"
    if result['winner']=='attacker':
        tu = get_user(target)
        loot = int(tu["money"]*0.5)
        add(uid, "money", loot)
        add(tid, "money", -loot)
        msg += f"Ты забрал {loot} 💶."

    return bot.reply_to(message, cartel_msg(message.from_user, msg))

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
        if random.random()<0.6:
            reward = random.randint(500,1500)
            add(uid, "money", reward)
            return bot.reply_to(message, cartel_msg(message.from_user, f"Дело прошло чисто. +{reward} 💶"))
        else:
            return bot.reply_to(message, cartel_msg(message.from_user, "Дело сорвалось. Кто-то не вернулся."))

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='задания'", (uid,))
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, cartel_msg(message.from_user, "Некого отправлять."))

    cursor.execute("INSERT INTO missions (user_id, merc_type, count, start_time) VALUES (?, ?, ?, ?)",
                   (uid, row["merc_type"], row["count"], datetime.now().isoformat()))
    conn.commit()
    return bot.reply_to(message, cartel_msg(message.from_user, "Люди ушли. Вернутся через сутки."))

# =====================================================
# ===== АККРЕДИТАЦИЯ =====
# =====================================================
def accreditation(bot, message, uid, text):
    if uid != ADMIN_ID:
        return
    parts = text.split()
    if len(parts)==2 and parts[1].isdigit():
        add(uid, "money", int(parts[1]))
        return bot.reply_to(message, cartel_msg(message.from_user, "Средства выданы."))

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