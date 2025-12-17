import sqlite3
import os
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
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
    bushes INTEGER DEFAULT 0,
    high INTEGER DEFAULT 0,
    full INTEGER DEFAULT 0,
    msg_count INTEGER DEFAULT 0,
    last_sisi TEXT,
    last_hui TEXT,
    last_klitor TEXT,
    last_beer TEXT,
    last_high TEXT,
    PRIMARY KEY (chat_id, user_id)
)
""")
conn.commit()

# =========================
# ФАЙЛЫ ПАМЯТИ КАНАБИЗ
# =========================
def _cfile(chat_id):
    return f"data/игра_{chat_id}.json"

def load_cannabis(chat_id):
    f = _cfile(chat_id)
    if not os.path.exists(f):
        return {}
    try:
        with open(f, "r", encoding="utf8") as file:
            return json.load(file)
    except:
        return {}

# =========================
# ОБЩИЕ ФУНКЦИИ
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
            "bushes": r[7],
            "high": r[8],
            "full": r[9],
            "msg_count": r[10],
            "last_sisi": r[11],
            "last_hui": r[12],
            "last_klitor": r[13],
            "last_beer": r[14],
            "last_high": r[15],
        }

    # подтягиваем данные из канабиза
    cdata = load_cannabis(chat_id)
    for uid, u in users.items():
        if uid in cdata:
            u["bushes"] = cdata[uid].get("кусты", u.get("bushes",0))
            u["high"] = cdata[uid].get("кайф", u.get("high",0))
            u["full"] = cdata[uid].get("сытость", u.get("full",0))
    return users

def _format_klitor(mm: int):
    return f"{mm / 10:.1f}"

# =========================
# ТОП С КНОПКАМИ
# =========================
def handle_top(bot, message):
    chat_id = str(message.chat.id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🍒 Сисечки", callback_data="top_sisi"),
        InlineKeyboardButton("🍌 Хуй", callback_data="top_hui"),
        InlineKeyboardButton("🍑 Клитор", callback_data="top_klitor"),
        InlineKeyboardButton("🍺 Пиво", callback_data="top_beer"),
        InlineKeyboardButton("🌱 Кусты", callback_data="top_bushes"),
        InlineKeyboardButton("😵 Кайф", callback_data="top_high"),
        InlineKeyboardButton("❤️ Сытость", callback_data="top_full"),
        InlineKeyboardButton("💬 Общение", callback_data="top_msg")
    )
    bot.send_message(chat_id, "Выбери топ, который хочешь посмотреть:", reply_markup=markup)

def handle_top_callback(bot, call):
    chat_id = str(call.message.chat.id)
    users = load_users(chat_id)
    if not users:
        return bot.answer_callback_query(call.id, "Никто ещё не играл 😿")

    key_map = {
        "top_sisi": ("🏆 Топ сисечек:", "🍒", "sisi"),
        "top_hui": ("🍌 Топ достоинств:", "🍌", "hui"),
        "top_klitor": ("🍑 Топ клиторов:", "🍑", "klitor"),
        "top_beer": ("🍺 Топ алкашей:", "🍺", "beer"),
        "top_bushes": ("🌱 Топ кустов:", "🌱", "bushes"),
        "top_high": ("😵 Топ кайфа:", "😵", "high"),
        "top_full": ("❤️ Топ сытости:", "❤️", "full"),
        "top_msg": ("💬 Топ общения:", "💬", "msg_count")
    }

    if call.data not in key_map:
        return

    title, emoji, key = key_map[call.data]
    top_list = sorted(users.values(), key=lambda x: x.get(key,0), reverse=True)[:10]

    if key == "klitor":
        text = f"{title}\n" + "\n".join(f"{i+1}. {u['name']} — {_format_klitor(u[key])} см {emoji}" for i,u in enumerate(top_list))
    else:
        text = f"{title}\n" + "\n".join(f"{i+1}. {u['name']} — {u[key]} {emoji}" for i,u in enumerate(top_list))

    bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id)

# =========================
# МОЙ ТОП
# =========================
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
        f"🍺 Выпито пива: {u[6]} л\n"
        f"🌱 Кусты: {u[7]}\n"
        f"😵 Кайф: {u[8]}\n"
        f"❤️ Сытость: {u[9]}\n"
        f"💬 Сообщений: {u[10]}"
    )
    bot.reply_to(message, txt)

# =========================
# ОБЩИЙ ОБРАБОТЧИК ТОПА
# =========================
def handle(bot, message):
    text = (message.text or "").lower()
    if text.startswith("/top") or text.startswith("топ") or text.startswith("рейтинг"):
        handle_top(bot, message)
    elif text.startswith("/my") or text.startswith("мои размеры") or text.startswith("мои"):
        handle_my(bot, message)

# =========================
# СЧЁТЧИК СООБЩЕНИЙ
# =========================
def count_message(chat_id, user):
    ensure_user(chat_id, user)
    cursor.execute("UPDATE users SET msg_count = msg_count + 1 WHERE chat_id=? AND user_id=?", (str(chat_id), str(user.id)))
    conn.commit()