import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telebot.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ChatPermissions, LabeledPrice
)

DATA_FILE = "data/price.json"
TZ = ZoneInfo("Europe/Berlin")
DEFAULT_PRICE = 2  # ⭐ за минуту

# ТВОЙ TOKEN
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"


# ---------------- STORAGE ----------------
def ensure_data_dir():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)


def load_price():
    ensure_data_dir()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f).get("price", DEFAULT_PRICE))
    except:
        return DEFAULT_PRICE


def save_price(p):
    ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"price": int(p)}, f)


# ---------------- NAME HANDLING ----------------
def get_display_name(user):
    if user.username:
        return f"@{user.username}"
    return user.first_name or "Пользователь"


def get_display_name_by_id(bot, chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id).user
        return get_display_name(member)
    except:
        return "Пользователь"


# ---------------- MUTE APPLY ----------------
def apply_mute(bot, chat_id, target_id, minutes, payer_name):
    until = int((datetime.utcnow() + timedelta(minutes=minutes)).timestamp())

    try:
        perms = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        bot.restrict_chat_member(chat_id, target_id, permissions=perms, until_date=until)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Не удалось выдать мут: {e}")
        return

    target_name = get_display_name_by_id(bot, chat_id, target_id)

    bot.send_message(
        chat_id,
        f"🔇 {target_name}, ты уже заебал {payer_name}…\n"
        f"Он оплатил твоё молчание 😎💰",
        parse_mode="HTML"
    )


# ---------------- PAYMENT SUCCESS ----------------
def handle_successful_payment(bot, message):
    payload = message.successful_payment.invoice_payload

    # mut:<chat_id>:<payer_id>:<target_id>:<minutes>
    try:
        _, chat_id, payer_id, target_id, minutes = payload.split(":")
        chat_id = int(chat_id)
        payer_id = int(payer_id)
        target_id = int(target_id)
        minutes = int(minutes)
    except:
        bot.send_message(message.chat.id, "❌ Ошибка данных платежа")
        return

    payer_name = get_display_name_by_id(bot, chat_id, payer_id)
    apply_mute(bot, chat_id, target_id, minutes, payer_name)


# ---------------- MAIN MUT COMMAND ----------------
def handle(bot, message):
    text = (message.text or "").strip()

    # ----- /price -----
    if text.startswith("/price"):
        if message.from_user.id != 5791171535:
            return bot.reply_to(message, "⛔ Только админ может менять цену.")

        parts = text.split()
        if len(parts) < 2:
            return bot.reply_to(
                message, f"Текущая цена: {load_price()} ⭐ за минуту."
            )

        try:
            newp = int(parts[1])
            save_price(newp)
            return bot.reply_to(message, f"Цена обновлена: {newp} ⭐")
        except:
            return bot.reply_to(message, "Укажи число.")

    # ----- /mut -----
    if not text.startswith("/mut"):
        return

    if not message.reply_to_message:
        return bot.reply_to(message, "Ответь на сообщение человека: /mut <минуты>")

    parts = text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Укажи минуты: /mut 5")

    try:
        minutes = int(parts[1])
        if minutes <= 0:
            raise ValueError()
    except:
        return bot.reply_to(message, "Минуты должны быть числом > 0")

    payer = message.from_user
    target = message.reply_to_message.from_user
    price_per_min = load_price()
    total_stars = price_per_min * minutes

    payer_name = get_display_name(payer)
    target_name = get_display_name(target)

    # ----- FREE MODE -----
    if price_per_min == 0:
        return apply_mute(bot, message.chat.id, target.id, minutes, payer_name)

    # ----- REAL STARS PAYMENT -----
    try:
        bot.send_invoice(
            chat_id=message.chat.id,
            title="Оплата мута",
            description=(
                f"{payer_name} хочет замутить {target_name} на {minutes} минут.\n"
                f"Стоимость: {total_stars} ⭐"
            ),
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=[LabeledPrice(label="Mute", amount=total_stars)],
            invoice_payload=f"mut:{message.chat.id}:{payer.id}:{target.id}:{minutes}",
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка выставления счёта: {e}")