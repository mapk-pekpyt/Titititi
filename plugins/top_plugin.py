# plugins/db_top_plugin.py
import sqlite3
import datetime
from plugins.common import get_name, german_date

DB_FILE = "data/data.db"

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# =========================
# Создаем таблицу пользователей
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id TEXT,
    user_id TEXT,
    name TEXT,
    sisi INTEGER DEFAULT 0,
    hui INTEGER DEFAULT 0,
    klitor INTEGER DEFAULT 0,
    beer INTEGER DEFAULT 0,
    last_sisi TEXT,
    last_hui TEXT,
    last_klitor TEXT,
    last_beer TEXT,
    PRIMARY KEY (chat_id, user_id)
)
""")
conn.commit()


# =========================
# Основные функции
# =========================

def ensure_user(chat_id, user):
    chat, uid = str(chat_id), str(user.id)
    name = get_name(user)
    cursor.execute("INSERT OR IGNORE INTO users(chat_id, user_id, name) VALUES (?, ?, ?)",
                   (chat, uid, name))
    cursor.execute("UPDATE users SET name=? WHERE chat_id=? AND user_id=?", (name, chat, uid))
    conn.commit()


def update_stat(chat_id, user, key, delta):
    chat, uid = str(chat_id), str(user.id)
    ensure_user(chat_id, user)
    cursor.execute(f"UPDATE users SET {key} = {key} + ? WHERE chat_id=? AND user_id=?", (delta, chat, uid))
    conn.commit()


def update_date(chat_id, user, key):
    chat, uid = str(chat_id), str(user.id)
    ensure_user(chat_id, user)
    cursor.execute(f"UPDATE users SET {key} = ? WHERE chat_id=? AND user_id=?", (german_date().isoformat(), chat, uid))
    conn.commit()


def was_today(chat_id, user, key):
    chat, uid = str(chat_id), str(user.id)
    cursor.execute(f"SELECT {key} FROM users WHERE chat_id=? AND user_id=?", (chat, uid))
    row = cursor.fetchone()
    if not row or not row[0]:
        return False
    return row[0] == german_date().isoformat()


def load_users(chat_id):
    chat = str(chat_id)
    cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat,))
    rows = cursor.fetchall()
    users = {}
    for r in rows:
        users[r[1]] = {
            "name": r[2],
            "sisi": r[3],
            "hui": r[4],
            "klitor": r[5],
            "beer": r[6],
            "last_sisi": r[7],
            "last_hui": r[8],
            "last_klitor": r[9],
            "last_beer": r[10],
        }
    return users


def _format_klitor(mm: int):
    return f"{mm / 10:.1f}"


# =========================
# ТОПЫ
# =========================

def handle_top(bot, message):
    chat_id = str(message.chat.id)
    users = load_users(chat_id)
    if not users:
        return bot.reply_to(message, "Никто ещё не играл 😿")

    # Топ сисек
    sisi_list = sorted(users.values(), key=lambda x: x.get("sisi",0), reverse=True)[:3]
    txt1 = "🏆 Топ сисечек:\n" + "\n".join(f"{i+1}. {u['name']} — {u['sisi']} размер 🍒" for i,u in enumerate(sisi_list))

    # Топ хуев
    hui_list = sorted(users.values(), key=lambda x: x.get("hui",0), reverse=True)[:3]
    txt2 = "🍌 Топ достоинств:\n" + "\n".join(f"{i+1}. {u['name']} — {u['hui']} см 🍌" for i,u in enumerate(hui_list))

    # Топ клиторов
    klit_list = sorted(users.values(), key=lambda x: x.get("klitor",0), reverse=True)[:3]
    txt3 = "🍑 Топ клиторов:\n" + "\n".join(f"{i+1}. {u['name']} — {_format_klitor(u['klitor'])} см 🍑" for i,u in enumerate(klit_list))

    # Топ алкашей
    beer_list = sorted(users.values(), key=lambda x: x.get("beer",0), reverse=True)[:3]
    txt4 = "🍺 Топ алкашей:\n" + "\n".join(f"{i+1}. {u['name']} — {u.get('beer',0)} л 🍺" for i,u in enumerate(beer_list))

    for txt in (txt1, txt2, txt3, txt4):
        bot.reply_to(message, txt)


def handle_my(bot, message):
    chat_id = str(message.chat.id)
    user = message.from_user
    uid = str(user.id)
    ensure_user(chat_id, user)

    cursor.execute("SELECT * FROM users WHERE chat_id=? AND user_id=?", (chat_id, uid))
    u = cursor.fetchone()

    txt = (
        f"📊 {u[2]}, твои размеры:\n\n"
        f"🍒 Сисечки: {u[3]} размера\n"
        f"🍌 Хуй: {u[4]} см\n"
        f"🍑 Клитор: {_format_klitor(u[5])} см\n"
        f"🍺 Выпито пива: {u[6]} л"
    )
    bot.reply_to(message, txt)


def handle(bot, message):
    text = (message.text or "").lower()
    if text.startswith("/top") or text.startswith("топ") or text.startswith("рейтинг"):
        handle_top(bot, message)
    elif text.startswith("/my") or text.startswith("мои размеры") or text.startswith("мои"):
        handle_my(bot, message)