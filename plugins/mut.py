import os
import json
import threading
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, Message

DATA_FILE = "data/price.json"
ADMIN_ID = 5791171535  # твой ID

DEFAULT_PRICE = 2  # цена в звездах за минуту

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

def unmute_later(bot, chat_id, target_id, minutes):
    """Снимаем мут через X минут"""
    def unmute():
        try:
            perms = ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
            bot.restrict_chat_member(chat_id, target_id, permissions=perms)
            bot.send_message(chat_id, f"✅ <a href='tg://user?id={target_id}'>пользователь</a> снова может писать.", parse_mode="HTML")
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при снятии мута: {e}")

    t = threading.Timer(minutes * 60, unmute)
    t.start()

def apply_mute(bot, chat_id, target_id, minutes, payer_name):
    """Выдаем временный мут через restrict_chat_member"""
    try:
        perms = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        until = int((datetime.utcnow() + timedelta(minutes=minutes)).timestamp())
        bot.restrict_chat_member(chat_id, target_id, permissions=perms, until_date=until)
    except Exception as e:
        bot.send_message(chat_id, f"Не удалось выдать мут (ошибка API): {e}")
        return

    bot.send_message(chat_id,
                     f"⛔ Пользователь <a href='tg://user?id={target_id}'>пользователь</a> лишён голоса на {minutes} минут — "
                     f"т.к. {payer_name} оплатил(а).",
                     parse_mode="HTML")
    unmute_later(bot, chat_id, target_id, minutes)

def handle_callback(bot, call):
    """Обработка нажатия кнопки оплаты"""
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

    if call.from_user.id != payer_id:
        bot.answer_callback_query(call.id, "Только плательщик может нажать кнопку")
        return True

    payer_name = get_display_name_from_user(call.from_user)
    apply_mute(bot, call.message.chat.id, target_id, minutes, payer_name)
    bot.answer_callback_query(call.id, "Оплата подтверждена, мут выдан ✅")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    return True

def handle(bot, message: Message):
    text = (message.text or "").strip()

    # --- Управление ценой ---
    if text.startswith("/price"):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ Только админ может менять цену.")
            return
        parts = text.split()
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

    # --- Выдать мут ---
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

    # Если цена == 0 — сразу мут
    if price_per_min == 0:
        apply_mute(bot, message.chat.id, target.id, minutes, payer_name)
        return

    # Иначе создаем кнопку оплаты
    markup = InlineKeyboardMarkup()
    cb = f"paymut:{payer.id}:{target.id}:{minutes}"
    markup.add(InlineKeyboardButton(text=f"💫 Оплатить {total} ⭐", callback_data=cb))
    bot.send_message(message.chat.id,
                     f"💰 {payer_name} хочет замутить {target_name} на {minutes} минут. "
                     f"Для подтверждения оплаты нажмите кнопку ниже (только плательщик). Цена: {total} ⭐",
                     reply_markup=markup)