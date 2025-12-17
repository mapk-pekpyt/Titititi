import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.common import get_name

DB_FILE = "data/data.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# =========================
# Создаём таблицу пользователей
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
    balance INTEGER DEFAULT 0,
    keksy INTEGER DEFAULT 0,
    cannabis INTEGER DEFAULT 0,
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
# БАЗОВЫЕ ФУНКЦИИ
# =========================
def ensure_user(chat_id, user):
    chat, uid = str(chat_id), str(user.id)
    name = get_name(user)
    cursor.execute(
        "INSERT OR IGNORE INTO users(chat_id, user_id, name) VALUES (?, ?, ?)",
        (chat, uid, name)
    )
    cursor.execute("UPDATE users SET name=? WHERE chat_id=? AND user_id=?", (name, chat, uid))
    conn.commit()

def update_stat(chat_id, user, key, delta):
    ensure_user(chat_id, user)
    chat, uid = str(chat_id), str(user.id)
    cursor.execute(f"UPDATE users SET {key} = {key} + ? WHERE chat_id=? AND user_id=?", (delta, chat, uid))
    conn.commit()

def load_users(chat_id):
    chat = str(chat_id)
    cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat,))
    rows = cursor.fetchall()
    users = {}
    for r in rows:
        users[r[1]] = {
            "name": r[2],
            "sisi": r[3] or 0,
            "hui": r[4] or 0,
            "klitor": r[5] or 0,
            "beer": r[6] or 0,
            "bushes": r[7] or 0,
            "high": r[8] or 0,
            "full": r[9] or 0,
            "msg_count": r[10] or 0,
            "balance": r[11] or 0,
            "keksy": r[12] or 0,
            "cannabis": r[13] or 0
        }
    return users

def _format_klitor(mm: int):
    return f"{mm / 10:.1f}"

# =========================
# ТОП-КНОПКИ
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
        InlineKeyboardButton("💬 Общение", callback_data="top_msg"),
        InlineKeyboardButton("💰 Баланс", callback_data="top_balance"),
        InlineKeyboardButton("🧁 Кексы", callback_data="top_keksy"),
        InlineKeyboardButton("🌿 Канабис", callback_data="top_cannabis")
    )
    bot.send_message(chat_id, "Выбери топ, который хочешь посмотреть:", reply_markup=markup)

# =========================
# ОБРАБОТКА CALLBACK
# =========================
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
        "top_msg": ("💬 Топ общения:", "💬", "msg_count"),
        "top_balance": ("💰 Топ денег:", "💰", "balance"),
        "top_keksy": ("🧁 Топ кексов:", "🧁", "keksy"),
        "top_cannabis": ("🌿 Топ травы:", "🌿", "cannabis"),
    }

    if call.data not in key_map:
        return

    title, emoji, key = key_map[call.data]
    top_list = sorted(users.values(), key=lambda x: x.get(key, 0), reverse=True)[:10]

    if key == "klitor":
        text = f"{title}\n" + "\n".join(
            f"{i+1}. {u['name']} — {_format_klitor(u[key])} см {emoji}" for i, u in enumerate(top_list)
        )
    else:
        text = f"{title}\n" + "\n".join(
            f"{i+1}. {u['name']} — {u[key]} {emoji}" for i, u in enumerate(top_list)
        )

    bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id)

# =========================
# МОЙ ТОП (/my)
# =========================
def handle_my(bot, message):
    chat_id = str(message.chat.id)
    user = message.from_user
    ensure_user(chat_id, user)
    uid = str(user.id)

    cursor.execute("SELECT * FROM users WHERE chat_id=? AND user_id=?", (chat_id, uid))
    u = cursor.fetchone()
    txt = (
        f"📊 {u[2]}, твои размеры:\n\n"
        f"🍒 Сисечки: {u[3]}\n"
        f"🍌 Хуй: {u[4]} см\n"
        f"🍑 Клитор: {_format_klitor(u[5])} см\n"
        f"🍺 Выпито пива: {u[6]}\n"
        f"🌱 Кусты: {u[7]}\n"
        f"😵 Кайф: {u[8]}\n"
        f"❤️ Сытость: {u[9]}\n"
        f"💬 Сообщений: {u[10]}\n"
        f"💰 Баланс: {u[11]}\n"
        f"🧁 Кексы: {u[12]}\n"
        f"🌿 Канабис: {u[13]}"
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
    cursor.execute(
        "UPDATE users SET msg_count = msg_count + 1 WHERE chat_id=? AND user_id=?",
        (str(chat_id), str(user.id))
    )
    conn.commit()