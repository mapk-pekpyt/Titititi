import os
import json
from datetime import datetime, timedelta, timezone
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatPermissions,
    LabeledPrice
)
from telebot import TeleBot

# === НАСТРОЙКИ ===

DATA_FILE = "data/price.json"
ADMIN_ID = 5791171535                 # твой ID
DEFAULT_PRICE = 2                     # цена за минуту
PROVIDER_TOKEN = os.environ.get("PROVIDER_TOKEN")  # токен Telegram Payments
CURRENCY = "XTR"                      # валюта Telegram Stars
TZ = timezone.utc


# === ХРАНЕНИЕ ЦЕНЫ ===

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


# === ВСПОМОГАТЕЛЬНЫЕ ===

def get_display_name(user):
    if getattr(user, "username", None):
        return f"@{user.username}"
    return user.first_name or "Безымянный"


def apply_mute(bot: TeleBot, chat_id, target_id, minutes, payer_name):
    until = int((datetime.utcnow() + timedelta(minutes=minutes)).timestamp())
    perms = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )

    try:
        bot.restrict_chat_member(chat_id, target_id, permissions=perms, until_date=until)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Не удалось выдать мут: {e}")
        return

    bot.send_message(
        chat_id,
        f"🔇 <a href='tg://user?id={target_id}'>Пользователь</a>, "
        f"ты уже реально заебал…\n"
        f"{payer_name} оплатил твоё молчание 😎💰",
        parse_mode="HTML"
    )


# === ГЛАВНАЯ ФУНКЦИЯ ПЛАГИНА (main.py вызывает только ЭТО) ===

def handle(bot: TeleBot, message):
    text = (message.text or "").strip()

    # === Команда /price ===
    if text.startswith("/price"):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ Только админ может менять цену.")
            return

        parts = text.split()
        if len(parts) == 1:
            bot.reply_to(message, f"💰 Текущая цена: {load_price()} ⭐ за 1 минуту")
            return

        try:
            p = int(parts[1])
        except:
            bot.reply_to(message, "❗ Введи число: /price 3")
            return

        save_price(p)
        bot.reply_to(message, f"✅ Новая цена: {p} ⭐")
        return

    # === Команда /mut ===
    if not text.startswith("/mut"):
        return

    if not message.reply_to_message:
        bot.reply_to(message, "⚠ Ответь на сообщение пользователя: /mut <минуты>")
        return

    parts = text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❗ Укажи минуты: /mut 5")
        return

    try:
        minutes = int(parts[1])
        if minutes <= 0:
            raise ValueError()
    except:
        bot.reply_to(message, "❗ Укажи корректное целое число")
        return

    payer = message.from_user
    target = message.reply_to_message.from_user
    payer_name = get_display_name(payer)
    target_name = get_display_name(target)

    price_per_min = load_price()
    total_price = price_per_min * minutes

    # === Бесплатный мут ===
    if total_price == 0:
        apply_mute(bot, message.chat.id, target.id, minutes, payer_name)
        return

    # === Платёж Stars ===
    try:
        prices = [LabeledPrice(label=f"{minutes} мин мута", amount=total_price)]
        bot.send_invoice(
            chat_id=message.chat.id,
            title=f"Мут {target_name}",
            description=f"{payer_name} хочет замутить {target_name} на {minutes} минут 🔇",
            provider_token=PROVIDER_TOKEN,
            currency=CURRENCY,
            prices=prices,
            start_parameter="mut",
            invoice_payload=f"mut:{target.id}:{minutes}",
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка создания платежа: {e}")


# === ХЕНДЛЕР УСПЕШНОЙ ОПЛАТЫ (РЕГИСТРИРУЕМ ЗДЕСЬ) ===

def register_handlers(bot: TeleBot):
    @bot.pre_checkout_query_handler(func=lambda q: True)
    def _(q):
        bot.answer_pre_checkout_query(q.id, ok=True)

    @bot.message_handler(content_types=['successful_payment'])
    def _(msg):
        payload = msg.successful_payment.invoice_payload
        if not payload.startswith("mut:"):
            return

        _, tid, minutes = payload.split(":")
        apply_mute(bot, msg.chat.id, int(tid), int(minutes), get_display_name(msg.from_user))


# === РЕГИСТРАЦИЯ ХЕНДЛЕРОВ ПРИ ИМПОРТЕ ===
# main.py НЕ НУЖНО ОТКРЫВАТЬ ИЛИ МЕНЯТЬ
# bot ИМЕЕТСЯ ВНУТРИ main.py → импортируем mut ПОСЛЕ bot = TeleBot(...)

def init(bot):
    register_handlers(bot)