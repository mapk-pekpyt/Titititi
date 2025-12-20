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
# БАЗА
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
    start_time TEXT
)
""")
conn.commit()

# =====================================================
# КОНСТАНТЫ
# =====================================================
MERC_TYPES = {
    "гопник": {"hp": 100, "attack": 20, "cost": 500},
    "бандит": {"hp": 150, "attack": 40, "cost": 750},
    "солдат": {"hp": 350, "attack": 70, "cost": 1000},
}

ROLES = ["рейд", "защита", "задания"]
ADMIN_ID = "5791171535"

# =====================================================
# УТИЛИТЫ
# =====================================================
def say(user, text):
    return f"{get_name(user)},\n{text}"

def army_power(rows):
    hp = atk = units = 0
    for r in rows:
        s = MERC_TYPES[r["merc_type"]]
        hp += s["hp"] * r["count"]
        atk += s["attack"] * r["count"]
        units += r["count"]
    return hp, atk, units

def remove_units(user_id, role, loss):
    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role=?",
        (user_id, role)
    )
    rows = cursor.fetchall()
    left = loss

    for r in rows:
        if left <= 0:
            break
        kill = min(r["count"], left)
        left -= kill
        cursor.execute("""
            UPDATE cartel_members
            SET count = count - ?
            WHERE user_id=? AND merc_type=? AND role=?
        """, (kill, user_id, r["merc_type"], role))
    conn.commit()

# =====================================================
# НАЙМ
# =====================================================
def hire(bot, message, uid, text):
    parts = text.split()
    name = get_name(message.from_user)

    if len(parts) != 4:
        return bot.reply_to(
            message,
            say(message.from_user,
                "Пиши так:\n"
                "нанять <рейд|защита|задания> <гопник|бандит|солдат> <число>"
            )
        )

    role, merc, count = parts[1], parts[2], parts[3]

    if role not in ROLES or merc not in MERC_TYPES or not count.isdigit():
        return bot.reply_to(message, say(message.from_user, "Ты сам понял, что написал?"))

    count = int(count)
    cost = MERC_TYPES[merc]["cost"] * count
    u = get_user(message.from_user)

    if u["money"] < cost:
        return bot.reply_to(
            message,
            say(message.from_user,
                f"Денег не хватает.\n"
                f"Нужно {cost}, у тебя {u['money']}."
            )
        )

    # списываем
    add(uid, "money", -cost)

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
        say(message.from_user,
            f"{count} {merc} теперь у тебя.\n"
            f"Роль: {role}.\n"
            f"Осталось денег: {u['money']} 💶"
        )
    )

# =====================================================
# ОТРЯД
# =====================================================
def squads(bot, message, uid):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        return bot.reply_to(message, say(message.from_user, "У тебя никого нет."))

    out = ""
    for role in ROLES:
        block = [r for r in rows if r["role"] == role and r["count"] > 0]
        if not block:
            continue
        out += f"\n{role.capitalize()}:\n"
        for r in block:
            out += f"{r['merc_type'].capitalize()} — {r['count']}\n"

    return bot.reply_to(message, say(message.from_user, out.strip()))

# =====================================================
# РЕЙД
# =====================================================
def raid(bot, message, uid):
    if not message.reply_to_message:
        return bot.reply_to(message, "Рейд — ответом на сообщение.")

    target = message.reply_to_message.from_user
    tid = str(target.id)

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='рейд'", (uid,))
    atk = cursor.fetchall()
    if not atk:
        return bot.reply_to(message, say(message.from_user, "Некем бить."))

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='защита'", (tid,))
    dfn = cursor.fetchall()

    atk_hp, atk_atk, atk_units = army_power(atk)
    def_hp, def_atk, def_units = army_power(dfn)

    if atk_atk <= 0:
        return bot.reply_to(message, "Бой не состоялся.")

    atk_time = def_hp / atk_atk if def_hp else 0
    def_time = atk_hp / def_atk if def_atk else 999

    if atk_time < def_time:
        # победа
        loss_a = int(atk_units * 0.3)
        loss_d = def_units
        remove_units(uid, "рейд", loss_a)
        remove_units(tid, "защита", loss_d)

        tu = get_user(target)
        loot = int(tu["money"] * 0.5)
        add(uid, "money", loot)
        add(tid, "money", -loot)

        text = (
            f"Ты зашёл жёстко.\n"
            f"Забрал {loot} 💶.\n\n"
            f"Потери:\n"
            f"У тебя: {loss_a}\n"
            f"У него: {loss_d}"
        )
    else:
        loss_a = int(atk_units * 0.7)
        remove_units(uid, "рейд", loss_a)

        text = (
            f"Тебя ждали.\n"
            f"Рейд захлебнулся.\n\n"
            f"Потери: {loss_a}"
        )

    return bot.reply_to(message, say(message.from_user, text))

# =====================================================
# АККРЕДИТАЦИЯ
# =====================================================
def accreditation(bot, message, uid, text):
    if uid != ADMIN_ID:
        return

    parts = text.split()
    if not message.reply_to_message or len(parts) != 2 or not parts[1].isdigit():
        return bot.reply_to(message, "Ответом + сумма.")

    target = message.reply_to_message.from_user
    amount = int(parts[1])
    add(str(target.id), "money", amount)

    return bot.reply_to(
        message,
        f"{get_name(target)} получил {amount} 💶."
    )

# =====================================================
# HANDLE
# =====================================================
def handle(bot, message):
    uid = str(message.from_user.id)
    text = (message.text or "").lower().strip()

    if text.startswith("нанять"):
        return hire(bot, message, uid, text)
    if text == "отряд":
        return squads(bot, message, uid)
    if text.startswith("рейд"):
        return raid(bot, message, uid)
    if text.startswith("аккредитация"):
        return accreditation(bot, message, uid, text)