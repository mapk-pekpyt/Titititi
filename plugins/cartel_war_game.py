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
    user = message.from_user
    name = get_name(user)

    if len(parts) != 4:
        return bot.reply_to(
            message,
            f"{name}, пиши нормально:\n"
            f"нанять <рейд|защита|задания> <гопник|бандит|солдат> <число>"
        )

    role, merc, count = parts[1], parts[2], parts[3]

    if role not in ROLES or merc not in MERC_TYPES or not count.isdigit():
        return bot.reply_to(message, f"{name}, ты несёшь хуйню.")

    count = int(count)
    if count <= 0:
        return bot.reply_to(message, f"{name}, количество должно быть больше нуля.")

    cost = MERC_TYPES[merc]["cost"] * count
    u = get_user(user)

    if u["money"] < cost:
        return bot.reply_to(
            message,
            f"{name}, денег мало.\n"
            f"Нужно {cost}, у тебя {u['money']}."
        )

    # 1️⃣ сначала добавляем наёмников
    cursor.execute("""
        INSERT INTO cartel_members (user_id, merc_type, role, count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, merc_type, role)
        DO UPDATE SET count = count + ?
    """, (uid, merc, role, count, count))
    conn.commit()

    # 2️⃣ потом списываем деньги
    add(uid, "money", -cost)

    # 3️⃣ перечитываем баланс
    u = get_user(user)

    return bot.reply_to(
        message,
        f"{name}, договор закрыт.\n"
        f"{count} {merc} теперь работают на тебя.\n"
        f"Роль: {role}.\n"
        f"Осталось денег: {u['money']} 💶"
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
    user = message.from_user
    name = get_name(user)

    if not message.reply_to_message:
        return bot.reply_to(message, f"{name}, рейд — ответом.")

    target = message.reply_to_message.from_user

    if target.is_bot:
        return bot.reply_to(message, f"{name}, ты серьёзно? Это бот.")

    if str(target.id) == uid:
        return bot.reply_to(message, f"{name}, себя рейдить — клиника.")

    tid = str(target.id)
    tname = get_name(target)

    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role='рейд'",
        (uid,)
    )
    atk = cursor.fetchall()

    if not atk:
        return bot.reply_to(message, f"{name}, тебе не с кем идти.")

    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role='защита'",
        (tid,)
    )
    dfn = cursor.fetchall()

    atk_hp, atk_dps, atk_units = army_power(atk)
    def_hp, def_dps, def_units = army_power(dfn)

    if atk_dps <= 0:
        return bot.reply_to(message, f"{name}, твои бойцы не умеют стрелять.")

    # время уничтожения
    time_to_kill_def = def_hp / atk_dps if def_hp > 0 else 0
    time_to_kill_atk = atk_hp / def_dps if def_dps > 0 else 999

    if time_to_kill_def < time_to_kill_atk:
        # победа
        atk_loss = int(atk_units * random.uniform(0.2, 0.4))
        def_loss = def_units

        remove_units(uid, "рейд", atk_loss)
        remove_units(tid, "защита", def_loss)

        tu = get_user(target)
        loot = int(tu["money"] * 0.4)
        add(uid, "money", loot)
        add(tid, "money", -loot)

        text = (
            f"Ты зашёл жёстко.\n\n"
            f"Добыча: {loot} 💶\n\n"
            f"Потери:\n"
            f"У тебя: {atk_loss}\n"
            f"У них: {def_loss}"
        )
    else:
        atk_loss = int(atk_units * random.uniform(0.6, 0.9))
        remove_units(uid, "рейд", atk_loss)

        text = (
            f"Засада.\n\n"
            f"Рейд сорвался.\n"
            f"Потери: {atk_loss}"
        )

    return bot.reply_to(message, f"{name},\n{text}")
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