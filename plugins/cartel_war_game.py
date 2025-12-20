import sqlite3
import random
from datetime import datetime, timedelta

from plugins.common import get_name
from plugins.cannabis_game import get_user, add

# =====================================================
# БАЗА
# =====================================================
DB = "data/cartel_game.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cartel_members (
    user_id TEXT,
    merc_type TEXT,
    role TEXT,
    count INTEGER NOT NULL,
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
    "гопник":  {"hp": 100, "attack": 20, "cost": 500},
    "бандит":  {"hp": 150, "attack": 40, "cost": 750},
    "солдат":  {"hp": 350, "attack": 70, "cost": 1000},
}

ROLES = ["рейд", "защита", "задания"]
ADMIN_ID = "5791171535"

# =====================================================
# УТИЛИТЫ
# =====================================================
def say(user, text):
    return f"{get_name(user)},\n{text}"

# =====================================================
# НАЁМ — ОПЛАТА ЗДЕСЬ 100% РАБОЧАЯ
# =====================================================
def hire(bot, message, uid, text):
    parts = text.split()
    user = message.from_user
    name = get_name(user)

    if len(parts) != 4:
        return bot.reply_to(
            message,
            f"{name}, формат такой:\n"
            f"нанять <рейд|защита|задания> <гопник|бандит|солдат> <число>"
        )

    role, merc, count = parts[1], parts[2], parts[3]

    if role not in ROLES:
        return bot.reply_to(message, f"{name}, такой роли нет.")
    if merc not in MERC_TYPES:
        return bot.reply_to(message, f"{name}, таких людей у меня нет.")
    if not count.isdigit() or int(count) <= 0:
        return bot.reply_to(message, f"{name}, количество должно быть числом.")

    count = int(count)
    cost = MERC_TYPES[merc]["cost"] * count

    u = get_user(user)
    if u["money"] < cost:
        can = u["money"] // MERC_TYPES[merc]["cost"]
        return bot.reply_to(
            message,
            f"{name}, денег не хватает.\n"
            f"Нужно {cost}, у тебя {u['money']}.\n"
            f"Максимум можешь нанять: {can}"
        )

    # 1️⃣ СНАЧАЛА НАЁМНИКИ
    cursor.execute("""
        INSERT INTO cartel_members (user_id, merc_type, role, count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, merc_type, role)
        DO UPDATE SET count = count + excluded.count
    """, (uid, merc, role, count))
    conn.commit()

    # 2️⃣ ПОТОМ ДЕНЬГИ
    add(uid, "money", -cost)

    # 3️⃣ ПЕРЕЧИТЫВАЕМ БАЛАНС
    u = get_user(user)

    return bot.reply_to(
        message,
        f"{name}, договор закрыт.\n"
        f"{count} {merc} теперь при деле.\n"
        f"Назначение: {role}.\n"
        f"Осталось денег: {u['money']} 💶"
    )

# =====================================================
# ОТРЯД
# =====================================================
def squads(bot, message, uid):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (uid,))
    rows = cursor.fetchall()

    if not rows:
        return bot.reply_to(message, say(message.from_user, "У тебя пока никого нет."))

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
# АККРЕДИТАЦИЯ (СЕБЕ И ДРУГИМ)
# =====================================================
def accreditation(bot, message, uid, text):
    if uid != ADMIN_ID:
        return

    parts = text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return bot.reply_to(message, "Формат: аккредитация <сумма> (ответом)")

    if not message.reply_to_message:
        return bot.reply_to(message, "Нужно ответом на сообщение.")

    target = message.reply_to_message.from_user
    amount = int(parts[1])

    add(str(target.id), "money", amount)

    return bot.reply_to(
        message,
        f"{get_name(target)} получил {amount} 💶."
    )

# =====================================================
# HANDLE — НЕ ТРОГАТЬ
# =====================================================
def handle(bot, message):
    uid = str(message.from_user.id)
    text = (message.text or "").lower().strip()

    if text.startswith("нанять"):
        return hire(bot, message, uid, text)
    if text == "отряд":
        return squads(bot, message, uid)
    if text.startswith("аккредитация"):
        return accreditation(bot, message, uid, text)

# =====================================================
# ________ ДАЛЬШЕ МОЖНО ДОБАВЛЯТЬ БЛОКИ ________
# РЕЙД
# МИССИИ
# КАРТЕЛИ
# КВ
# ______________________________________________