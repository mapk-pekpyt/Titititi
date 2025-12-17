# plugins/cannabis_game.py
import sqlite3, random
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from plugins.common import get_name, german_date

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

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
    high INTEGER DEFAULT 0,
    last_collect TEXT,
    last_smoke TEXT,
    PRIMARY KEY (chat_id, user_id)
)
""")
conn.commit()

def ensure(chat, user):
    cursor.execute(
        "INSERT OR IGNORE INTO cannabis(chat_id,user_id,name) VALUES (?,?,?)",
        (str(chat), str(user.id), get_name(user))
    )
    conn.commit()

def handle(bot, message):
    chat = message.chat.id
    user = message.from_user
    name = get_name(user)
    text = (message.text or "").lower().strip()
    ensure(chat, user)

    cursor.execute(
        "SELECT * FROM cannabis WHERE chat_id=? AND user_id=?",
        (str(chat), str(user.id))
    )
    u = cursor.fetchone()
    now = datetime.now()

    if text == "баланс":
        bot.reply_to(
            message,
            f"🌿 {name}:\n"
            f"💰 Коины: {u[3]}\n"
            f"🌱 Кусты: {u[4]}\n"
            f"🌿 Конопля: {u[5]}\n"
            f"🥮 Кексы: {u[6]}\n"
            f"🚬 Косяки: {u[7]}\n"
            f"❤️ Сытость: {u[8]}\n"
            f"😵‍💫 Кайф: {u[9]}"
        )

    if text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split()) > 1 else 1
        cost = n * 10
        if u[3] < cost:
            return bot.reply_to(message, "❌ Нищета")
        cursor.execute(
            "UPDATE cannabis SET coins=coins-?, bushes=bushes+? WHERE chat_id=? AND user_id=?",
            (cost, n, str(chat), str(user.id))
        )
        conn.commit()
        bot.reply_to(message, f"🌱 Купил {n} кустов")

    if text == "подымить":
        if u[7] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        effect = random.randint(-5, 5)
        cursor.execute(
            "UPDATE cannabis SET joints=joints-1, high=high+?, last_smoke=? WHERE chat_id=? AND user_id=?",
            (effect, german_date().isoformat(), str(chat), str(user.id))
        )
        conn.commit()

        if effect > 0:
            msg = f"😵‍💫 {name}, ты кайфанул 🔥 Кайф +{effect}"
        elif effect < 0:
            msg = f"🤢 {name}, ты подавился 🤮 Кайф {effect}"
        else:
            msg = f"😐 {name}, вообще никак"

        bot.reply_to(message, msg)