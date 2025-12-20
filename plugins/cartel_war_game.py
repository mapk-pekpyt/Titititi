import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name
from plugins.cannabis_game import get_user, add  # используем существующий канабиз

DB = "data/cartel_game.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ================== БАЗЫ ДАННЫХ ==================
cursor.execute("""
CREATE TABLE IF NOT EXISTS cartel_members (
    cartel_id INTEGER,
    user_id TEXT,
    rank TEXT DEFAULT 'новичок',
    role TEXT DEFAULT 'защита',
    merc_type TEXT,
    count INTEGER DEFAULT 0,
    PRIMARY KEY(cartel_id, user_id, merc_type, role)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS cartels (
    cartel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    boss_id TEXT,
    bank INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS missions (
    mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    merc_type TEXT,
    role TEXT,
    count INTEGER,
    start_time TEXT,
    duration_hours INTEGER,
    reward INTEGER,
    success INTEGER DEFAULT 0
)
""")
conn.commit()

# ================== ХЕЛПЕРЫ ==================
def cooldown(last_time, hours=1):
    if not last_time:
        return True
    return datetime.now() - datetime.fromisoformat(last_time) >= timedelta(hours=hours)

def money_word(n):
    if n % 10 == 1 and n % 100 != 11:
        return "еврик"
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "еврика"
    return "евриков"

def cartel_msg(title, text):
    return f"💣 {title} 💣\n{text}"

# ================== НАЕМНИКИ ==================
MERC_TYPES = {
    "гопник": {"hp": 100, "attack": 20, "cost": 500},
    "бандит": {"hp": 150, "attack": 40, "cost": 750},
    "солдат": {"hp": 350, "attack": 70, "cost": 1000},
}

ROLES = ["защита", "рейд", "задания"]

# ---------- НАЙМ НАЕМНИКОВ ----------
def hire_merc(bot, message, uid, u, text):
    parts = text.split()
    if len(parts) != 4:
        return bot.reply_to(message, "❌ Пример: нанять защита гопник 5")

    role, merc_type, count = parts[1], parts[2], parts[3]
    if role not in ROLES:
        return bot.reply_to(message, f"❌ Неверная роль. Выбери: {', '.join(ROLES)}")

    if merc_type not in MERC_TYPES:
        return bot.reply_to(message, f"❌ Неверный тип наемника. Доступные: {', '.join(MERC_TYPES.keys())}")

    if not count.isdigit():
        return bot.reply_to(message, "❌ Количество должно быть числом")

    count = int(count)
    cost = MERC_TYPES[merc_type]["cost"] * count

    if u["money"] < cost:
        return bot.reply_to(message, f"❌ Не хватает {cost - u['money']} {money_word(cost - u['money'])}")

    # Списание денег через канабиз
    add(uid, "money", -cost)

    # Вставка или обновление наемников
    cursor.execute(
        "INSERT INTO cartel_members (user_id, merc_type, role, count) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(user_id, merc_type, role) DO UPDATE SET count=count+?",
        (uid, merc_type, role, count, count)
    )
    conn.commit()

    return bot.reply_to(message, f"💀 Нанято {count} {merc_type} для {role} за {cost} {money_word(cost)}")

# ---------- ПОКАЗАТЬ ОТРЯД НАЕМНИКОВ ----------
def show_mercs(bot, message, uid):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        return bot.reply_to(message, "🤷‍♂️ У тебя пока нет наемников")

    msg = "💣 Отряды наемников 💣\n"
    for row in rows:
        msg += f"• {row['merc_type'].capitalize()} | Роль: {row['role']} | Кол-во: {row['count']}\n"

    return bot.reply_to(message, msg)

# ================== ОБРАБОТКА КОМАНД НАЕМНИКОВ ==================
def handle_mercs(bot, message, uid, u, text):
    if text.startswith("нанять"):
        return hire_merc(bot, message, uid, u, text)

    if text == "отряд":
        return show_mercs(bot, message, uid)