# plugins/mut.py
import json
import os
from datetime import datetime, timedelta
from telebot.types import ChatPermissions, LabeledPrice

# настройки
DATA_FILE = "data/price.json"
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"  # твой провайдер-токен
DEFAULT_PRICE = 2  # ⭐ за минуту (если нет файла)

# ---------------- storage ----------------
def ensure_data_dir():
    dirname = os.path.dirname(DATA_FILE)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

def load_price():
    ensure_data_dir()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            return int(d.get("price", DEFAULT_PRICE))
    except:
        return DEFAULT_PRICE

def save_price(p):
    ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"price": int(p)}, f)

# ---------------- names ----------------
def get_name(user):
    if getattr(user, "first_name", None):
        return user.first_name
    if getattr(user, "username", None):
        return f"@{user.username}"
    return "Пользователь"

def get_name_by_id(bot, chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id).user
        return get_name(member)
    except:
        return "Пользователь"

# ---------------- apply mute ----------------
def apply_mute(bot, chat_id, target_id, minutes, payer_name, target_name=None):
    until_ts = int((datetime.utcnow() + timedelta(minutes=minutes)).timestamp())
    try:
        perms = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        bot.restrict_chat_member(chat_id, target_id, permissions=perms, until_date=until_ts)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Не удалось выдать мут: {e}")
        return

    if not target_name:
        target_name = get_name_by_id(bot, chat_id, target_id)

    bot.send_message(
        chat_id,
        f"🔇 <b>{target_name}</b>, ты уже заебал <b>{payer_name}</b>…\n"
        f"Он оплатил твоё молчание на <b>{minutes}</b> минут 😎💰",
        parse_mode="HTML"
    )

# ---------------- successful payment handler ----------------
def handle_successful(bot, message):
    # ожидаем invoice_payload формата: mut:<chat_id>:<payer_id>:<target_id>:<minutes>
    payload = getattr(message.successful_payment, "invoice_payload", "") or getattr(message.successful_payment, "payload", "")
    if not payload.startswith("mut:"):
        return
    try:
        _, chat_id_s, payer_id_s, target_id_s, minutes_s = payload.split(":")
        chat_id = int(chat_id_s); payer_id = int(payer_id_s)
        target_id = int(target_id_s); minutes = int(minutes_s)
    except Exception:
        bot.send_message(message.chat.id, "❌ Ошибка разбора payload после оплаты.")
        return

    payer_name = get_name_by_id(bot, chat_id, payer_id)
    apply_mute(bot, chat_id, target_id, minutes, payer_name)

# ---------------- main handler ----------------
def handle(bot, message):
    text = (message.text or "").strip()

    # /price — только админ (ID ставь свой, если нужно поменять)
    if text.startswith("/price"):
        parts = text.split()
        ADMIN_ID = 5791171535
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "⛔ Только админ может менять цену.")
        if len(parts) == 1:
            return bot.reply_to(message, f"Текущая цена: {load_price()} ⭐ за 1 минуту.")
        try:
            newp = int(parts[1])
            save_price(newp)
            return bot.reply_to(message, f"✅ Цена за 1 минуту установлена: {newp} ⭐")
        except:
            return bot.reply_to(message, "❗ Укажи целое число: /price 3")

    # команда /mut
    if not text.startswith("/mut"):
        return

    if not message.reply_to_message:
        return bot.reply_to(message, "⚠️ Чтобы выдать мут, ответь на сообщение пользователя и введи /mut <минуты>")

    parts = text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Укажи минуты: /mut 5")

    try:
        minutes = int(parts[1])
        if minutes <= 0:
            raise ValueError()
    except:
        return bot.reply_to(message, "Укажи корректное количество минут (целое, > 0).")

    payer = message.from_user
    target = message.reply_to_message.from_user
    payer_name = get_name(payer)
    target_name = get_name(target)

    price_per_min = load_price()
    total_stars = price_per_min * minutes

    # --- если цена нулевая или отрицательная — выдаём мут сразу и НЕ создаём инвойс
    if price_per_min <= 0 or total_stars <= 0:
        return apply_mute(bot, message.chat.id, target.id, minutes, payer_name, target_name)

    # --- иначе — создаём реальный инвойс (pyTelegramBotAPI >=4.20/4.23 формат)
    try:
        prices = [LabeledPrice(label="Mute", amount=total_stars)]
        bot.send_invoice(
            chat_id=message.chat.id,
            title=f"Мут {target_name} на {minutes} мин",
            description=f"{payer_name} хочет замутить {target_name} на {minutes} минут. Стоимость: {total_stars} ⭐",
            invoice_payload=f"mut:{message.chat.id}:{payer.id}:{target.id}:{minutes}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )
    except Exception as e:
        # на всякий случай — если инвойс не удаётся создать, уведомляем об этом и не ломаем процесс
        bot.reply_to(message, f"❌ Ошибка выставления счёта: {e}")