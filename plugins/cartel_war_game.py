import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name
from plugins import cannabis_game

DB = "data/cartel_game.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ================== БАЗЫ ДАННЫХ ==================
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
    return cannabis_game.get_user(user)

def add_money(user_id, amount):
    cannabis_game.add(user_id, "money", amount)

def money_word(n):
    if n % 10 == 1 and n % 100 != 11:
        return "еврик"
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "еврика"
    return "евриков"

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

    # Добавляем или обновляем наёмников корректно
    cursor.execute("SELECT count FROM cartel_members WHERE user_id=? AND merc_type=? AND role=?",
                   (uid, merc_type, role))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE cartel_members SET count=count+? WHERE user_id=? AND merc_type=? AND role=?",
                       (count, uid, merc_type, role))
    else:
        cursor.execute("INSERT INTO cartel_members (user_id, merc_type, role, count) VALUES (?, ?, ?, ?)",
                       (uid, merc_type, role, count))
    conn.commit()

    return bot.reply_to(message, cartel_msg("Крестный отец говорит:",
                                            f"Ты нанял {count} {merc_type} для {role}. Заплати {cost} {money_word(cost)}"))

def show_mercs(bot, message, uid):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (uid,))
    rows = cursor.fetchall()
    if not rows:
        return bot.reply_to(message, cartel_msg("Крестный отец", "У тебя пока нет наёмников"))

    msg = "💣 Твои отряды 💣\n"
    for row in rows:
        msg += f"• {row['merc_type'].capitalize()} | Роль: {row['role']} | Кол-во: {row['count']}\n"
    return bot.reply_to(message, cartel_msg("Крестный отец", msg))

# ================== РЕЙД ==================
def raid(bot, message, uid, u, text):
    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        # случайный противник для теста
        return bot.reply_to(message, cartel_msg("Крестный отец", "❌ Укажи игрока через ответ на сообщение"))

    target_uid = str(target_user.id)
    target_data = get_user(target_user)
    if not target_data:
        return bot.reply_to(message, cartel_msg("Крестный отец", "❌ Игрок не найден"))

    # Подсчёт силы твоих наёмников для рейда
    cursor.execute("SELECT merc_type, count FROM cartel_members WHERE user_id=? AND role='рейд'", (uid,))
    mercs = cursor.fetchall()
    if not mercs:
        return bot.reply_to(message, cartel_msg("Крестный отец", "❌ У тебя нет наёмников для рейда"))

    your_power = sum(MERC_TYPES[m['merc_type']]['attack'] * m['count'] for m in mercs)

    # Сила противника — грубая имитация, все роли и типы суммируются
    cursor.execute("SELECT merc_type, count FROM cartel_members WHERE user_id=?", (target_uid,))
    target_mercs = cursor.fetchall()
    target_power = sum(MERC_TYPES[m['merc_type']]['attack'] * m['count'] for m in target_mercs)

    # Битва
    if your_power > target_power:
        gain = int(target_data["money"] * 0.5)
        add_money(uid, gain)
        return bot.reply_to(message, cartel_msg("Крестный отец",
                                                f"🏆 Ты победил игрока {target_user.first_name} и забрал {gain} 💶"))
    else:
        return bot.reply_to(message, cartel_msg("Крестный отец",
                                                f"💀 Рейд провален. Игрок {target_user.first_name} сильнее"))

# ================== ОБЩИЙ HANDLE ==================
def handle(bot, message):
    uid = str(message.from_user.id)
    u = get_user(message.from_user)
    text = (message.text or "").lower().strip()

    if text.startswith("нанять") or text == "отряд":
        return handle_mercs(bot, message, uid, u, text)

    if text.startswith("рейд"):
        return raid(bot, message, uid, u, text)

def handle_mercs(bot, message, uid, u, text):
    if text.startswith("нанять"):
        return hire_merc(bot, message, uid, u, text)
    if text == "отряд":
        return show_mercs(bot, message, uid)