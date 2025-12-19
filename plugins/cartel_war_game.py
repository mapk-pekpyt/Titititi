import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name

DB = "data/cartel_game.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ================== БАЗЫ ДАННЫХ ==================
# Игроки и наёмники будут привязаны к канабиз-плагину
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
def ensure_user(user):
    """Подготовка пользователя в системе"""
    # Берем данные из канабиз
    pass  # уже используется через get_user из канабиз

def get_cartel(user_id):
    cursor.execute("SELECT * FROM cartel_members WHERE user_id=?", (user_id,))
    return cursor.fetchone()

def add_money(user_id, amount):
    """Добавление евриков игроку через канабиз"""
    from plugins.cannabis_game import add  # используем функцию add
    add(user_id, "money", amount)

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

# ================== СТИЛЬ СООБЩЕНИЙ ==================
def cartel_msg(title, text):
    return f"💣 {title} 💣\n{text}"

def mission_msg(user, merc_type, count, reward, success):
    if success:
        return f"🚀 {user} успешно выполнил миссию с {count} {merc_type}, получил {reward} 💶"
    else:
        return f"💀 {user} провалил миссию с {count} {merc_type}, ничего не получил, часть выживших вернулась"

# ================== ОСНОВНОЙ ОБРАБОТЧИК ==================
def handle(bot, message):
    user = message.from_user
    text = (message.text or "").lower().strip()
    uid = str(user.id)
    u = get_user(user)  # функция из канабиз

    # Здесь будет блок команд наёмников
    # Здесь будет блок команд картеля
    # Здесь будет блок миссий
    # Здесь будет блок рейдов
    # Здесь будет блок КВ
    # Здесь будет блок управления членами (посвятить, окрестить, обесценить, отречь, возвысить)
    # Здесь будет блок наградить

    # Шаблон ответа
    # return bot.reply_to(message, cartel_msg("Название", "Текст"))

# ================== КОНЕЦ ШАПКИ ==================