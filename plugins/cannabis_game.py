import sqlite3, random
from datetime import datetime, timedelta
from plugins.common import get_name

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
    high INTEGER DEFAULT 0,
    last_collect TEXT,
    last_high TEXT,
    PRIMARY KEY (chat_id, user_id)
)
""")
conn.commit()

# ================== HELPERS ==================
def ensure(chat, user):
    cursor.execute(
        "INSERT OR IGNORE INTO cannabis(chat_id,user_id,name) VALUES (?,?,?)",
        (str(chat), str(user.id), get_name(user))
    )
    cursor.execute(
        "UPDATE cannabis SET name=? WHERE chat_id=? AND user_id=?",
        (get_name(user), str(chat), str(user.id))
    )
    conn.commit()

def get(chat, user):
    ensure(chat, user)
    cursor.execute(
        "SELECT * FROM cannabis WHERE chat_id=? AND user_id=?",
        (str(chat), str(user.id))
    )
    return cursor.fetchone()

# ================== GAME ==================
def handle(bot, message):
    chat = message.chat.id
    user = message.from_user
    name = get_name(user)
    text = (message.text or "").lower().strip()
    now = datetime.now()

    u = get(chat, user)

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
            f"❤️ Сытость: {u[8]}\n"
            f"😵‍💫 Кайф: {u[9]}"
        )

    # -------- КУПИТЬ --------
    if text.startswith("купить"):
        n = int(text.split()[1]) if len(text.split()) > 1 else 1
        cost = n * 10
        if u[3] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")
        cursor.execute(
            "UPDATE cannabis SET coins=coins-?, bushes=bushes+? WHERE chat_id=? AND user_id=?",
            (cost, n, str(chat), str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} коинов")

    # -------- СОБРАТЬ --------
    if text == "собрать":
        if u[10]:
            last = datetime.fromisoformat(u[10])
            if now - last < timedelta(hours=1):
                mins = int((timedelta(hours=1)-(now-last)).seconds/60)
                return bot.reply_to(message, f"⏳ Рано, подожди {mins} мин")
        gain = random.randint(0, u[4])
        cursor.execute(
            "UPDATE cannabis SET weed=weed+?, last_collect=? WHERE chat_id=? AND user_id=?",
            (gain, now.isoformat(), str(chat), str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"🌿 Собрано {gain} конопли")

    # -------- ПРОДАТЬ --------
    if text.startswith("продать ") and not text.startswith("продать кексы"):
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        earned = n // 10
        cursor.execute(
            "UPDATE cannabis SET weed=weed-?, coins=coins+? WHERE chat_id=? AND user_id=?",
            (n, earned, str(chat), str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"💰 Продал {n} → +{earned} коинов")

    # -------- ИСПЕЧЬ --------
    if text.startswith("испечь"):
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        burned = 0
        baked = 0
        for _ in range(n):
            if random.random() < 0.3:
                burned += 1
            else:
                baked += 1
        cursor.execute(
            "UPDATE cannabis SET weed=weed-?, cakes=cakes+? WHERE chat_id=? AND user_id=?",
            (n, baked, str(chat), str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"🥮 Испёк {baked}, 🔥 сгорело {burned}")

    # -------- СЪЕСТЬ --------
    if text.startswith("съесть"):
        n = int(text.split()[1])
        if u[6] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        cursor.execute(
            "UPDATE cannabis SET cakes=cakes-?, hunger=hunger+? WHERE chat_id=? AND user_id=?",
            (n, n, str(chat), str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # -------- ПРОДАТЬ КЕКСЫ --------
    if text.startswith("продать кексы"):
        n = int(text.split()[2])
        if u[6] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        earned = n // 5
        cursor.execute(
            "UPDATE cannabis SET cakes=cakes-?, coins=coins+? WHERE chat_id=? AND user_id=?",
            (n, earned, str(chat), str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"💰 Продал {n} кексов → +{earned} коинов")

    # -------- КРАФТ --------
    if text.startswith("крафт"):
        n = int(text.split()[1])
        if u[5] < n:
            return bot.reply_to(message, "❌ Нет конопли")
        cursor.execute(
            "UPDATE cannabis SET weed=weed-?, joints=joints+? WHERE chat_id=? AND user_id=?",
            (n, n, str(chat), str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"🚬 Скрафтил {n} косяков")

    # -------- ПОДЫМИТЬ --------
    if text == "подымить":
        if u[7] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")
        if u[11]:
            last = datetime.fromisoformat(u[11])
            if now - last < timedelta(hours=1):
                mins = int((timedelta(hours=1)-(now-last)).seconds/60)
                return bot.reply_to(message, f"⏳ Подожди {mins} мин")

        effect = random.choice([-5,-3,-2,-1,0,1,2,3,4,5])
        cursor.execute(
            "UPDATE cannabis SET joints=joints-1, high=high+?, last_high=? WHERE chat_id=? AND user_id=?",
            (effect, now.isoformat(), str(chat), str(user.id))
        )
        conn.commit()

        if effect > 0:
            return bot.reply_to(message, f"🔥 Ты кайфанул 😵‍💫\nКайф +{effect}")
        elif effect < 0:
            return bot.reply_to(message, f"🤢 Ты подавился\nКайф {effect}")
        else:
            return bot.reply_to(message, "😐 Ни рыба ни мясо")