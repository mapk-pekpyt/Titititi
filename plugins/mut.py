import os
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from telebot.types import LabeledPrice, ChatPermissions
from telebot import TeleBot

DATA_FILE = "data/price.json"
TZ = ZoneInfo("Europe/Berlin")
ADMIN_ID = 5791171535  # твой id
DEFAULT_PRICE = 2  # цена по умолчанию в телеграмм-звездах

PAYMENT_PROVIDER_TOKEN = os.environ.get("PAYMENT_PROVIDER_TOKEN")  # токен платежного провайдера

def ensure_data_dir():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

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

def get_display_name(user):
    if getattr(user, "username", None):
        return f"@{user.username}"
    if getattr(user, "first_name", None) and getattr(user, "last_name", None):
        return f"{user.first_name} {user.last_name}"
    return user.first_name or "Пользователь"

def apply_mute(bot: TeleBot, chat_id, target_id, minutes, payer_name):
    until = int((datetime.now(timezone.utc) + timedelta(minutes=minutes)).timestamp())
    perms = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )
    bot.restrict_chat_member(chat_id, target_id, permissions=perms, until_date=until)
    bot.send_message(
        chat_id,
        f"⛔ Пользователь <a href='tg://user?id={target_id}'>пользователь</a> лишён голоса на {minutes} минут — по тому что заебал - {payer_name}",
        parse_mode="HTML"
    )

# Обработка команды /price
def handle_price(bot, message):
    text = message.text or ""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Только админ может менять цену.")
        return

    parts = text.split()
    if len(parts) < 2:
        current = load_price()
        bot.reply_to(message, f"Текущая цена за 1 минуту: {current} ⭐")
        return

    try:
        new_price = int(parts[1])
    except:
        bot.reply_to(message, "❗ Укажи целое число: /price 3")
        return

    save_price(new_price)
    bot.reply_to(message, f"✅ Цена за 1 минуту установлена: {new_price} ⭐")

# Обработка /mut
def handle_mut(bot, message):
    text = (message.text or "").strip()
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Чтобы выдать мут, ответь на сообщение пользователя и введи /mut <минуты>")
        return

    parts = text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Укажи минуты: /mut 5")
        return

    try:
        minutes = int(parts[1])
        if minutes <= 0:
            raise ValueError()
    except:
        bot.reply_to(message, "Укажи корректное количество минут (целое).")
        return

    price_per_min = load_price()
    total = price_per_min * minutes
    payer = message.from_user
    target = message.reply_to_message.from_user

    payer_name = get_display_name(payer)
    target_name = get_display_name(target)

    # Если цена 0 — сразу выдаём мут
    if price_per_min == 0:
        apply_mute(bot, message.chat.id, target.id, minutes, payer_name)
        return

    # Отправка настоящего инвойса Telegram
    prices = [LabeledPrice(label=f"{minutes} минута(-ы) мута {target_name}", amount=total * 100)]  # цена в копейках
    bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Оплата мута {target_name}",
        description=f"{payer_name} хочет замутить {target_name} на {minutes} минут",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        payload=f"mute:{payer.id}:{target.id}:{minutes}",
        start_parameter="mutepayment"
    )

# Обработка успешной оплаты
def handle_precheckout(bot, pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

def handle_success(bot, message):
    payload = getattr(message, "successful_payment", None)
    if not payload:
        return
    data = payload.invoice_payload  # формат: mute:{payer_id}:{target_id}:{minutes}
    if not data.startswith("mute:"):
        return
    _, payer_id_s, target_id_s, minutes_s = data.split(":")
    payer_id = int(payer_id_s)
    target_id = int(target_id_s)
    minutes = int(minutes_s)
    payer = message.from_user
    if payer.id != payer_id:
        bot.send_message(message.chat.id, "❌ Платёж с неправильного аккаунта")
        return
    payer_name = get_display_name(payer)
    apply_mute(bot, message.chat.id, target_id, minutes, payer_name)

# Главная точка вызова
def handle(bot, message):
    text = (message.text or "").strip()
    if text.startswith("/price"):
        handle_price(bot, message)
        return
    if text.startswith("/mut"):
        handle_mut(bot, message)
        return

# Регистрируем обработку платежей в main.py:
# bot.pre_checkout_query_handler(func=lambda query: True)(mut.handle_precheckout)
# bot.message_handler(content_types=['successful_payment'])(mut.handle_success)