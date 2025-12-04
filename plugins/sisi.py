# plugins/sisi.py

import os
import json
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today

# --- ФАЙЛ ЦЕНЫ /bustprice ---
DATA_FILE = "data/bust_price.json"
DEFAULT_BUST_PRICE = 3  # цена за +1 к размеру груди
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"
ADMIN_ID = 5791171535


# ======= ИМЕНА =======
def get_display_name(user):
    fn = getattr(user, "first_name", None)
    ln = getattr(user, "last_name", None)

    if fn and ln:
        return f"{fn} {ln}"
    if fn:
        return fn
    return "Пользователь"


def get_name_by_id(bot, chat_id, user_id):
    try:
        m = bot.get_chat_member(chat_id, user_id).user
        return get_display_name(m)
    except:
        return "Пользователь"


# ======= PRICE SYSTEM =======
def ensure_dir():
    d = os.path.dirname(DATA_FILE)
    if d:
        os.makedirs(d, exist_ok=True)


def load_bust_price():
    ensure_dir()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f).get("bust_price", DEFAULT_BUST_PRICE))
    except:
        return DEFAULT_BUST_PRICE


def save_bust_price(v):
    ensure_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"bust_price": int(v)}, f)


# ======= УВЕЛИЧЕНИЕ ГРУДИ ПО ОПЛАТЕ =======
def handle_successful_bust(bot, message):
    payload = (
        getattr(message.successful_payment, "invoice_payload", "") or
        getattr(message.successful_payment, "payload", "")
    )

    if not payload.startswith("bust:"):
        return

    _, chat_id_s, user_id_s, amount_s = payload.split(":")

    chat_id = int(chat_id_s)
    user_id = int(user_id_s)
    amount = int(amount_s)

    data = ensure_user(chat_id, message.from_user)

    # увеличиваем размер
    current = data[str(chat_id)][str(user_id)]["sisi"]
    new_size = current + amount
    data[str(chat_id)][str(user_id)]["sisi"] = new_size

    payer = get_name_by_id(bot, chat_id, user_id)

    bot.send_message(
        chat_id,
        f"💖 {payer}, твои сисечки стали больше на {amount}! "
        f"Теперь размер: {new_size} 🍒"
    )


# ======= ОБРАБОТЧИК КОМАНД =======
def handle(bot, message):
    text = (message.text or "").strip()
    if not text:
        return

    cmd_raw = text.split()[0].lower()
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw

    # ======================================
    # /bustprice — установить цену
    # ======================================
    if cmd == "/bustprice":
        parts = text.split()

        if len(parts) == 1:
            bot.reply_to(message, f"💳 Текущая цена: {load_bust_price()} ⭐ за +1 размер")
            return

        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ Только админ может менять цену.")
            return

        try:
            newp = int(parts[1])
            save_bust_price(newp)
            bot.reply_to(message, f"✅ Новая цена: {newp} ⭐ за +1 размера груди")
        except:
            bot.reply_to(message, "❗ Используй: /bustprice 3")
        return

    # ======================================
    # /bust — покупка размера груди
    # ======================================
    if cmd == "/bust":
        parts = text.split()

        if len(parts) < 2:
            bot.reply_to(message, "Использование: /bust 3 (увеличить на 3)")
            return

        try:
            amount = int(parts[1])
            if amount <= 0:
                raise ValueError()
        except:
            bot.reply_to(message, "❗ Значение должно быть > 0")
            return

        user = message.from_user
        price_per_1 = load_bust_price()
        total = price_per_1 * amount

        # формируем инвойс
        try:
            prices = [LabeledPrice("Bust Growth", total)]

            bot.send_invoice(
                chat_id=message.chat.id,
                title="Увеличение груди ❤️",
                description=f"Увеличение на {amount} единиц",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices,
                invoice_payload=f"bust:{message.chat.id}:{user.id}:{amount}"
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка оплаты: {e}")

        return

    # ======================================
    # ✨ Обычная игра «сисечки»
    # ======================================
    if cmd != "/sisi":
        return

    user = message.from_user
    name = get_display_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)

    if was_today(chat, user, "last_sisi"):
        current = data[str(chat)][str(user.id)]["sisi"]
        return bot.reply_to(
            message,
            f"{name}, шалунишка ты мой, думал не замечу? "
            f"Ты уже играла сегодня и твои вишенки сейчас {current} размера 😳🍒"
        )

    delta = weighted_random()

    # предотвращение отрицательных размеров
    old = data[str(chat)][str(user.id)]["sisi"]
    new_val = old + delta
    if new_val < 0:
        new_val = 0
        delta = -old  # корректная разница

    data[str(chat)][str(user.id)]["sisi"] = new_val
    update_date(chat, user, "last_sisi")

    bot.reply_to(
        message,
        f"{name}, твои сисечки изменились на {delta:+}, "
        f"теперь твой размер груди {new_val} 😳🍒"
    )