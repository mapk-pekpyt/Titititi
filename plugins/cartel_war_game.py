import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name
from plugins import cannabis_game  # берём баланс и функцию add

DB = "data/cartel_game.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ================== БАЗЫ ДАННЫХ ==================
# Наёмники пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS cartel_members (
    user_id TEXT,
    merc_type TEXT,
    role TEXT,
    count INTEGER DEFAULT 0,
    PRIMARY KEY(user_id, merc_type, role)
)
""")
conn.commit()

# ================== ХЕЛПЕРЫ ==================
def get_user(user):
    """Берём данные пользователя из канабиза"""
    return cannabis_game.get_user(user)

def add_money(user_id, amount):
    """Добавление евриков через канабиз"""
    cannabis_game.add(user_id, "money", amount)

def money_word(n):
    if n % 10 == 1 and n % 100 != 11:
        return "еврик"
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "еврика"
    return "евриков"

# ================== СООБЩЕНИЯ ==================
def cartel_msg(title, text):
    return f"💣 {title} 💣\n{text}"

# ================== НАЁМНИКИ ==================
MERC_TYPES = {
    "гопник": {"hp": 100, "attack": 20, "cost": 500},
    "бандит": {"hp": 150, "attack": 40, "cost": 750},
    "солдат": {"hp": 350, "attack": 70, "cost": 1000},
}

ROLES = ["защита", "рейд", "задания"]

def hire_merc(bot, message, uid, u, text):
    parts = text.split()
    if len(parts) != 4:
        return bot.reply_to(message, "❌ Пример: нанять защита гопник 5")

    role, merc_type, count = parts[1], parts[2], parts[3]

    if role not in ROLES:
        return bot.reply_to(message, f"❌ Роль неверна. Выбери: {', '.join(ROLES)}")
    if merc_type not in MERC_TYPES:
        return bot.reply_to(message, f"❌ Тип неверен. Доступные: {', '.join(MERC_TYPES.keys())}")
    if not count.isdigit():
        return bot.reply_to(message, "❌ Количество должно быть числом")

    count = int(count)
    cost = MERC_TYPES[merc_type]["cost"] * count
    if u["money"] < cost:
        return bot.reply_to(message, f"❌ Не хватает {cost - u['money']} {money_word(cost - u['money'])}")

    # Списываем деньги
    add_money(uid, -cost)

    # Добавляем наёмников
    cursor.execute("""
        INSERT INTO cartel_members (user_id, merc_type, role, count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, merc_type, role) DO UPDATE SET count=count+?
    """, (uid, merc_type, role, count, count))
    conn.commit()

    return bot.reply_to(message, f"💀 Нанято {count} {merc_type} для {role} за {cost} {money_word(cost)}")

def show_mercs(bot, message, uid):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        return bot.reply_to(message, "🤷‍♂️ У тебя пока нет наёмников")

    msg = "💣 Отряды наёмников 💣\n"
    for row in rows:
        msg += f"• {row['merc_type'].capitalize()} | Роль: {row['role']} | Кол-во: {row['count']}\n"

    return bot.reply_to(message, msg)

def handle_mercs(bot, message, uid, u, text):
    if text.startswith("нанять"):
        return hire_merc(bot, message, uid, u, text)
    if text == "отряд":
        return show_mercs(bot, message, uid)

# ================== ОБЩИЙ HANDLE ==================
def handle(bot, message):
    uid = str(message.from_user.id)
    u = get_user(message.from_user)
    text = (message.text or "").lower().strip()

    # ---------- НАЁМНИКИ ----------
    if text.startswith("нанять") or text == "отряд":
        return handle_mercs(bot, message, uid, u, text)

    # ---------- ЗДЕСЬ БУДУТ БЛОКИ: рейды, миссии, картель, награды ----------