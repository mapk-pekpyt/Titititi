import sqlite3, random
from datetime import datetime, timedelta
from plugins.common import get_name

DB = "data/data.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row

# ================== TABLE ==================
with conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS cannabis (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        money INTEGER DEFAULT 1000,
        bushes INTEGER DEFAULT 0,
        weed INTEGER DEFAULT 0,
        cakes INTEGER DEFAULT 0,
        joints INTEGER DEFAULT 0,
        last_collect TEXT,
        last_smoke TEXT
    )
    """)

# ================== HELPERS ==================
def get_user(user):
    uid = str(user.id)
    name = get_name(user)
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO cannabis(user_id,name) VALUES (?,?)",
            (uid, name)
        )
        conn.execute(
            "UPDATE cannabis SET name=? WHERE user_id=?",
            (name, uid)
        )
    return conn.execute(
        "SELECT * FROM cannabis WHERE user_id=?",
        (uid,)
    ).fetchone()

def hours_passed(last, h=1):
    if not last:
        return True
    return datetime.now() - datetime.fromisoformat(last) >= timedelta(hours=h)

# ================== GAME ==================
def handle(bot, message):
    try:
        user = message.from_user
        text = (message.text or "").lower().strip()
        cmd = text.split()[0]
        args = text.split()[1:]
        u = get_user(user)

        # ===== БАЛАНС =====
        if cmd == "баланс":
            bot.reply_to(message,
                f"🌿 {u['name']}\n\n"
                f"💶 Еврейчики: {u['money']}\n"
                f"🌱 Кусты: {u['bushes']}\n"
                f"🌿 Конопля: {u['weed']}\n"
                f"🥮 Кексы: {u['cakes']}\n"
                f"🚬 Косяки: {u['joints']}"
            )
            return

        # ===== КУПИТЬ =====
        if cmd == "купить":
            n = int(args[0]) if args else 1
            cost = n * 10
            if n <= 0 or u["money"] < cost:
                bot.reply_to(message, "❌ Не хватает еврейчиков")
                return
            with conn:
                conn.execute(
                    "UPDATE cannabis SET money=money-?, bushes=bushes+? WHERE user_id=?",
                    (cost, n, u["user_id"])
                )
            bot.reply_to(message, f"🌱 Куплено {n} кустов за {cost} 💶")
            return

        # ===== СОБРАТЬ =====
        if cmd == "собрать":
            if not hours_passed(u["last_collect"]):
                bot.reply_to(message, "⏳ Рано, подожди час")
                return
            if u["bushes"] <= 0:
                bot.reply_to(message, "❌ Нет кустов")
                return
            gain = random.randint(1, u["bushes"])
            with conn:
                conn.execute(
                    "UPDATE cannabis SET weed=weed+?, last_collect=? WHERE user_id=?",
                    (gain, datetime.now().isoformat(), u["user_id"])
                )
            bot.reply_to(message, f"🌿 Собрано {gain} конопли")
            return

        # ===== ПРОДАТЬ =====
        if cmd == "продать":
            n = int(args[0])
            if n <= 0 or u["weed"] < n:
                bot.reply_to(message, "❌ Нечего продавать")
                return
            money = n * 1
            with conn:
                conn.execute(
                    "UPDATE cannabis SET weed=weed-?, money=money+? WHERE user_id=?",
                    (n, money, u["user_id"])
                )
            bot.reply_to(message, f"💶 Продано {n} → +{money} еврейчиков")
            return

        # ===== КРАФТ =====
        if cmd == "крафт":
            n = int(args[0])
            if n <= 0 or u["weed"] < n:
                bot.reply_to(message, "❌ Нет конопли")
                return
            success = sum(1 for _ in range(n) if random.random() > 0.4)
            with conn:
                conn.execute(
                    "UPDATE cannabis SET weed=weed-?, joints=joints+? WHERE user_id=?",
                    (n, success, u["user_id"])
                )
            bot.reply_to(message, f"🚬 Скрутил {success}, остальное рассыпалось")
            return

        # ===== ДУНУТЬ =====
        if cmd == "дунуть":
            if u["joints"] <= 0:
                bot.reply_to(message, "❌ Нет косяков")
                return
            if not hours_passed(u["last_smoke"]):
                bot.reply_to(message, "⏳ Передышка нужна")
                return
            text = random.choice([
                "😵‍💫 улетел красиво",
                "🤢 подавился дымом",
                "😐 ни о чём"
            ])
            with conn:
                conn.execute(
                    "UPDATE cannabis SET joints=joints-1, last_smoke=? WHERE user_id=?",
                    (datetime.now().isoformat(), u["user_id"])
                )
            bot.reply_to(message, text)
            return

    except Exception as e:
        print("CANNABIS ERROR:", e)