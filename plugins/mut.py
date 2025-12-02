# plugins/mut.py
import os
import json
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions

DATA_FILE = "data/price.json"
TZ = ZoneInfo("Europe/Berlin")
ADMIN_ID = 5791171535  # твой id (как ты прислал)

# default price (stars) per minute
DEFAULT_PRICE = 2

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

def get_display_name_from_user(user):
    if getattr(user, "username", None):
        return f"@{user.username}"
    return user.first_name or "Пользователь"

def apply_mute(bot, chat_id, target_id, minutes, payer_name):
    # until_date as unix timestamp
    until = int((datetime.utcnow() + timedelta(minutes=minutes)).timestamp())
    try:
        perms = ChatPermissions(can_send_messages=False, can_send_media_messages=False,
                                can_send_other_messages=False, can_add_web_page_previews=False)
        bot.restrict_chat_member(chat_id, target_id, permissions=perms, until_date=until)
    except Exception as e:
        # try fallback: send message about failure
        bot.send_message(chat_id, f"Не удалось выдать мут (ошибка API): {e}")
        return
    bot.send_message(chat_id, f"⛔ Пользователь <a href='tg://user?id={target_id}'>пользователь</a> лишён голоса на {minutes} минут — т.к. {payer_name} оплатил(а).", parse_mode="HTML")

# callback handler name: should be set in main.py to route callback_query to plugins if necessary.
# But telebot supports global handler - since plugins are imported, register callback handler here:

def handle_callback(bot, call):
    """
    Обработка callback'ов для оплаты мутов.
    callback_data формат: paymut:{payer_id}:{target_id}:{minutes}
    """
    data = call.data or ""
    if not data.startswith("paymut:"):
        return False
    parts = data.split(":")
    if len(parts) != 4:
        bot.answer_callback_query(call.id, "Неправильные данные")
        return True
    _, payer_id_s, target_id_s, minutes_s = parts
    try:
        payer_id = int(payer_id_s)
        target_id = int(target_id_s)
        minutes = int(minutes_s)
    except:
        bot.answer_callback_query(call.id, "Неверные данные")
        return True

    # only the payer can press the pay button
    if call.from_user.id != payer_id:
        bot.answer_callback_query(call.id, "Только платильщик может нажать эту кнопку")
        return True

    payer_name = get_display_name_from_user(call.from_user)
    # here we assume payment is done outside or transferred; we treat button press as confirmation
    apply_mute(bot, call.message.chat.id, target_id, minutes, payer_name)
    bot.answer_callback_query(call.id, "Оплата подтверждена, мут выдан ✅")
    # edit message to show paid
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    return True

def handle(bot, message):
    text = (message.text or "").strip()
    # admin can set price with /price X
    if text.startswith("/price"):
        parts = text.split()
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ Только админ может менять цену.")
            return
        if len(parts) < 2:
            current = load_price()
            bot.reply_to(message, f"Текущая цена за 1 минуту: {current} ⭐")
            return
        try:
            newp = int(parts[1])
        except:
            bot.reply_to(message, "❗ Укажи целое число: /price 3")
            return
        save_price(newp)
        bot.reply_to(message, f"✅ Цена за 1 минуту установлена: {newp} ⭐")
        return

    # /mut command
    if not text.startswith("/mut"):
        return

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
    payer_name = get_display_name_from_user(payer)
    target_name = get_display_name_from_user(target)

    # if price == 0 — immediate mute (only payer must have the right to perform; we allow anyone to pay)
    if price_per_min == 0:
        apply_mute(bot, message.chat.id, target.id, minutes, payer_name)
        return

    # else: create inline button "Оплатить"
    markup = InlineKeyboardMarkup()
    # embed payer id so only payer can confirm
    cb = f"paymut:{payer.id}:{target.id}:{minutes}"
    markup.add(InlineKeyboardButton(text=f"💫 Оплатить {total} ⭐", callback_data=cb))
    bot.send_message(message.chat.id,
                     f"💰 {payer_name} хочет замутить {target_name} на {minutes} минут. Для подтверждения оплаты нажмите кнопку ниже (только плательщик). Цена: {total} ⭐",
                     reply_markup=markup)