import json
import os
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatPermissions,
    LabeledPrice
)

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"
DATA_FILE = "data/price.json"


def ensure_data_dir():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)


def load_price():
    ensure_data_dir()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            return int(d.get("price", 2))
    except:
        return 2


def save_price(p):
    ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"price": int(p)}, f)


def get_name(user):
    if user.first_name:
        return user.first_name
    if user.username:
        return f"@{user.username}"
    return "Пользователь"


# -------------------- APPLY MUTE --------------------

def apply_mute(bot, chat_id, target_id, minutes, payer_name, target_name):
    until = bot.datetime.datetime.utcnow() + bot.datetime.timedelta(minutes=minutes)
    until_ts = int(until.timestamp())

    perms = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_add_web_page_previews=False,
        can_send_other_messages=False,
    )

    bot.restrict_chat_member(chat_id, target_id, permissions=perms, until_date=until_ts)

    bot.send_message(
        chat_id,
        f"🤫 <b>{target_name}</b>, ты уже заебал <b>{payer_name}</b>…\n"
        f"Он оплатил твоё молчание на <b>{minutes}</b> минут 😈💸",
        parse_mode="HTML"
    )


# -------------------- SUCCESS PAYMENT --------------------

def handle_successful(bot, message):
    payload = message.successful_payment.invoice_payload
    # format: mut:chat:payer:target:minutes
    parts = payload.split(":")
    if len(parts) != 5:
        return

    _, chat_id, payer_id, target_id, minutes = parts
    chat_id = int(chat_id)
    payer_id = int(payer_id)
    target_id = int(target_id)
    minutes = int(minutes)

    payer = bot.get_chat_member(chat_id, payer_id).user
    target = bot.get_chat_member(chat_id, target_id).user

    payer_name = get_name(payer)
    target_name = get_name(target)

    apply_mute(bot, chat_id, target_id, minutes, payer_name, target_name)


# -------------------- MAIN COMMAND --------------------

def handle(bot, message):
    text = (message.text or "").strip()

    # /price
    if text.startswith("/price"):
        parts = text.split()
        if message.from_user.id != 5791171535:
            bot.reply_to(message, "⛔ Только админ может менять цену.")
            return

        if len(parts) == 1:
            bot.reply_to(message, f"Текущая цена ⭐ за 1 минуту: {load_price()}")
            return

        try:
            new_p = int(parts[1])
        except:
            bot.reply_to(message, "Укажи число: /price 3")
            return

        save_price(new_p)
        bot.reply_to(message, f"Цена за минуту установлена: {new_p} ⭐")
        return

    # /mut
    if not text.startswith("/mut"):
        return

    if not message.reply_to_message:
        bot.reply_to(message, "Ответь на сообщение: /mut <минуты>")
        return

    parts = text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Укажи минуты: /mut 5")
        return

    try:
        minutes = int(parts[1])
        if minutes <= 0:
            raise ValueError
    except:
        bot.reply_to(message, "Минуты должны быть числом.")
        return

    price_per_min = load_price()
    total_stars = price_per_min * minutes

    payer = message.from_user
    target = message.reply_to_message.from_user

    payer_name = get_name(payer)
    target_name = get_name(target)

    prices = [LabeledPrice(label="Mute", amount=total_stars)]

    try:
        bot.send_invoice(
            chat_id=message.chat.id,
            title="Оплата мута",
            description=(
                f"{payer_name} хочет замутить {target_name} на {minutes} минут.\n"
                f"Стоимость: {total_stars} ⭐"
            ),
            invoice_payload=f"mut:{message.chat.id}:{payer.id}:{target.id}:{minutes}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка оплаты: {e}")