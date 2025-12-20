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

# =====================================================
# ===== BLOCK: НАЙМ НАЁМНИКОВ =========================
# =====================================================
def hire(bot, message, uid, u, text):
    parts = text.split()
    name = get_name(message.from_user)

    if len(parts) != 4:
        return bot.reply_to(message,
            f"{name}, говори чётко.\n"
            f"нанять <защита|рейд|задания> <гопник|бандит|солдат> <число>"
        )

    role, merc, count = parts[1], parts[2], parts[3]

    if role not in ROLES or merc not in MERC_TYPES or not count.isdigit():
        return bot.reply_to(message, f"{name}, ты путаешь слова.")

    count = int(count)
    cost = MERC_TYPES[merc]["cost"] * count

    if u["money"] < cost:
        need = cost - u["money"]
        can = u["money"] // MERC_TYPES[merc]["cost"]
        return bot.reply_to(message,
            f"{name}, ты пришёл без денег.\n"
            f"Не хватает {need} 💶.\n"
            f"Максимум можешь нанять: {can}."
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

# ⬇️ ОБЯЗАТЕЛЬНО перечитываем игрока из БД
u = get_user(message.from_user)

return bot.reply_to(
    message,
    f"{name}, сделка закрыта.\n"
    f"{count} {merc} теперь служат тебе.\n"
    f"Осталось 💶 {u['money']}"
)

# =====================================================
# ===== BLOCK: ОТРЯДЫ =================================
# =====================================================
def squads(bot, message, uid):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (uid,))
    rows = cursor.fetchall()

    if not rows:
        return bot.reply_to(message, cartel_msg(
            message.from_user, "У тебя пока нет людей."
        ))

    txt = "Твоя семья:\n"
    for r in rows:
        txt += f"• {r['merc_type']} — {r['role']} — {r['count']}\n"

    return bot.reply_to(message, cartel_msg(message.from_user, txt))

# =====================================================
# ===== BLOCK: РЕЙД ===================================
# =====================================================
def raid(bot, message, uid):
    attacker = message.from_user
    aname = get_name(attacker)

    if not message.reply_to_message:
        return bot.reply_to(message, f"{aname}, рейд — ответом.")

    target = message.reply_to_message.from_user
    tid = str(target.id)
    tname = get_name(target)

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='рейд'", (uid,))
    atk = cursor.fetchall()

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='защита'", (tid,))
    dfn = cursor.fetchall()

    if not atk:
        return bot.reply_to(message, f"{aname}, тебе некого посылать.")

    result = resolve_battle(atk, dfn, uid, tid)
    if not result:
        return bot.reply_to(message, "Бой не состоялся.")

    text = (
        f"Рейд против {tname}\n\n"
        f"Победил: {'ты' if result['winner']=='attacker' else tname}\n\n"
        f"Твои потери: {result['atk_lost']}\n"
        f"Их потери: {result['def_lost']}\n"
    )

    if result["escaped"]:
        text += "\nЧасть бойцов сумела сбежать."

    if result["winner"] == "attacker":
        tu = get_user(target)
        loot = int(tu["money"] * 0.5)
        add(uid, "money", loot)
        add(tid, "money", -loot)
        text += f"\nТы забрал {loot} 💶."

    return bot.reply_to(message, cartel_msg(attacker, text))

# =====================================================
# ===== BLOCK: МИССИИ ================================
# =====================================================
def missions(bot, message, uid):
    cursor.execute("SELECT * FROM missions WHERE user_id=?", (uid,))
    m = cursor.fetchone()

    if m:
        start = datetime.fromisoformat(m["start_time"])
        end = start + timedelta(hours=24)
        if datetime.now() < end:
            left = int((end - datetime.now()).total_seconds() // 3600)
            return bot.reply_to(message, cartel_msg(
                message.from_user, f"Люди вернутся через {left} ч."
            ))

        cursor.execute("DELETE FROM missions WHERE user_id=?", (uid,))
        conn.commit()

        if random.random() < 0.6:
            reward = random.randint(500, 1500)
            add(uid, "money", reward)
            return bot.reply_to(message, cartel_msg(
                message.from_user, f"Дело прошло чисто. +{reward} 💶."
            ))
        else:
            return bot.reply_to(message, cartel_msg(
                message.from_user, "Дело сорвалось. Вернулись не все."
            ))

    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role='задания'", (uid,)
    )
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, cartel_msg(
            message.from_user, "Некого отправлять."
        ))

    cursor.execute("""
        INSERT INTO missions (user_id, merc_type, count, start_time)
        VALUES (?, ?, ?, ?)
    """, (uid, row["merc_type"], row["count"], datetime.now().isoformat()))
    conn.commit()

    return bot.reply_to(message, cartel_msg(
        message.from_user, "Люди ушли. Вернутся через сутки."
    ))

# =====================================================
# ===== BLOCK: АККРЕДИТАЦИЯ ==========================
# =====================================================
def accreditation(bot, message, uid, text):
    if uid != ADMIN_ID:
        return
    parts = text.split()
    if len(parts) == 2 and parts[1].isdigit():
        add(uid, "money", int(parts[1]))
        return bot.reply_to(message, cartel_msg(
            message.from_user, "Средства выданы."
        ))

# =====================================================
# 🔥 HANDLE (ПОД ТВОЙ MAIN)
# =====================================================
def handle(bot, message):
    user = message.from_user
    uid = str(user.id)
    text = (message.text or "").lower().strip()
    u = get_user(user)

    if text.startswith("нанять"):
        return hire(bot, message, uid, u, text)
    if text == "отряд":
        return squads(bot, message, uid)
    if text.startswith("рейд"):
        return raid(bot, message, uid)
    if text == "миссии":
        return missions(bot, message, uid)
    if text.startswith("аккредитация"):
        return accreditation(bot, message, uid, text)

# =====================================================
# ===== BLOCK: КАРТЕЛИ (будущее) =====================
# =====================================================

# =====================================================
# ===== BLOCK: КВ — ВОЙНЫ КАРТЕЛЕЙ ====================
# =====================================================

# =====================================================
# ===== BLOCK: КОЛОНИИ И КРЫША ========================
# =====================================================