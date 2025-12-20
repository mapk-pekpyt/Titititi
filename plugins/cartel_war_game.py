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
# НАЁМ
# =====================================================
def hire(bot, message, uid, text):
    parts = text.split()
    user = message.from_user
    name = get_name(user)

    if len(parts) != 4:
        return bot.reply_to(
            message,
            f"{name}, формат:\nнанять <рейд|защита|задания> <гопник|бандит|солдат> <число>"
        )

    role, merc, count = parts[1], parts[2], parts[3]

    if role not in ROLES:
        return bot.reply_to(message, f"{name}, такой роли нет.")
    if merc not in MERC_TYPES:
        return bot.reply_to(message, f"{name}, таких людей нет.")
    if not count.isdigit() or int(count) <= 0:
        return bot.reply_to(message, f"{name}, количество должно быть числом больше 0.")

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

    # 1️⃣ списываем деньги
    add(uid, "money", -cost)

    # 2️⃣ добавляем наёмников (SQLite: исключаем конфликт)
    cursor.execute("""
        INSERT INTO cartel_members (user_id, merc_type, role, count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, merc_type, role)
        DO UPDATE SET count = count + excluded.count
    """, (uid, merc, role, count))
    conn.commit()  # коммитим изменения

    # 3️⃣ перечитываем баланс
    u = get_user(user)

    # 4️⃣ готовый красивый ответ
    return bot.reply_to(
        message,
        f"{name}, сделка прошла успешно!\n"
        f"{count} {merc} теперь в деле.\n"
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
    attacker = message.from_user
    tid = str(message.reply_to_message.from_user.id) if message.reply_to_message else None

    if not tid:
        return bot.reply_to(message, say(attacker, "Рейд — ответом на сообщение цели."))

    if tid == uid:
        return bot.reply_to(message, say(attacker, "Не можешь рейдить себя."))

    # Атакующие
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='рейд'", (uid,))
    atk = cursor.fetchall()
    if not atk:
        return bot.reply_to(message, say(attacker, "У тебя нет бойцов для рейда."))

    # Защитники
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='защита'", (tid,))
    dfn = cursor.fetchall()

    atk_hp, atk_power, atk_units = army_power(atk)
    def_hp, def_power, def_units = army_power(dfn)

    # Время до уничтожения
    atk_time = def_hp / max(atk_power, 1)
    def_time = atk_hp / max(def_power, 1)

    # Потери
    if atk_time < def_time:
        winner = "attacker"
        atk_loss = int(atk_units * random.uniform(0.2, 0.5))
        def_loss = def_units
    else:
        winner = "defender"
        def_loss = int(def_units * random.uniform(0.2, 0.5))
        atk_loss = atk_units

    # Шанс побега половины при поражении
    escaped = False
    if random.random() < 0.5:
        escaped = True
        if winner == "attacker":
            def_loss = int(def_loss * 0.5)
        else:
            atk_loss = int(atk_loss * 0.5)

    remove_units(uid, "рейд", atk_loss)
    remove_units(tid, "защита", def_loss)

    msg = f"Рейд завершён:\n"
    msg += f"Победитель: {'Ты' if winner=='attacker' else 'Противник'}\n"
    msg += f"Твои потери: {atk_loss}\n"
    msg += f"Потери противника: {def_loss}\n"
    if escaped:
        msg += "Часть бойцов сумела сбежать.\n"

    # Лут если победил атакующий
    if winner == "attacker":
        tu = get_user(message.reply_to_message.from_user)
        loot = int(tu["money"] * 0.5)
        add(uid, "money", loot)
        add(tid, "money", -loot)
        msg += f"Забрал {loot} 💶 у цели."

    return bot.reply_to(message, say(attacker, msg))

# =====================================================
# МИССИИ
# =====================================================
def missions(bot, message, uid):
    user = message.from_user

    cursor.execute("SELECT * FROM missions WHERE user_id=?", (uid,))
    m = cursor.fetchone()

    cursor.execute("SELECT * FROM cartel_members WHERE user_id=? AND role='задания'", (uid,))
    rows = cursor.fetchall()
    if not rows:
        return bot.reply_to(message, say(user, "Некого отправлять на задания."))

    units = sum(r["count"] for r in rows)
    success_chance = max(0.15, 0.8 - units * 0.02)

    if m:
        start = datetime.fromisoformat(m["start_time"])
        end = start + timedelta(hours=24)
        if datetime.now() < end:
            hours = int((end - datetime.now()).total_seconds() // 3600)
            return bot.reply_to(message, say(user, f"Люди вернутся через {hours} ч."))

        cursor.execute("DELETE FROM missions WHERE user_id=?", (uid,))
        conn.commit()

        if random.random() < success_chance:
            reward = units * random.randint(200, 400)
            add(uid, "money", reward)
            return bot.reply_to(message, say(user, f"Дело прошло успешно!\nВыручка: {reward} 💶"))
        else:
            loss = int(units * random.uniform(0.3, 0.6))
            remove_units(uid, "задания", loss)
            return bot.reply_to(message, say(user, f"Задание сорвано!\nПотеряно бойцов: {loss}"))

    # Начало миссии
    cursor.execute(
        "INSERT INTO missions (user_id, start_time) VALUES (?, ?)",
        (uid, datetime.now().isoformat())
    )
    conn.commit()
    return bot.reply_to(message, say(user, "Бойцы ушли на задание.\nВернутся через сутки."))

# =====================================================
# АККРЕДИТАЦИЯ
# =====================================================
def accreditation(bot, message, uid, text):
    if uid != ADMIN_ID:
        return

    if not message.reply_to_message:
        return bot.reply_to(message, "Ответом укажи получателя и сумму.")

    target = message.reply_to_message.from_user
    parts = text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return bot.reply_to(message, "Сумма должна быть числом.")

    amount = int(parts[1])
    add(str(target.id), "money", amount)
    return bot.reply_to(message, say(target, f"Получено {amount} 💶"))

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
    if text == "миссии":
        return missions(bot, message, uid)
    if text.startswith("аккредитация"):
        return accreditation(bot, message, uid, text)