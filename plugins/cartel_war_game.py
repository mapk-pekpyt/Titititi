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
# ===== BLOCK: БОЁВКА (HP / ATTACK / ПОБЕГ) ===========
# =====================================================
def calc_army(rows):
    total_hp = 0
    total_attack = 0
    total_units = 0

    for r in rows:
        stats = MERC_TYPES[r["merc_type"]]
        total_hp += stats["hp"] * r["count"]
        total_attack += stats["attack"] * r["count"]
        total_units += r["count"]

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
            "UPDATE cartel_members SET count = count - ? "
            "WHERE user_id=? AND merc_type=? AND role=?",
            (lost, user_id, r["merc_type"], role)
        )

        report.append(f"{lost} {r['merc_type']}")

    conn.commit()
    return report


def resolve_battle(attacker_rows, defender_rows, attacker_id, defender_id):
    atk_hp, atk_atk, atk_units = calc_army(attacker_rows)
    def_hp, def_atk, def_units = calc_army(defender_rows)

    if atk_atk <= 0 or def_atk <= 0:
        return None

    atk_time = def_hp / atk_atk
    def_time = atk_hp / def_atk

    if atk_time < def_time:
        winner = "attacker"
        atk_loss_units = int(atk_units * random.uniform(0.2, 0.5))
        def_loss_units = def_units
    else:
        winner = "defender"
        def_loss_units = int(def_units * random.uniform(0.2, 0.5))
        atk_loss_units = atk_units

    # 50% шанс побега половины при поражении
    escaped = False
    if random.random() < 0.5:
        escaped = True
        if winner == "attacker":
            def_loss_units = int(def_loss_units * 0.5)
        else:
            atk_loss_units = int(atk_loss_units * 0.5)

    atk_report = apply_losses(attacker_rows, atk_loss_units, attacker_id, "рейд")
    def_report = apply_losses(defender_rows, def_loss_units, defender_id, "защита")

    return {
        "winner": winner,
        "atk_lost": atk_loss_units,
        "def_lost": def_loss_units,
        "atk_report": atk_report,
        "def_report": def_report,
        "escaped": escaped
    }

# =====================================================# =====================================================
# 👥 НАЁМНИКИ, ОТРЯДЫ, РЕЙД, МИССИИ, АККРЕДИТАЦИЯ
# =====================================================
from plugins.cannabis_game import get_user, add
from datetime import datetime, timedelta
import random
from plugins.common import get_name

MERC_TYPES = {
    "гопник": {"hp": 100, "attack": 20, "cost": 500},
    "бандит": {"hp": 150, "attack": 40, "cost": 750},
    "солдат": {"hp": 350, "attack": 70, "cost": 1000},
}

ROLES = ["защита", "рейд", "задания"]
ADMIN_ID = "5791171535"

# ------------------ СТИЛЬ ------------------
def cartel_msg(user, text):
    return f"🕴 {get_name(user)}\n{text}"

# ------------------ НАЁМ ------------------
def hire(bot, message, uid, u, text):
    parts = text.split()
    name = get_name(message.from_user)

    if len(parts) != 4:
        return bot.reply_to(message, f"{name}, говори чётко:\nнанять <защита|рейд|задания> <гопник|бандит|солдат> <число>")

    role, merc, count = parts[1], parts[2], parts[3]

    if role not in ROLES:
        return bot.reply_to(message, f"{name}, такой роли нет. Выбирай: {', '.join(ROLES)}")
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
            f"{name}, пришёл нанимать детей, но денег мало.\nНе хватает {need} 💶.\nМаксимум можно нанять: {can}"
        )

    # списываем деньги
    add(uid, "money", -cost)

    # добавляем наёмников
    cursor.execute("""
        INSERT INTO cartel_members (user_id, merc_type, role, count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, merc_type, role)
        DO UPDATE SET count = count + ?
    """, (uid, merc, role, count, count))
    conn.commit()

    # перечитываем баланс
    u = get_user(message.from_user)

    return bot.reply_to(message,
        f"{name}, ты нанял {count} {merc}.\n"
        f"Роль: {role}.\nОтносись к ним с уважением.\nОсталось 💶 {u['money']}"
    )

# ------------------ ОТРЯДЫ ------------------
def squads(bot, message, uid):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        return bot.reply_to(message, cartel_msg(message.from_user, "У тебя пока нет наемников."))

    txt = "Твои отряды:\n"
    for r in rows:
        txt += f"• {r['merc_type']} | Роль: {r['role']} | Кол-во: {r['count']}\n"

    return bot.reply_to(message, cartel_msg(message.from_user, txt))

# ------------------ РЕЙД ------------------
def raid(bot, message, uid):
    attacker = message.from_user
    aname = get_name(attacker)

    if not message.reply_to_message:
        return bot.reply_to(message, f"{aname}, рейд делается ответом на сообщение.")

    target = message.reply_to_message.from_user
    tid = str(target.id)
    tname = get_name(target)

    # атакующие
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='рейд'", (uid,))
    atk = cursor.fetchall()
    if not atk:
        return bot.reply_to(message, f"{aname}, тебе некого отправлять в рейд.")

    # защитники
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='защита'", (tid,))
    dfn = cursor.fetchall()

    atk_hp = sum(MERC_TYPES[a["merc_type"]]["hp"] * a["count"] for a in atk)
    atk_power = sum(MERC_TYPES[a["merc_type"]]["attack"] * a["count"] for a in atk)
    def_hp = sum(MERC_TYPES[d["merc_type"]]["hp"] * d["count"] for d in dfn)
    def_power = sum(MERC_TYPES[d["merc_type"]]["attack"] * d["count"] for d in dfn)

    # простой бой, урон на силу/HP
    atk_time = def_hp / max(atk_power,1)
    def_time = atk_hp / max(def_power,1)

    # потери
    atk_loss = int(sum(a["count"] for a in atk) * 0.5 if atk_time > def_time else sum(a["count"] for a in atk) * 0.2)
    def_loss = int(sum(d["count"] for d in dfn) * 0.5 if def_time > atk_time else sum(d["count"] for d in dfn) * 0.2)

    # случайный шанс побега половины атакующих при поражении
    if atk_time > def_time:
        loot = int(get_user(target)["money"] * 0.5)
        add(uid, "money", loot)
        add(tid, "money", -loot)
        msg = f"{aname} победил.\nЗабрал {loot} 💶 у {tname}.\nПотери твоих: {atk_loss}\nПотери врага: {def_loss}"
    else:
        # шанс бегства
        for a in atk:
            if random.random() < 0.5:
                a_half = a["count"] // 2
                cursor.execute(
                    "UPDATE cartel_members SET count = ? WHERE user_id=? AND merc_type=? AND role='рейд'",
                    (a_half, uid, a["merc_type"])
                )
        msg = f"{aname} проиграл.\nПотери твоих: {atk_loss}\nПотери врага: {def_loss}\nПоловина твоих могла сбежать."

    # списываем потери
    for a in atk:
        lost = min(a["count"], atk_loss)
        cursor.execute(
            "UPDATE cartel_members SET count = count - ? WHERE user_id=? AND merc_type=? AND role='рейд'",
            (lost, uid, a["merc_type"])
        )
    for d in dfn:
        lost = min(d["count"], def_loss)
        cursor.execute(
            "UPDATE cartel_members SET count = count - ? WHERE user_id=? AND merc_type=? AND role='защита'",
            (lost, tid, d["merc_type"])
        )
    conn.commit()

    return bot.reply_to(message, cartel_msg(attacker, msg))

# ------------------ МИССИИ ------------------
def missions(bot, message, uid):
    cursor.execute("SELECT * FROM missions WHERE user_id=?", (uid,))
    m = cursor.fetchone()

    if m:
        start = datetime.fromisoformat(m["start_time"])
        end = start + timedelta(hours=24)
        if datetime.now() < end:
            left = int((end - datetime.now()).total_seconds() // 3600)
            return bot.reply_to(message, cartel_msg(message.from_user, f"Люди вернутся через {left} ч."))

        cursor.execute("DELETE FROM missions WHERE user_id=?", (uid,))
        conn.commit()

        if random.random() < 0.6:
            reward = random.randint(500, 1500)
            add(uid, "money", reward)
            return bot.reply_to(message, cartel_msg(message.from_user, f"Дело прошло чисто. +{reward} 💶"))
        else:
            return bot.reply_to(message, cartel_msg(message.from_user, "Дело сорвалось. Кто-то не вернулся."))

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='задания'", (uid,))
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, cartel_msg(message.from_user, "Некого отправлять."))

    cursor.execute("""
        INSERT INTO missions (user_id, merc_type, count, start_time)
        VALUES (?, ?, ?, ?)
    """, (uid, row["merc_type"], row["count"], datetime.now().isoformat()))
    conn.commit()

    return bot.reply_to(message, cartel_msg(message.from_user, "Люди ушли. Вернутся через сутки."))

# ------------------ АККРЕДИТАЦИЯ ------------------
def accreditation(bot, message, uid, text):
    if uid != ADMIN_ID:
        return
    parts = text.split()
    if len(parts) == 2 and parts[1].isdigit():
        add(uid, "money", int(parts[1]))
        return bot.reply_to(message, cartel_msg(message.from_user, f"Средства выданы."))
# =====================================================
# ===== BLOCK: КАРТЕЛИ (будущее) =====================
# =====================================================

# =====================================================
# ===== BLOCK: КВ — ВОЙНЫ КАРТЕЛЕЙ ====================
# =====================================================

# =====================================================
# ===== BLOCK: КОЛОНИИ И КРЫША ========================
# =====================================================