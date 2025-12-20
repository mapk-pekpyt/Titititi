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
# 👥 НАЙМ НАЁМНИКОВ
# команда: нанять <роль> <тип> <кол-во>
# =====================================================
def hire(bot, message, uid, u, text):
    parts = text.split()
    name = get_name(message.from_user)

    if len(parts) != 4:
        return bot.reply_to(
            message,
            f"{name}, говори чётко.\n"
            f"Нанять <защита|рейд|задания> <гопник|бандит|солдат> <число>"
        )

    role, merc, count = parts[1], parts[2], parts[3]

    if role not in ROLES:
        return bot.reply_to(
            message,
            f"{name}, такой роли у семьи нет.\n"
            f"Доступно: защита, рейд, задания."
        )

    if merc not in MERC_TYPES:
        return bot.reply_to(
            message,
            f"{name}, таких людей мне не приводят."
        )

    if not count.isdigit() or int(count) <= 0:
        return bot.reply_to(
            message,
            f"{name}, количество должно быть числом."
        )

    count = int(count)
    cost = MERC_TYPES[merc]["cost"] * count

    if u["money"] < cost:
        need = cost - u["money"]
        can = u["money"] // MERC_TYPES[merc]["cost"]
        return bot.reply_to(
            message,
            f"{name}, ты пришёл в мой дом нанимать моих людей,\n"
            f"но не взял денег.\n\n"
            f"Не хватает {need} 💶.\n"
            f"Максимум, кого ты можешь нанять — {can}."
        )

    # списываем деньги
    add(uid, "money", -cost)

    # проверяем, есть ли уже такие наёмники
    cursor.execute(
        "SELECT count FROM cartel_members WHERE user_id=? AND merc_type=? AND role=?",
        (uid, merc, role)
    )
    row = cursor.fetchone()

    if row:
        cursor.execute(
            "UPDATE cartel_members SET count = count + ? "
            "WHERE user_id=? AND merc_type=? AND role=?",
            (count, uid, merc, role)
        )
    else:
        cursor.execute(
            "INSERT INTO cartel_members (user_id, merc_type, role, count) "
            "VALUES (?, ?, ?, ?)",
            (uid, merc, role, count)
        )

    conn.commit()

    remaining = u["money"] - cost

    return bot.reply_to(
        message,
        f"{name}, сделка состоялась.\n\n"
        f"Ты нанял {count} {merc}.\n"
        f"Их роль — {role}.\n\n"
        f"Относись к ним с уважением.\n"
        f"У тебя осталось {remaining} 💶."
    )

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
    attacker = message.from_user
    aname = get_name(attacker)

    if not message.reply_to_message:
        return bot.reply_to(
            message,
            f"{aname}, рейды делаются ответом на сообщение."
        )

    target = message.reply_to_message.from_user
    tid = str(target.id)
    tname = get_name(target)

    # атакующие
    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role='рейд'",
        (uid,)
    )
    atk = cursor.fetchall()

    if not atk:
        return bot.reply_to(
            message,
            f"{aname}, тебе некого отправлять в бой."
        )

    # защитники
    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role='защита'",
        (tid,)
    )
    dfn = cursor.fetchall()

    atk_power = sum(MERC_TYPES[a["merc_type"]]["attack"] * a["count"] for a in atk)
    def_power = sum(MERC_TYPES[d["merc_type"]]["attack"] * d["count"] for d in dfn)

    atk_loss = int(sum(a["count"] for a in atk) * random.uniform(0.1, 0.4))
    def_loss = int(sum(d["count"] for d in dfn) * random.uniform(0.2, 0.6))

    # списываем потери
    for a in atk:
        lost = min(a["count"], max(0, atk_loss))
        cursor.execute(
            "UPDATE cartel_members SET count = count - ? "
            "WHERE user_id=? AND merc_type=? AND role='рейд'",
            (lost, uid, a["merc_type"])
        )

    for d in dfn:
        lost = min(d["count"], max(0, def_loss))
        cursor.execute(
            "UPDATE cartel_members SET count = count - ? "
            "WHERE user_id=? AND merc_type=? AND role='защита'",
            (lost, tid, d["merc_type"])
        )

    conn.commit()

    if atk_power > def_power:
        tu = get_user(target)
        loot = int(tu["money"] * 0.5)
        add(uid, "money", loot)
        add(tid, "money", -loot)

        return bot.reply_to(
            message,
            f"{aname}, дело сделано.\n\n"
            f"Ты забрал у {tname} {loot} 💶.\n\n"
            f"Твои потери: {atk_loss}\n"
            f"Потери противника: {def_loss}"
        )

    return bot.reply_to(
        message,
        f"{aname}, тебя ждали.\n\n"
        f"Твои потери: {atk_loss}\n"
        f"Потери противника: {def_loss}\n\n"
        f"Добычи нет."
    )

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