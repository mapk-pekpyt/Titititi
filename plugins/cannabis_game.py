import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name
from plugins import top_plugin

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

# ================== TABLE ==================
cursor.execute("""
CREATE TABLE IF NOT EXISTS cannabis (
    chat_id TEXT,
    user_id TEXT,
    name TEXT,
    coins INTEGER DEFAULT 10,
    bushes INTEGER DEFAULT 0,
    weed INTEGER DEFAULT 0,
    cakes INTEGER DEFAULT 0,
    joints INTEGER DEFAULT 0,
    hunger INTEGER DEFAULT 0,
    last_collect TEXT,
    last_high TEXT,
    PRIMARY KEY (chat_id, user_id)
)
""")
conn.commit()

# ================== HELPERS ==================
def ensure(chat_id, user):
    cursor.execute(
        "INSERT OR IGNORE INTO cannabis(chat_id,user_id,name) VALUES (?,?,?)",
        (str(chat_id), str(user.id), get_name(user))
    )
    cursor.execute(
        "UPDATE cannabis SET name=? WHERE chat_id=? AND user_id=?",
        (get_name(user), str(chat_id), str(user.id))
    )
    conn.commit()

def get(chat_id, user):
    ensure(chat_id, user)
    cursor.execute(
        "SELECT * FROM cannabis WHERE chat_id=? AND user_id=?",
        (str(chat_id), str(user.id))
    )
    return cursor.fetchone()

def cooldown_passed(last_time, hours=1):
    if not last_time:
        return True
    return datetime.now() - datetime.fromisoformat(last_time) >= timedelta(hours=hours)

# ================== GAME ==================
def handle(bot, message):
    chat_id = message.chat.id
    user = message.from_user
    text = (message.text or "").lower().strip()
    name = get_name(user)

    u = get(chat_id, user)

    # -------- БАЛАНС --------
    if text == "баланс":
        return bot.reply_to(
            message,
            f"🌿 {name}\n\n"
            f"💰 Коины: {u[3]}\n"
            f"🌱 Кусты: {u[4]}\n"
            f"🌿 Конопля: {u[5]}\n"
            f"🥮 Кексы: {u[6]}\n"
            f"🚬 Косяки: {u[7]}\n"
            f"❤️ Сытость: {u[8]}"
        )

    # -------- КУПИТЬ КУСТЫ --------
    if text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split()) > 1 else 1
        cost = n * 10

        if u[3] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")

        cursor.execute("""
            UPDATE cannabis
            SET coins = coins - ?, bushes = bushes + ?
            WHERE chat_id=? AND user_id=?
        """, (cost, n, str(chat_id), str(user.id)))
        conn.commit()

        # ⬆️ В ТОП
        top_plugin.update_stat(chat_id, user, "bushes", n)

        return bot.reply_to(message, f"🌱 Куплено {n} кустов")

    # -------- СБОР (РАЗ В ЧАС) --------
    if text == "собрать":
        if not cooldown_passed(u[9]):
            mins = int((timedelta(hours=1) - (datetime.now() - datetime.fromisoformat(u[9]))).seconds / 60)
            return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")

        if u[4] <= 0:
            return bot.reply_to(message, "❌ У тебя нет кустов")

        gain = random.randint(1, u[4])

        cursor.execute("""
            UPDATE cannabis
            SET weed = weed + ?, last_collect=?
            WHERE chat_id=? AND user_id=?
        """, (gain, datetime.now().isoformat(), str(chat_id), str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ ТРАВУ --------
    if text.startswith("продать ") and not text.startswith("продать кексы"):
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет конопли")

        earned = n // 10
        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, coins = coins + ?
            WHERE chat_id=? AND user_id=?
        """, (n, earned, str(chat_id), str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"💰 Продано {n} → +{earned} коинов")

    # -------- КРАФТ КОСЯКОВ --------
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет конопли")

        cursor.execute("""
            UPDATE cannabis
            SET weed = weed - ?, joints = joints + ?
            WHERE chat_id=? AND user_id=?
        """, (n, n, str(chat_id), str(user.id)))
        conn.commit()

        return bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

    # -------- ПОДЫМИТЬ (РАЗ В ЧАС) --------
    if text == "подымить":
        if u[7] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")

        if not cooldown_passed(u[10]):
            mins = int((timedelta(hours=1) - (datetime.now() - datetime.fromisoformat(u[10]))).seconds / 60)
            return bot.reply_to(message, f"⏳ Подожди {mins} мин")

        effect = random.randint(1, 5)

        cursor.execute("""
            UPDATE cannabis
            SET joints=joints-1, last_high=?
            WHERE chat_id=? AND user_id=?
        """, (datetime.now().isoformat(), str(chat_id), str(user.id)))
        conn.commit()

        # ⬆️ В ТОП КАЙФА
        top_plugin.update_stat(chat_id, user, "high", effect)

        return bot.reply_to(message, f"😵‍💫 Кайф +{effect}")