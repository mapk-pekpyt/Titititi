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
    return f"🕴 {get_name(user)}\n{text}"

# =====================================================
# 👥 НАЙМ
# команда: нанять <роль> <тип> <кол-во>
# =====================================================
def hire(bot, message, uid, u, text):
    parts = text.split()
    if len(parts) != 4:
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            "Говори чётко.\nнанять защита гопник 5"
        ))

    role, merc, count = parts[1], parts[2], parts[3]

    if role not in ROLES:
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            f"Роль должна быть: {', '.join(ROLES)}"
        ))

    if merc not in MERC_TYPES:
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            f"Таких людей у меня нет."
        ))

    if not count.isdigit() or int(count) <= 0:
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            "Количество должно быть числом."
        ))

    count = int(count)
    cost = MERC_TYPES[merc]["cost"] * count

    if u["money"] < cost:
        need = cost - u["money"]
        can = u["money"] // MERC_TYPES[merc]["cost"]
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            f"Ты пришёл ко мне без денег.\n"
            f"Не хватает {need} 💶.\n"
            f"Максимум — {can}."
        ))

    add(uid, "money", -cost)

    cursor.execute("""
        INSERT INTO cartel_members (user_id, merc_type, role, count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, merc_type, role)
        DO UPDATE SET count = count + ?
    """, (uid, merc, role, count, count))
    conn.commit()

    return bot.reply_to(message, cartel_msg(
        message.from_user,
        f"Ты нанял {count} {merc}.\n"
        f"Они служат в роли «{role}».\n"
        f"Осталось {u['money'] - cost} 💶."
    ))

# =====================================================
# 👥 ОТРЯДЫ
# команда: отряд
# =====================================================
def squads(bot, message, uid):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (uid,))
    rows = cursor.fetchall()

    if not rows:
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            "У тебя пока нет людей."
        ))

    txt = "Твои люди:\n"
    for r in rows:
        txt += f"• {r['merc_type']} — {r['role']} — {r['count']}\n"

    return bot.reply_to(message, cartel_msg(message.from_user, txt))

# =====================================================
# ⚔ РЕЙД
# команда: рейд (ответом)
# =====================================================
def raid(bot, message, uid):
    if not message.reply_to_message:
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            "Рейды делают ответом на сообщение."
        ))

    target = message.reply_to_message.from_user
    tid = str(target.id)

    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role='рейд'", (uid,)
    )
    atk = cursor.fetchall()
    if not atk:
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            "Некого отправлять."
        ))

    atk_power = sum(MERC_TYPES[a["merc_type"]]["attack"] * a["count"] for a in atk)

    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=?", (tid,)
    )
    defn = cursor.fetchall()
    def_power = sum(MERC_TYPES[d["merc_type"]]["attack"] * d["count"] for d in defn)

    if atk_power > def_power:
        tu = get_user(target)
        loot = int(tu["money"] * 0.5)
        add(uid, "money", loot)
        add(tid, "money", -loot)
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            f"Ты забрал своё.\n{get_name(target)} потерял {loot} 💶."
        ))
    else:
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            "Тебя ждали. Люди вернулись ни с чем."
        ))

# =====================================================
# 🧭 МИССИИ
# команда: миссии
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
                message.from_user,
                f"Люди вернутся через {left} ч."
            ))

        cursor.execute("DELETE FROM missions WHERE user_id=?", (uid,))
        conn.commit()

        if random.random() < 0.6:
            reward = random.randint(500, 1500)
            add(uid, "money", reward)
            return bot.reply_to(message, cartel_msg(
                message.from_user,
                f"Дело прошло чисто. +{reward} 💶."
            ))
        else:
            return bot.reply_to(message, cartel_msg(
                message.from_user,
                "Дело сорвалось. Кто-то не вернулся."
            ))

    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role='задания'", (uid,)
    )
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            "Некого отправлять."
        ))

    cursor.execute("""
        INSERT INTO missions (user_id, merc_type, count, start_time)
        VALUES (?, ?, ?, ?)
    """, (uid, row["merc_type"], row["count"], datetime.now().isoformat()))
    conn.commit()

    return bot.reply_to(message, cartel_msg(
        message.from_user,
        "Люди ушли. Вернутся через сутки."
    ))

# =====================================================
# 🧪 АККРЕДИТАЦИЯ (ТЕСТ)
# =====================================================
def accreditation(bot, message, uid, text):
    if uid != ADMIN_ID:
        return
    parts = text.split()
    if len(parts) == 2 and parts[1].isdigit():
        add(uid, "money", int(parts[1]))
        return bot.reply_to(message, cartel_msg(
            message.from_user,
            "Средства выданы."
        ))

# =====================================================
# 🔥 ГЛАВНЫЙ HANDLE (под твой MAIN)
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
# _________________________________________________
# КАРТЕЛИ (создание, ранги, банк, участники)
# _________________________________________________

# =====================================================
# _________________________________________________
# КВ — ВОЙНЫ КАРТЕЛЕЙ
# _________________________________________________

# =====================================================
# _________________________________________________
# КОЛОНИИ И КРЫША
# _________________________________________________