import sqlite3
import random
from datetime import datetime, timedelta
from plugins.common import get_name

DB_FILE = "data/data.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# =====================================================
# ТАБЛИЦЫ
# =====================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    coins INTEGER DEFAULT 1000,
    bushes INTEGER DEFAULT 0,
    weed INTEGER DEFAULT 0,
    cakes INTEGER DEFAULT 0,
    joints INTEGER DEFAULT 0,
    hunger INTEGER DEFAULT 10,
    high INTEGER DEFAULT 0,
    last_collect TEXT,
    last_eat TEXT,
    last_smoke TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS merc_groups (
    user_id TEXT,
    type TEXT,
    level INTEGER,
    count INTEGER,
    hp INTEGER,
    PRIMARY KEY (user_id, type, level)
)
""")

conn.commit()

# =====================================================
# ХЕЛПЕРЫ
# =====================================================

def now():
    return datetime.utcnow()

def ensure_player(user):
    cursor.execute(
        "INSERT OR IGNORE INTO players(user_id, name) VALUES (?,?)",
        (str(user.id), get_name(user))
    )
    cursor.execute(
        "UPDATE players SET name=? WHERE user_id=?",
        (get_name(user), str(user.id))
    )
    conn.commit()

def get_player(user):
    ensure_player(user)
    cursor.execute("SELECT * FROM players WHERE user_id=?", (str(user.id),))
    return cursor.fetchone()

def can_do(last_time, minutes=60):
    if not last_time:
        return True
    return now() - datetime.fromisoformat(last_time) >= timedelta(minutes=minutes)

def set_time(user_id, field):
    cursor.execute(
        f"UPDATE players SET {field}=? WHERE user_id=?",
        (now().isoformat(), user_id)
    )
    conn.commit()

# =====================================================
# ЭКОНОМИКА
# =====================================================

BUSH_PRICE = 10          # коинов
WEED_SELL = 10           # 10 травы = 1 коин
CAKE_SELL = 5            # 5 кексов = 1 коин
JOINT_SELL = 2           # 1 косяк = 2 коина

# =====================================================
# ОСНОВНОЙ HANDLE
# =====================================================

def handle(bot, message):
    if not message.text:
        return

    text = message.text.lower().strip()
    user = message.from_user
    ensure_player(user)
    p = get_player(user)

    # -------------------------------------------------
    # БАЛАНС
    # -------------------------------------------------
    if text == "баланс":
        return bot.reply_to(
            message,
            f"🌿 {p[1]}\n\n"
            f"💰 Коины: {p[2]}\n"
            f"🌱 Кусты: {p[3]}\n"
            f"🌿 Трава: {p[4]}\n"
            f"🥮 Кексы: {p[5]}\n"
            f"🚬 Косяки: {p[6]}\n"
            f"❤️ Сытость: {p[7]}\n"
            f"😵 Кайф: {p[8]}"
        )

    # -------------------------------------------------
    # КУПИТЬ КУСТЫ
    # -------------------------------------------------
    if text.startswith("купить куст"):
        try:
            n = int(text.split()[-1])
        except:
            n = 1

        cost = n * BUSH_PRICE
        if p[2] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")

        cursor.execute(
            "UPDATE players SET coins=coins-?, bushes=bushes+? WHERE user_id=?",
            (cost, n, str(user.id))
        )
        conn.commit()
        return bot.reply_to(
            message,
            f"🌱 Куплено кустов: {n}\n💸 Потрачено: {cost}"
        )

    # -------------------------------------------------
    # СБОР УРОЖАЯ (1 РАЗ В ЧАС)
    # -------------------------------------------------
    if text == "собрать":
        if not can_do(p[9], 60):
            return bot.reply_to(message, "⏳ Урожай ещё не вырос")

        if p[3] <= 0:
            return bot.reply_to(message, "❌ У тебя нет кустов")

        gain = random.randint(p[3], p[3] * 3)
        cursor.execute(
            "UPDATE players SET weed=weed+? WHERE user_id=?",
            (gain, str(user.id))
        )
        set_time(str(user.id), "last_collect")

        return bot.reply_to(
            message,
            f"🌿 Ты собрал {gain} травы"
        )

    # -------------------------------------------------
    # ПРОДАТЬ
    # -------------------------------------------------
    if text.startswith("продать траву"):
        try:
            n = int(text.split()[-1])
        except:
            return bot.reply_to(message, "❌ Укажи количество")

        if p[4] < n:
            return bot.reply_to(message, "❌ Недостаточно травы")

        coins = n // WEED_SELL
        cursor.execute(
            "UPDATE players SET weed=weed-?, coins=coins+? WHERE user_id=?",
            (n, coins, str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"💰 +{coins} коинов")

    if text.startswith("продать кексы"):
        n = int(text.split()[-1])
        if p[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")
        coins = n // CAKE_SELL
        cursor.execute(
            "UPDATE players SET cakes=cakes-?, coins=coins+? WHERE user_id=?",
            (n, coins, str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"💰 +{coins} коинов")

    if text.startswith("продать косяки"):
        n = int(text.split()[-1])
        if p[6] < n:
            return bot.reply_to(message, "❌ Нет косяков")
        coins = n * JOINT_SELL
        cursor.execute(
            "UPDATE players SET joints=joints-?, coins=coins+? WHERE user_id=?",
            (n, coins, str(user.id))
        )
        conn.commit()
        return bot.reply_to(message, f"💰 +{coins} коинов")

    # -------------------------------------------------
    # СЪЕСТЬ КЕКС (1 РАЗ В ЧАС)
    # -------------------------------------------------
    if text.startswith("съесть"):
        if not can_do(p[10], 60):
            return bot.reply_to(message, "⏳ Желудок ещё занят")

        try:
            n = int(text.split()[-1])
        except:
            n = 1

        if p[5] < n:
            return bot.reply_to(message, "❌ Нет кексов")

        cursor.execute(
            "UPDATE players SET cakes=cakes-?, hunger=hunger+? WHERE user_id=?",
            (n, n, str(user.id))
        )
        set_time(str(user.id), "last_eat")
        return bot.reply_to(message, f"❤️ Сытость +{n}")

    # -------------------------------------------------
    # ДУНУТЬ (1 РАЗ В ЧАС)
    # -------------------------------------------------
    if text == "дунуть":
        if not can_do(p[11], 60):
            return bot.reply_to(message, "⏳ Лёгкие ещё не отошли")

        if p[6] <= 0:
            return bot.reply_to(message, "❌ Нет косяков")

        effect = random.randint(1, 5)
        cursor.execute(
            "UPDATE players SET joints=joints-1, high=high+? WHERE user_id=?",
            (effect, str(user.id))
        )
        set_time(str(user.id), "last_smoke")
        return bot.reply_to(
            message,
            f"😵‍💫 Ты дунул\nКайф +{effect}"
        )
        # =====================================================
# ЧАСТЬ 2 — НАЁМНИКИ, АРМИЯ, ТРЕНИРОВКА, БОИ, ДИВЕРСИИ
# =====================================================

# ТИПЫ НАЁМНИКОВ
MERC_TYPES = {
    "гопник":  {"hp": 100, "price": 50},
    "солдат":  {"hp": 200, "price": 120},
    "элита":   {"hp": 400, "price": 300},
}

MAX_LEVEL = 15
TRAIN_PRICE = 40        # коинов за тренировку 1 юнита
DIVERSION_PRICE = 200   # коинов
RAID_COOLDOWN = 30      # минут

# =====================================================
# АРМИЯ — ХЕЛПЕРЫ
# =====================================================

def get_groups(user_id):
    cursor.execute(
        "SELECT type, level, count, hp FROM merc_groups WHERE user_id=? ORDER BY type, level",
        (user_id,)
    )
    return cursor.fetchall()

def total_army_power(user_id):
    groups = get_groups(user_id)
    power = 0
    for g in groups:
        power += g[1] * g[2] * 10
    return power

def merge_groups(user_id, mtype, level):
    cursor.execute(
        """
        SELECT SUM(count), SUM(hp)
        FROM merc_groups
        WHERE user_id=? AND type=? AND level=?
        """,
        (user_id, mtype, level)
    )
    row = cursor.fetchone()
    if row and row[0]:
        cursor.execute(
            "DELETE FROM merc_groups WHERE user_id=? AND type=? AND level=?",
            (user_id, mtype, level)
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO merc_groups(user_id,type,level,count,hp)
            VALUES (?,?,?,?,?)
            """,
            (user_id, mtype, level, row[0], row[1])
        )
        conn.commit()

# =====================================================
# РАСШИРЕНИЕ HANDLE
# =====================================================

def handle(bot, message):
    if not message.text:
        return

    text = message.text.lower().strip()
    user = message.from_user
    ensure_player(user)
    p = get_player(user)
    uid = str(user.id)

    # -------------------------------------------------
    # НАЁМНИКИ — СПИСОК
    # -------------------------------------------------
    if text == "наемники":
        groups = get_groups(uid)
        if not groups:
            return bot.reply_to(message, "🪖 У тебя нет армии")

        msg = "🪖 Твоя армия:\n\n"
        for g in groups:
            msg += f"• {g[0].title()} | Ур. {g[1]} | x{g[2]} | ❤️ {g[3]}\n"
        msg += f"\n⚔️ Общая сила: {total_army_power(uid)}"
        return bot.reply_to(message, msg)

    # -------------------------------------------------
    # НАНЯТЬ
    # -------------------------------------------------
    if text.startswith("нанять"):
        parts = text.split()
        if len(parts) < 2:
            return bot.reply_to(message, "❌ Пример: нанять гопник 3")

        mtype = parts[1]
        count = int(parts[2]) if len(parts) > 2 else 1

        if mtype not in MERC_TYPES:
            return bot.reply_to(message, "❌ Нет такого типа")

        price = MERC_TYPES[mtype]["price"] * count
        if p[2] < price:
            return bot.reply_to(message, "❌ Не хватает коинов")

        base_hp = MERC_TYPES[mtype]["hp"] * count

        cursor.execute(
            "INSERT OR IGNORE INTO merc_groups VALUES (?,?,?,?,?)",
            (uid, mtype, 1, 0, 0)
        )
        cursor.execute(
            """
            UPDATE merc_groups
            SET count=count+?, hp=hp+?
            WHERE user_id=? AND type=? AND level=1
            """,
            (count, base_hp, uid, mtype)
        )
        cursor.execute(
            "UPDATE players SET coins=coins-? WHERE user_id=?",
            (price, uid)
        )
        conn.commit()
        merge_groups(uid, mtype, 1)

        return bot.reply_to(
            message,
            f"🪖 Нанято: {count} {mtype}\n💸 Потрачено: {price}"
        )

    # -------------------------------------------------
    # ТРЕНИРОВКА
    # -------------------------------------------------
    if text.startswith("тренировать"):
        parts = text.split()
        if len(parts) < 3:
            return bot.reply_to(message, "❌ Пример: тренировать гопник 1")

        mtype = parts[1]
        level = int(parts[2])

        cursor.execute(
            """
            SELECT count, hp FROM merc_groups
            WHERE user_id=? AND type=? AND level=?
            """,
            (uid, mtype, level)
        )
        row = cursor.fetchone()
        if not row:
            return bot.reply_to(message, "❌ Такой группы нет")

        if level >= MAX_LEVEL:
            return bot.reply_to(message, "🚫 Максимальный уровень")

        cost = row[0] * TRAIN_PRICE
        if p[2] < cost:
            return bot.reply_to(message, "❌ Не хватает коинов")

        cursor.execute(
            "DELETE FROM merc_groups WHERE user_id=? AND type=? AND level=?",
            (uid, mtype, level)
        )
        cursor.execute(
            "INSERT OR IGNORE INTO merc_groups VALUES (?,?,?,?,?)",
            (uid, mtype, level + 1, row[0], row[1] + row[0] * 20)
        )
        cursor.execute(
            "UPDATE players SET coins=coins-? WHERE user_id=?",
            (cost, uid)
        )
        conn.commit()
        merge_groups(uid, mtype, level + 1)

        return bot.reply_to(
            message,
            f"📈 {mtype.title()} повышены до {level+1}\n💸 Потрачено: {cost}"
        )

    # -------------------------------------------------
    # ДИВЕРСИЯ (УРОН АРМИИ)
    # -------------------------------------------------
    if text.startswith("диверсия"):
        if p[2] < DIVERSION_PRICE:
            return bot.reply_to(message, "❌ Не хватает коинов")

        cursor.execute(
            "SELECT user_id FROM merc_groups WHERE user_id!=? ORDER BY RANDOM() LIMIT 1",
            (uid,)
        )
        target = cursor.fetchone()
        if not target:
            return bot.reply_to(message, "❌ Целей нет")

        target_id = target[0]

        cursor.execute(
            """
            UPDATE merc_groups
            SET hp = CAST(hp * 0.7 AS INT)
            WHERE user_id=?
            """,
            (target_id,)
        )
        cursor.execute(
            "UPDATE players SET coins=coins-? WHERE user_id=?",
            (DIVERSION_PRICE, uid)
        )
        conn.commit()

        return bot.reply_to(
            message,
            "🔥 Диверсия успешна!\n⚔️ Армия врага ослаблена"
        )

    # -------------------------------------------------
    # РЕЙД (РАНДОМНЫЙ)
    # -------------------------------------------------
    if text == "рейд":
        cursor.execute(
            "SELECT user_id FROM players WHERE user_id!=? ORDER BY RANDOM() LIMIT 1",
            (uid,)
        )
        enemy = cursor.fetchone()
        if not enemy:
            return bot.reply_to(message, "❌ Нет врагов")

        enemy_id = enemy[0]
        my_power = total_army_power(uid)
        enemy_power = total_army_power(enemy_id)

        if my_power <= 0:
            return bot.reply_to(message, "❌ У тебя нет армии")

        if my_power >= enemy_power:
            steal = max(1, p[3] // 10)
            cursor.execute(
                "UPDATE players SET bushes=bushes+? WHERE user_id=?",
                (steal, uid)
            )
            cursor.execute(
                "UPDATE players SET bushes=bushes-? WHERE user_id=?",
                (steal, enemy_id)
            )
            conn.commit()
            return bot.reply_to(message, f"⚔️ Победа!\n🌱 Украдено кустов: {steal}")
        else:
            loss = max(1, p[3] // 2)
            cursor.execute(
                "UPDATE players SET bushes=bushes-? WHERE user_id=?",
                (loss, uid)
            )
            conn.commit()
            return bot.reply_to(
                message,
                f"💀 Поражение\n🌱 Потеряно кустов: {loss}"
            )
            # =====================================================
# ЧАСТЬ 3 — КЛАНЫ, БАНК, КВ, КЛАНОВАЯ АРМИЯ, ТОПЫ
# =====================================================

# =====================================================
# КОНСТАНТЫ КЛАНОВ
# =====================================================
CLAN_CREATE_PRICE = 500
CLAN_TAX = 0.10          # 10% в банк (НЕ вычитается у игрока)
CLAN_WAR_SHARE_WIN = 0.20
CLAN_WAR_BANK_WIN = 0.40
CLAN_WAR_LOSS_PLAYER = 0.40
CLAN_WAR_LOSS_BANK = 0.50

# =====================================================
# КЛАН — ХЕЛПЕРЫ
# =====================================================

def get_clan(user_id):
    cursor.execute("""
        SELECT c.id, c.name, m.role
        FROM clans c
        JOIN clan_members m ON c.id=m.clan_id
        WHERE m.user_id=?
    """, (user_id,))
    return cursor.fetchone()

def clan_power(clan_id):
    cursor.execute(
        "SELECT SUM(level*count*10) FROM clan_army WHERE clan_id=?",
        (clan_id,)
    )
    return cursor.fetchone()[0] or 0

def clan_add_bank(clan_id, amount):
    cursor.execute(
        "UPDATE clans SET bank=bank+? WHERE id=?",
        (amount, clan_id)
    )

# =====================================================
# ДОБАВКА К HANDLE
# =====================================================

def handle(bot, message):
    if not message.text:
        return

    text = message.text.lower().strip()
    user = message.from_user
    ensure_player(user)
    uid = str(user.id)
    clan = get_clan(uid)

    # -------------------------------------------------
    # СОЗДАТЬ КЛАН
    # -------------------------------------------------
    if text.startswith("клан создать"):
        name = message.text[12:].strip()
        if not name:
            return bot.reply_to(message, "❌ Укажи название")

        cursor.execute("SELECT coins FROM players WHERE user_id=?", (uid,))
        coins = cursor.fetchone()[0]
        if coins < CLAN_CREATE_PRICE:
            return bot.reply_to(message, "❌ Не хватает коинов")

        cursor.execute("INSERT INTO clans(name, bank) VALUES (?,0)", (name,))
        clan_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO clan_members VALUES (?,?,?)",
            (clan_id, uid, "leader")
        )
        cursor.execute(
            "UPDATE players SET coins=coins-? WHERE user_id=?",
            (CLAN_CREATE_PRICE, uid)
        )
        conn.commit()

        return bot.reply_to(message, f"🏴 Клан «{name}» создан!")

    # -------------------------------------------------
    # ВСТУПИТЬ В КЛАН
    # -------------------------------------------------
    if text == "кв+":
        cursor.execute("SELECT id FROM clans ORDER BY RANDOM() LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return bot.reply_to(message, "❌ Кланов нет")

        cursor.execute(
            "INSERT OR IGNORE INTO clan_members VALUES (?,?,?)",
            (row[0], uid, "member")
        )
        conn.commit()
        return bot.reply_to(message, "✅ Ты вступил в клан")

    # -------------------------------------------------
    # ВЫДАТЬ РЕСУРС (ЛИДЕР)
    # -------------------------------------------------
    if text.startswith("клан выдать"):
        if not clan or clan[2] != "leader":
            return bot.reply_to(message, "❌ Только лидер")

        parts = text.split()
        if len(parts) < 4:
            return bot.reply_to(message, "❌ клан выдать 10 кексы")

        amount = int(parts[2])
        resource = parts[3]

        if not message.reply_to_message:
            return bot.reply_to(message, "❌ Ответь на сообщение")

        target_id = str(message.reply_to_message.from_user.id)

        cursor.execute(
            f"UPDATE players SET {resource}={resource}+? WHERE user_id=?",
            (amount, target_id)
        )
        conn.commit()
        return bot.reply_to(message, "🎁 Ресурс выдан")

    # -------------------------------------------------
    # КЛАН — ИНФО
    # -------------------------------------------------
    if text == "клан":
        if not clan:
            return bot.reply_to(message, "❌ Ты не в клане")

        cursor.execute(
            "SELECT name, bank FROM clans WHERE id=?",
            (clan[0],)
        )
        c = cursor.fetchone()
        return bot.reply_to(
            message,
            f"🏴 Клан: {c[0]}\n💰 Банк: {c[1]}\n⚔️ Сила: {clan_power(clan[0])}"
        )

    # -------------------------------------------------
    # КЛАНОВАЯ АРМИЯ (ПОКАЗ)
    # -------------------------------------------------
    if text == "клан армия":
        if not clan:
            return bot.reply_to(message, "❌ Ты не в клане")

        cursor.execute(
            "SELECT type, level, count, hp FROM clan_army WHERE clan_id=?",
            (clan[0],)
        )
        rows = cursor.fetchall()
        if not rows:
            return bot.reply_to(message, "🪖 У клана нет армии")

        msg = "🪖 Клановая армия:\n\n"
        for r in rows:
            msg += f"• {r[0]} | Ур {r[1]} | x{r[2]} | ❤️ {r[3]}\n"
        msg += f"\n⚔️ Общая сила: {clan_power(clan[0])}"
        return bot.reply_to(message, msg)

    # -------------------------------------------------
    # КВ — ЗАПУСК (ВОСКРЕСЕНЬЕ 19:00 CET — логика подготовлена)
    # -------------------------------------------------
    if text == "кв начать":
        if not clan or clan[2] not in ("leader", "co"):
            return bot.reply_to(message, "❌ Нет прав")

        cursor.execute(
            """
            SELECT id FROM clans
            WHERE id!=?
            ORDER BY ABS(
                (SELECT SUM(level*count*10) FROM clan_army WHERE clan_id=clans.id)
                -
                (SELECT SUM(level*count*10) FROM clan_army WHERE clan_id=?)
            )
            LIMIT 1
            """,
            (clan[0], clan[0])
        )
        enemy = cursor.fetchone()
        if not enemy:
            return bot.reply_to(message, "❌ Нет противников")

        my_p = clan_power(clan[0])
        en_p = clan_power(enemy[0])

        if my_p >= en_p:
            cursor.execute(
                "UPDATE clans SET bank=bank*? WHERE id=?",
                (1 + CLAN_WAR_BANK_WIN, clan[0])
            )
            cursor.execute(
                "UPDATE clans SET bank=bank*? WHERE id=?",
                (1 - CLAN_WAR_LOSS_BANK, enemy[0])
            )
            conn.commit()
            return bot.reply_to(message, "🏆 Победа в КВ!")
        else:
            cursor.execute(
                "UPDATE clans SET bank=bank*? WHERE id=?",
                (1 - CLAN_WAR_LOSS_BANK, clan[0])
            )
            conn.commit()
            return bot.reply_to(message, "💀 Поражение в КВ")

# =====================================================
# КОНЕЦ ПЛАГИНА
# =====================================================