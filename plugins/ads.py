import json
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

DATA_FILE = "ads.json"


def load():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "admin_chat_id": None}

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"pending": {}, "admin_chat_id": None}


def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# =================================================================
# /priser → показывает цену + сохраняет админа
# =================================================================
def handle_priser(bot, message):
    if message.chat.type != "private":
        bot.reply_to(message, "⚠ Реклама работает только в личных сообщениях.")
        return

    data = load()
    data["admin_chat_id"] = message.chat.id
    save(data)

    bot.send_message(
        message.chat.id,
        "💰 *Стоимость рекламы:* 1⭐ за 10 просмотров.\n\n"
        "Введите текст рекламы:",
        parse_mode="Markdown",
    )

    data["pending"][str(message.from_user.id)] = {"step": "text"}
    save(data)


# =================================================================
# Основной handler — получает текст / фото / частоту отчётов
# =================================================================
def handle(bot, message):
    if message.chat.type != "private":
        return

    user_id = str(message.from_user.id)
    data = load()

    if user_id not in data["pending"]:
        return

    step = data["pending"][user_id]["step"]

    # -------------------------------- TEXT --------------------------------
    if step == "text":
        data["pending"][user_id]["text"] = message.text
        data["pending"][user_id]["step"] = "photo_q"
        save(data)

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Добавить фото", callback_data="ads_add_photo"),
            InlineKeyboardButton("Без фото", callback_data="ads_no_photo")
        )

        bot.send_message(message.chat.id, "📸 Добавить фото?", reply_markup=kb)
        return

    # -------------------------------- PHOTO --------------------------------
    if step == "photo":
        if not message.photo:
            bot.send_message(message.chat.id, "⚠ Отправьте именно *фото*.")
            return

        file_id = message.photo[-1].file_id
        data["pending"][user_id]["photo"] = file_id
        data["pending"][user_id]["step"] = "notify"
        save(data)

        ask_notify(bot, message.chat.id)
        return

    # -------------------------------- NOTIFY INTERVAL --------------------------------
    if step == "notify":
        data["pending"][user_id]["notify"] = message.text
        data["pending"][user_id]["step"] = "confirm"
        save(data)

        send_to_admin(bot, user_id)
        return


# =================================================================
# Вопрос про уведомления
# =================================================================
def ask_notify(bot, chat_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Каждые 10", callback_data="ads_nf_10"),
        InlineKeyboardButton("Каждые 50", callback_data="ads_nf_50"),
        InlineKeyboardButton("Каждые 100", callback_data="ads_nf_100"),
        InlineKeyboardButton("Только в конце", callback_data="ads_nf_end"),
    )
    bot.send_message(chat_id, "📢 Как часто уведомлять?", reply_markup=kb)


# =================================================================
# Отправка админу
# =================================================================
def send_to_admin(bot, user_id):
    data = load()
    admin = data.get("admin_chat_id")

    if not admin:
        return  # НЕ ПАДАЕМ – просто некуда отправлять

    ad = data["pending"][user_id]

    caption = f"🔔 *Новая реклама*\n\n👤 Пользователь: `{user_id}`\n\n📝 {ad['text']}"

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Одобрить", callback_data=f"ads_ok_{user_id}"),
        InlineKeyboardButton("Отклонить", callback_data=f"ads_no_{user_id}")
    )

    if "photo" in ad:
        bot.send_photo(admin, ad["photo"], caption=caption, parse_mode="Markdown", reply_markup=kb)
    else:
        bot.send_message(admin, caption, parse_mode="Markdown", reply_markup=kb)


# =================================================================
# CALLBACKS
# =================================================================
def callback(bot, call):
    if not call.data.startswith("ads_"):
        return

    data = load()

    # remove buttons
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass

    # -------------------------------------------------------------------------
    # add / no photo
    # -------------------------------------------------------------------------
    if call.data == "ads_add_photo":
        user = str(call.from_user.id)
        data["pending"][user]["step"] = "photo"
        save(data)
        bot.send_message(call.message.chat.id, "📸 Отправьте фото")
        return

    if call.data == "ads_no_photo":
        user = str(call.from_user.id)
        data["pending"][user]["photo"] = None
        data["pending"][user]["step"] = "notify"
        save(data)
        ask_notify(bot, call.message.chat.id)
        return

    # -------------------------------------------------------------------------
    # notify settings
    # -------------------------------------------------------------------------
    if call.data.startswith("ads_nf_"):
        user = str(call.from_user.id)
        mode = call.data.replace("ads_nf_", "")
        data["pending"][user]["notify"] = mode
        data["pending"][user]["step"] = "confirm"
        save(data)

        send_to_admin(bot, user)
        bot.send_message(call.message.chat.id, "⏳ Реклама отправлена на проверку.")
        return

    # -------------------------------------------------------------------------
    # admin approve / decline
    # -------------------------------------------------------------------------
    if call.data.startswith("ads_ok_"):
        user = call.data.replace("ads_ok_", "")

        bot.send_message(
            user,
            "✅ Ваша реклама одобрена!\nОна будет отправлена автоматически."
        )

        del data["pending"][user]
        save(data)
        bot.send_message(call.message.chat.id, "👍 Одобрено.")
        return

    if call.data.startswith("ads_no_"):
        user = call.data.replace("ads_no_", "")

        bot.send_message(
            user,
            "❌ Ваша реклама отклонена."
        )

        del data["pending"][user]
        save(data)
        bot.send_message(call.message.chat.id, "🚫 Отклонено.")
        return