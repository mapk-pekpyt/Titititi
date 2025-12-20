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
# БАЗА ДАННЫХ
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

def army_stats(rows):
    hp = atk = units = 0
    for r in rows:
        s = MERC_TYPES[r["merc_type"]]
        hp += s["hp"] * r["count"]
        atk += s["attack"] * r["count"]
        units += r["count"]
    return hp, atk, units

def remove_units(user_id, role, loss):
    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role=? AND count>0",
        (user_id, role)
    )
    rows = cursor.fetchall()
    left = loss

    for r in rows:
        if left <= 0:
            break
        dead = min(r["count"], left)
        left -= dead
        cursor.execute("""
            UPDATE cartel_members
            SET count = count - ?
            WHERE user_id=? AND merc_type=? AND role=?
        """, (dead, user_id, r["merc_type"], role))

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
            f"{name}, формат:\n"
            f"нанять <рейд|защита|задания> <гопник|бандит|солдат> <число>"
        )

    role, merc, count = parts[1], parts[2], parts[3]

    if role not in ROLES or merc not in MERC_TYPES or not count.isdigit():
        return bot.reply_to(message, f"{name}, команда неверная.")

    count = int(count)
    if count <= 0:
        return bot.reply_to(message, f"{name}, количество должно быть больше нуля.")

    cost = MERC_TYPES[merc]["cost"] * count
    u = get_user(user)

    if u["money"] < cost:
        return bot.reply_to(
            message,
            f"{name}, денег не хватает.\n"
            f"Нужно {cost}, у тебя {u['money']}."
        )

    # === 1️⃣ СПИСЫВАЕМ ДЕНЬГИ ===
    add(uid, "money", -cost)

    # === 2️⃣ ОБЯЗАТЕЛЬНО перечитываем пользователя ===
    u = get_user(user)

    # === 3️⃣ ДОБАВЛЯЕМ НАЁМНИКОВ ===
    cursor.execute("""
        INSERT INTO cartel_members (user_id, merc_type, role, count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, merc_type, role)
        DO UPDATE SET count = count + ?
    """, (uid, merc, role, count, count))
    conn.commit()

    # === 4️⃣ ОТВЕТ ===
    return bot.reply_to(
        message,
        f"{name}, сделка прошла.\n"
        f"{count} {merc} в деле.\n"
        f"Назначение: {role}.\n"
        f"Осталось денег: {u['money']} 💶"
    )
# =====================================================
# ОТРЯДЫ
# =====================================================
def squads(bot, message, uid):
    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND count>0",
        (uid,)
    )
    rows = cursor.fetchall()
    if not rows:
        return bot.reply_to(message, say(message.from_user, "У тебя пока пусто."))

    out = ""
    for role in ROLES:
        block = [r for r in rows if r["role"] == role]
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
    attacker = message.from_user
    name = get_name(attacker)

    if not message.reply_to_message:
        return bot.reply_to(message, say(attacker, "Рейд делается ответом на сообщение."))

    target = message.reply_to_message.from_user
    tid = str(target.id)

    if tid == uid or target.is_bot:
        return bot.reply_to(message, say(attacker, "Ты не можешь атаковать это."))

    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role='рейд' AND count>0",
        (uid,)
    )
    atk_rows = cursor.fetchall()
    if not atk_rows:
        return bot.reply_to(message, say(attacker, "Некого отправлять."))

    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role='защита' AND count>0",
        (tid,)
    )
    def_rows = cursor.fetchall()

    atk_hp, atk_atk, atk_units = army_stats(atk_rows)
    def_hp, def_atk, def_units = army_stats(def_rows)

    if atk_atk <= 0:
        return bot.reply_to(message, say(attacker, "Твои люди не готовы к бою."))

    atk_time = def_hp / atk_atk if def_hp > 0 else 0
    def_time = atk_hp / def_atk if def_atk > 0 else float("inf")

    report = ""

    if atk_time < def_time:
        # победа
        loss_atk = int(atk_units * random.uniform(0.2, 0.4))
        loss_def = def_units

        remove_units(uid, "рейд", loss_atk)
        remove_units(tid, "защита", loss_def)

        loot = int(get_user(target)["money"] * random.uniform(0.2, 0.4))
        if loot > 0:
            add(uid, "money", loot)
            add(tid, "money", -loot)

        report = (
            f"Ты продавил оборону.\n"
            f"Потери твоих: {loss_atk}\n"
            f"Потери врага: {loss_def}\n"
            f"Добыча: {loot} 💶"
        )
    else:
        # поражение
        loss_atk = int(atk_units * random.uniform(0.4, 0.7))
        remove_units(uid, "рейд", loss_atk)

        # 50% шанс побега половины
        if random.random() < 0.5:
            saved = loss_atk // 2
            report = (
                f"Ты не дожал.\n"
                f"Потери: {loss_atk}\n"
                f"Часть людей ушла живыми: {saved}"
            )
        else:
            report = (
                f"Засада.\n"
                f"Потери: {loss_atk}\n"
                f"Никто не успел уйти."
            )

    return bot.reply_to(message, say(attacker, report))

# =====================================================
# МИССИИ
# =====================================================
def missions(bot, message, uid):
    user = message.from_user
    name = get_name(user)

    cursor.execute("SELECT * FROM missions WHERE user_id=?", (uid,))
    m = cursor.fetchone()

    if m:
        start = datetime.fromisoformat(m["start_time"])
        end = start + timedelta(hours=24)

        if datetime.now() < end:
            hours = int((end - datetime.now()).total_seconds() // 3600)
            return bot.reply_to(message, say(user, f"Люди вернутся через {hours} ч."))

        cursor.execute("DELETE FROM missions WHERE user_id=?", (uid,))
        conn.commit()

        cursor.execute(
            "SELECT * FROM cartel_members WHERE user_id=? AND role='задания' AND count>0",
            (uid,)
        )
        rows = cursor.fetchall()
        units = sum(r["count"] for r in rows)

        success = max(0.15, 0.8 - units * 0.02)

        if random.random() < success:
            reward = units * random.randint(200, 400)
            add(uid, "money", reward)
            return bot.reply_to(
                message,
                say(user, f"Дело прошло.\nВыручка: {reward} 💶")
            )
        else:
            loss = int(units * random.uniform(0.3, 0.6))
            remove_units(uid, "задания", loss)
            return bot.reply_to(
                message,
                say(user, f"Дело накрылось.\nПотери: {loss}")
            )

    cursor.execute(
        "SELECT * FROM cartel_members WHERE user_id=? AND role='задания' AND count>0",
        (uid,)
    )
    if not cursor.fetchone():
        return bot.reply_to(message, say(user, "Некого отправлять."))

    cursor.execute(
        "INSERT INTO missions (user_id, start_time) VALUES (?, ?)",
        (uid, datetime.now().isoformat())
    )
    conn.commit()

    return bot.reply_to(
        message,
        say(user, "Люди ушли на дело. Вернутся через сутки.")
    )

# =====================================================
# АККРЕДИТАЦИЯ
# =====================================================
def accreditation(bot, message, uid, text):
    if uid != ADMIN_ID:
        return

    parts = text.split()
    if not message.reply_to_message or len(parts) != 2 or not parts[1].isdigit():
        return bot.reply_to(message, "Ответом на сообщение + сумма.")

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
    if text == "миссия":
        return missions(bot, message, uid)
    if text.startswith("аккредитация"):
        return accreditation(bot, message, uid, text)

# =====================================================
# ____ БЛОК: КАРТЕЛИ (будущее)
# =====================================================

# =====================================================
# ____ БЛОК: ВОЙНЫ КАРТЕЛЕЙ
# =====================================================

# =====================================================
# ____ БЛОК: КРЫША / БИЗНЕС
# =====================================================