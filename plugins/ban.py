import os
import json
from datetime import datetime, timedelta
from telebot.types import LabeledPrice, ChatPermissions

DATA_DIR = "data"
PRICE_FILE = f"{DATA_DIR}/ban_prices.json"
SHIELD_FILE = f"{DATA_DIR}/shields.json"

ADMIN_ID = 5791171535
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

DEFAULT_PRICES = {
    "kick": 0,
    "ban": 3,
    "unban": 20,
    "shield": 5
}


# =========================
# FILE HELPERS
# =========================
def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_json(path, default):
    ensure_dir()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default.copy()


def save_json(path, data):
    ensure_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_prices():
    return load_json(PRICE_FILE, DEFAULT_PRICES)


def save_prices(data):
    save_json(PRICE_FILE, data)


def load_shields():
    return load_json(SHIELD_FILE, {})


def save_shields(data):
    save_json(SHIELD_FILE, data)


# =========================
# HELPERS
# =========================
def name(user):
    return getattr(user, "first_name", None) or "пользователь"


def is_admin(user_id):
    return user_id == ADMIN_ID


def restrict(bot, chat_id, user_id, minutes=None):
    until = None
    if minutes:
        until = int((datetime.utcnow() + timedelta(minutes=minutes)).timestamp())

    perms = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )

    bot.restrict_chat_member(chat_id, user_id, permissions=perms, until_date=until)


def ban_user(bot, chat_id, user_id, hours=None):
    until = None
    if hours:
        until = int((datetime.utcnow() + timedelta(hours=hours)).timestamp())

    bot.ban_chat_member(chat_id, user_id, until_date=until)


def unban_user(bot, chat_id, user_id):
    bot.unban_chat_member(chat_id, user_id, only_if_banned=True)


def has_shield(chat_id, user_id):
    data = load_shields()
    return str(chat_id) in data and str(user_id) in data[str(chat_id)]


def consume_shield(chat_id, user_id):
    data = load_shields()
    c = str(chat_id)
    u = str(user_id)

    if c in data and u in data[c]:
        del data[c][u]
        if not data[c]:
            del data[c]
        save_shields(data)
        return True
    return False


# =========================
# CHAT MEMBER PROTECTION
# =========================
def handle_chat_member_update(bot, update):
    """
    защита админа — если его банят/кикают → сразу откат
    """
    try:
        if not update or not update.new_chat_member:
            return

        user = update.new_chat_member.user
        status = update.new_chat_member.status
        chat_id = update.chat.id

        if user.id == ADMIN_ID and status in ["kicked", "banned", "left"]:
            unban_user(bot, chat_id, ADMIN_ID)

            try:
                link = bot.export_chat_invite_link(chat_id)
                bot.send_message(chat_id, f"👑 господин вернулся\n{link}")
            except:
                bot.send_message(chat_id, "👑 господин вернулся")
    except:
        pass


# =========================
# PAYMENT HANDLER
# =========================
def handle_successful(bot, message):
    payload = message.successful_payment.invoice_payload

    # ===== UNBAN =====
    if payload.startswith("unban:"):
        _, chat_id, target_id = payload.split(":")
        unban_user(bot, int(chat_id), int(target_id))

        bot.send_message(
            int(chat_id),
            "господин решил тебя помиловать, целуй ему ноги пес"
        )
        return

    # ===== SHIELD =====
    if payload.startswith("shield:"):
        _, chat_id, user_id = payload.split(":")

        data = load_shields()
        data.setdefault(chat_id, {})
        data[chat_id][user_id] = True
        save_shields(data)

        bot.send_message(int(chat_id), "🛡 щит активирован (1 бан)")
        return


# =========================
# MAIN HANDLER
# =========================
def handle(bot, message):
    text = (message.text or "").lower().strip()
    if not text:
        return

    parts = text.split()
    cmd = parts[0]

    prices = load_prices()

    # ================= KICK =================
    if cmd == "кик":
        if not message.reply_to_message:
            return

        target = message.reply_to_message.from_user
        bot.kick_chat_member(message.chat.id, target.id)

        bot.send_message(message.chat.id, "выйди и зайди нормально")
        return

    # ================= BAN =================
    if cmd == "бан":
        if not message.reply_to_message:
            return

        target = message.reply_to_message.from_user

        # защита щитом
        if has_shield(message.chat.id, target.id):
            consume_shield(message.chat.id, target.id)
            bot.send_message(message.chat.id, "🛡 щит сработал, бан отменён")
            return

        # админ — бесплатно
        if is_admin(message.from_user.id):
            hours = None
            if len(parts) > 1:
                try:
                    hours = int(parts[1])
                except:
                    hours = None

            ban_user(bot, message.chat.id, target.id, hours)
            bot.send_message(message.chat.id, "спердоляй с чату")
            return

        # платный бан
        bot.send_invoice(
            chat_id=message.chat.id,
            title="Бан",
            description="забанить пользователя",
            invoice_payload=f"ban:{message.chat.id}:{target.id}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=[LabeledPrice(label="ban", amount=prices["ban"])]
        )
        return

    # ================= UNBAN =================
    if cmd == "разбан":
        if not message.reply_to_message:
            return

        target = message.reply_to_message.from_user

        if is_admin(message.from_user.id):
            unban_user(bot, message.chat.id, target.id)
            bot.send_message(message.chat.id, "господин решил тебя помиловать, целуй ему ноги пес")
            return

        bot.send_invoice(
            chat_id=message.chat.id,
            title="Разбан",
            description="снять бан",
            invoice_payload=f"unban:{message.chat.id}:{target.id}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=[LabeledPrice(label="unban", amount=prices["unban"])]
        )
        return

    # ================= SHIELD BUY =================
    if cmd == "щит":
        if not message.reply_to_message:
            return

        target = message.reply_to_message.from_user

        bot.send_invoice(
            chat_id=message.chat.id,
            title="Щит",
            description="защита от 1 бана",
            invoice_payload=f"shield:{message.chat.id}:{target.id}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=[LabeledPrice(label="shield", amount=prices["shield"])]
        )
        return

    # ================= PRICE =================
    if cmd == "kickprice" and is_admin(message.from_user.id):
        prices["kick"] = int(parts[1])
        save_prices(prices)

    if cmd == "banprice" and is_admin(message.from_user.id):
        prices["ban"] = int(parts[1])
        save_prices(prices)

    if cmd == "banpricer" and is_admin(message.from_user.id):
        prices["unban"] = int(parts[1])
        save_prices(prices)