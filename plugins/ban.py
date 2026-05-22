import os
import json
from datetime import datetime, timedelta
from telebot.types import LabeledPrice

DATA_DIR = "data"
PRICE_FILE = f"{DATA_DIR}/prices.json"
SHIELD_FILE = f"{DATA_DIR}/shields.json"

ADMIN_ID = 5791171535
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

# ================= PRICES =================
DEFAULT = {
    "kick": 1,
    "ban": 3,
    "ban_hour": 2,
    "unban": 20,
    "shield": 5
}

# ================= FILES =================
def ensure():
    os.makedirs(DATA_DIR, exist_ok=True)

def load(path, default):
    ensure()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default.copy()

def save(path, data):
    ensure()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)

def prices():
    return load(PRICE_FILE, DEFAULT)

def save_prices(p):
    save(PRICE_FILE, p)

def shields():
    return load(SHIELD_FILE, {})

def save_shields(s):
    save(SHIELD_FILE, s)

# ================= HELPERS =================
def norm(text):
    return (text or "").lower().split()[0].split("@")[0].replace("/", "")

def is_admin(uid):
    return uid == ADMIN_ID

def has_shield(chat_id, user_id):
    s = shields()
    return str(chat_id) in s and str(user_id) in s[str(chat_id)]

def use_shield(chat_id, user_id):
    s = shields()
    c, u = str(chat_id), str(user_id)
    if c in s and u in s[c]:
        del s[c][u]
        if not s[c]:
            del s[c]
        save_shields(s)

# ================= ACTIONS =================
def kick(bot, chat_id, user_id):
    bot.ban_chat_member(chat_id, user_id)
    bot.unban_chat_member(chat_id, user_id)

def ban(bot, chat_id, user_id, hours=None):
    until = None
    if hours:
        until = int((datetime.utcnow() + timedelta(hours=hours)).timestamp())
    bot.ban_chat_member(chat_id, user_id, until_date=until)

def unban(bot, chat_id, user_id):
    bot.unban_chat_member(chat_id, user_id, only_if_banned=True)

# ================= JOIN EVENT =================
def handle_chat_member_update(bot, update):
    try:
        if not update or not update.new_chat_member:
            return

        user = update.new_chat_member.user
        chat_id = update.chat.id

        if update.new_chat_member.status == "member":
            bot.send_message(chat_id,
                f"👑 тебя помиловали, можешь заходить нормально, {user.first_name}")
    except:
        pass

# ================= PAYMENTS =================
def handle_successful(bot, message):
    payload = message.successful_payment.invoice_payload

    # UNBAN
    if payload.startswith("unban:"):
        _, chat_id, user_id = payload.split(":")

        unban(bot, int(chat_id), int(user_id))

        link = None
        try:
            link = bot.export_chat_invite_link(int(chat_id))
        except:
            link = "нет ссылки"

        bot.send_message(int(chat_id),
            "господин тебя помиловал")

        try:
            bot.send_message(int(user_id),
                f"ты разбанен 👑\nвход: {link}")
        except:
            pass
        return

    # SHIELD
    if payload.startswith("shield:"):
        _, chat_id, user_id = payload.split(":")
        s = shields()
        s.setdefault(chat_id, {})
        s[chat_id][user_id] = True
        save_shields(s)
        bot.send_message(int(chat_id), "🛡 щит активирован")
        return

    # BAN PAYMENT
    if payload.startswith("ban:"):
        _, chat_id, user_id, hours = payload.split(":")

        hours = int(hours)
        if hours <= 0:
            hours = None

        ban(bot, int(chat_id), int(user_id), hours)

        bot.send_message(int(chat_id),
            "ну всё, допрыгался лошара, посиди в бане")
        return

# ================= MAIN =================
def handle(bot, message):
    text = message.text or ""
    c = norm(text)
    p = prices()

    if not c:
        return

    parts = text.split()

    # ================= KICK =================
    if c == "кик":
        if not message.reply_to_message:
            return

        t = message.reply_to_message.from_user

        if is_admin(message.from_user.id):
            kick(bot, message.chat.id, t.id)
            bot.send_message(message.chat.id,
                "выйди и зайди нормально")
            return

        bot.send_invoice(
            message.chat.id,
            "кик",
            "выкинуть из чата",
            f"kick:{message.chat.id}:{t.id}",
            PROVIDER_TOKEN,
            "XTR",
            [LabeledPrice("kick", p["kick"])]
        )
        return

    # ================= BAN =================
    if c == "бан":
        if not message.reply_to_message:
            return

        t = message.reply_to_message.from_user

        # shield
        if has_shield(message.chat.id, t.id):
            use_shield(message.chat.id, t.id)
            bot.send_message(message.chat.id, "🛡 щит спас")
            return

        hours = None
        if len(parts) > 1:
            try:
                hours = int(parts[1])
            except:
                hours = None

        if is_admin(message.from_user.id):
            ban(bot, message.chat.id, t.id, hours)
            bot.send_message(message.chat.id,
                f"ну всё, посиди в бане {hours or '∞'} часов")
            return

        bot.send_invoice(
            message.chat.id,
            "бан",
            "бан по часам",
            f"ban:{message.chat.id}:{t.id}:{hours or 0}",
            PROVIDER_TOKEN,
            "XTR",
            [LabeledPrice("ban", p["ban_hour"])]
        )
        return

    # ================= UNBAN =================
    if c == "разбан":
        if not message.reply_to_message:
            return

        t = message.reply_to_message.from_user

        if is_admin(message.from_user.id):
            unban(bot, message.chat.id, t.id)
            bot.send_message(message.chat.id,
                "господин тебя помиловал")
            return

        bot.send_invoice(
            message.chat.id,
            "разбан",
            "снятие бана",
            f"unban:{message.chat.id}:{t.id}",
            PROVIDER_TOKEN,
            "XTR",
            [LabeledPrice("unban", p["unban"])]
        )
        return

    # ================= SHIELD =================
    if c == "щит":
        if not message.reply_to_message:
            return

        t = message.reply_to_message.from_user

        bot.send_invoice(
            message.chat.id,
            "щит",
            "защита от бана",
            f"shield:{message.chat.id}:{t.id}",
            PROVIDER_TOKEN,
            "XTR",
            [LabeledPrice("shield", p["shield"])]
        )
        return

    # ================= PRICES =================
    if c in ["kickprice", "banprice", "banpricer", "unbanprice", "shieldprice"]:
        if not is_admin(message.from_user.id):
            return

        val = int(parts[1])
        p = prices()

        if c == "kickprice":
            p["kick"] = val
        if c in ["banprice", "banpricer"]:
            p["ban"] = val
        if c == "unbanprice":
            p["unban"] = val
        if c == "shieldprice":
            p["shield"] = val

        save_prices(p)
        bot.reply_to(message, "цена обновлена")