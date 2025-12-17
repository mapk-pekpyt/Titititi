# plugins/top_plugin.py
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.common import get_name, german_date

DB_FILE = "data/data.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# ================== TABLE ==================
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

# ================== CORE ==================
def ensure_user(chat_id, user):
    chat, uid = str(chat_id), str(user.id)
    name = get_name(user)
    cursor.execute(
        "INSERT OR IGNORE INTO users(chat_id, user_id, name) VALUES (?, ?, ?)",
        (chat, uid, name)
    )
    cursor.execute(
        "UPDATE users SET name=? WHERE chat_id=? AND user_id=?",
        (name, chat, uid)
    )
    conn.commit()

def update_stat(chat_id, user, key, delta):
    ensure_user(chat_id, user)
    cursor.execute(
        f"UPDATE users SET {key}={key}+? WHERE chat_id=? AND user_id=?",
        (delta, str(chat_id), str(user.id))
    )
    conn.commit()

def update_date(chat_id, user, key):
    ensure_user(chat_id, user)
    cursor.execute(
        f"UPDATE users SET {key}=? WHERE chat_id=? AND user_id=?",
        (german_date().isoformat(), str(chat_id), str(user.id))
    )
    conn.commit()

def was_today(chat_id, user, key):
    cursor.execute(
        f"SELECT {key} FROM users WHERE chat_id=? AND user_id=?",
        (str(chat_id), str(user.id))
    )
    row = cursor.fetchone()
    return bool(row and row[0] == german_date().isoformat())

def load_users(chat_id):
    cursor.execute(
        "SELECT * FROM users WHERE chat_id=?",
        (str(chat_id),)
    )
    rows = cursor.fetchall()
    data = {}
    for r in rows:
        data[r[1]] = {
            "name": r[2],
            "sisi": r[3],
            "hui": r[4],
            "klitor": r[5],
            "beer": r[6]
        }
    return data

def _fmt_klitor(mm):
    return f"{mm/10:.1f}"

# ================== TOP ==================
def handle(bot, message):
    text = (message.text or "").lower()
    if text.startswith("/top") or text.startswith("топ") or text.startswith("рейтинг"):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🍒 Сиськи", callback_data="top_sisi"),
            InlineKeyboardButton("🍌 Хуй", callback_data="top_hui"),
            InlineKeyboardButton("🍑 Клитор", callback_data="top_klitor"),
            InlineKeyboardButton("🍺 Пиво", callback_data="top_beer")
        )
        bot.send_message(
            message.chat.id,
            "Выбери топ 👇",
            reply_markup=markup
        )
        return

    if text.startswith("/my") or text.startswith("мои"):
        ensure_user(message.chat.id, message.from_user)
        cursor.execute(
            "SELECT sisi,hui,klitor,beer FROM users WHERE chat_id=? AND user_id=?",
            (str(message.chat.id), str(message.from_user.id))
        )
        s, h, k, b = cursor.fetchone()
        bot.reply_to(
            message,
            f"📊 {get_name(message.from_user)}:\n\n"
            f"🍒 Сиськи: {s}\n"
            f"🍌 Хуй: {h} см\n"
            f"🍑 Клитор: {_fmt_klitor(k)} см\n"
            f"🍺 Пиво: {b} л"
        )

def handle_top_callback(bot, call):
    users = load_users(call.message.chat.id)
    if not users:
        bot.answer_callback_query(call.id, "Пусто 😿")
        return

    key_map = {
        "top_sisi": ("🍒 ТОП СИСЕК", "sisi"),
        "top_hui": ("🍌 ТОП ХУЕВ", "hui"),
        "top_klitor": ("🍑 ТОП КЛИТОРОВ", "klitor"),
        "top_beer": ("🍺 ТОП АЛКАШЕЙ", "beer")
    }

    title, key = key_map[call.data]
    top = sorted(users.values(), key=lambda x: x[key], reverse=True)[:5]

    lines = []
    for i, u in enumerate(top, 1):
        val = _fmt_klitor(u[key]) if key == "klitor" else u[key]
        lines.append(f"{i}. {u['name']} — {val}")

    bot.edit_message_text(
        f"{title}\n\n" + "\n".join(lines),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=call.message.reply_markup
    )
    bot.answer_callback_query(call.id)