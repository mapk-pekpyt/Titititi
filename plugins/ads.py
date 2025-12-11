import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

DATA_FILE = "ads_data.json"
ADMIN_ID = 1619156923   # ← ТЫ АДМИН

def load():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "price": 1, "active_ads": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==============================
# Команда изменить цену
# ==============================
def handle_priser(bot, message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Укажи цену, например:\n/priser 0.1")
        return

    try:
        price = float(parts[1])
    except:
        bot.send_message(message.chat.id, "Цена должна быть числом.")
        return

    data = load()
    data["price"] = price
    save(data)

    bot.send_message(message.chat.id, f"Цена установлена: {price} ⭐ за 1 показ")

# ==============================
# Старт покупки
# ==============================
def handle_buy(bot, message):
    user = str(message.from_user.id)
    data = load()

    data["pending"][user] = {
        "step": "text",
        "text": "",
        "photo_id": None,
        "count": 0,
        "report": "finish"
    }
    save(data)

    bot.send_message(
        message.chat.id,
        f"Стоимость рекламы: {data['price']} ⭐ за 1 показ.\n\nВведите текст рекламы:"
    )

# ==============================
# Главный обработчик шагов
# ==============================
def handle(bot, message):
    user = str(message.from_user.id)
    data = load()

    if user not in data["pending"]:
        return  # Не наш пользователь

    state = data["pending"][user]
    step = state["step"]

    # === ТЕКСТ ===
    if step == "text":
        state["text"] = message.text
        state["step"] = "photo"
        save(data)

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Добавить фото", callback_data="ads_add_photo"),
            InlineKeyboardButton("Без фото", callback_data="ads_no_photo")
        )

        bot.send_message(message.chat.id, "Хотите добавить фото?", reply_markup=kb)
        return

    # === ПРИЁМ ФОТО ===
    if step == "wait_photo":
        if not message.photo:
            bot.send_message(message.chat.id, "Отправьте фото.")
            return

        file_id = message.photo[-1].file_id
        state["photo_id"] = file_id
        state["step"] = "count"
        save(data)

        bot.send_message(message.chat.id, "Введите количество показов рекламы:")
        return

    # === КОЛИЧЕСТВО ПОКАЗОВ ===
    if step == "count":
        if not message.text.isdigit():
            bot.send_message(message.chat.id, "Введите число.")
            return

        state["count"] = int(message.text)
        state["step"] = "report"
        save(data)

        # Выбор частоты отчётов
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Каждые 10", callback_data="ads_rep_10"),
            InlineKeyboardButton("Каждые 50", callback_data="ads_rep_50")
        )
        kb.add(
            InlineKeyboardButton("Каждые 100", callback_data="ads_rep_100"),
            InlineKeyboardButton("Только по завершению", callback_data="ads_rep_finish")
        )

        bot.send_message(message.chat.id, "Как часто уведомлять об успешных показах?", reply_markup=kb)
        return

# ==============================
# CALLBACK обработчик
# ==============================
def callback(bot, call):
    user = str(call.from_user.id)
    data = load()
    state = data["pending"].get(user)

    if call.data == "ads_add_photo":
        state["step"] = "wait_photo"
        save(data)
        bot.edit_message_text("Отправьте фото:", call.message.chat.id, call.message.message_id)
        return

    if call.data == "ads_no_photo":
        state["photo_id"] = None
        state["step"] = "count"
        save(data)
        bot.edit_message_text("Введите количество показов:", call.message.chat.id, call.message.message_id)
        return

    # Частота отчётов
    if call.data.startswith("ads_rep_"):
        rep = call.data.replace("ads_rep_", "")
        state["report"] = rep
        state["step"] = "preview"
        save(data)

        # Показываем предпросмотр
        preview = f"📢 *Предпросмотр рекламы:*\n\n{state['text']}\n\nПоказов: {state['count']}\nОтчёты: {rep}"
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Все верно", callback_data="ads_ok"),
            InlineKeyboardButton("Изменить текст", callback_data="ads_edit_text")
        )
        kb.add(
            InlineKeyboardButton("Изменить фото", callback_data="ads_edit_photo"),
            InlineKeyboardButton("Изменить количество", callback_data="ads_edit_count")
        )

        if state["photo_id"]:
            bot.send_photo(call.message.chat.id, state["photo_id"], preview, reply_markup=kb, parse_mode="Markdown")
        else:
            bot.edit_message_text(preview, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    # === Исправления ===
    if call.data == "ads_edit_text":
        state["step"] = "text"
        save(data)
        bot.edit_message_text("Введите новый текст:", call.message.chat.id, call.message.message_id)
        return

    if call.data == "ads_edit_photo":
        state["step"] = "wait_photo"
        save(data)
        bot.edit_message_text("Отправьте новое фото:", call.message.chat.id, call.message.message_id)
        return

    if call.data == "ads_edit_count":
        state["step"] = "count"
        save(data)
        bot.edit_message_text("Введите количество показов:", call.message.chat.id, call.message.message_id)
        return

    # === ОТПРАВКА НА АДМИН-ПРОВЕРКУ ===
    if call.data == "ads_ok":
        ad = state.copy()
        ad["owner"] = user

        # Отсылаем админу
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Одобрить", callback_data=f"ads_admin_ok_{user}"),
            InlineKeyboardButton("Отклонить", callback_data=f"ads_admin_no_{user}")
        )

        if ad["photo_id"]:
            bot.send_photo(ADMIN_ID, ad["photo_id"], f"Новая реклама от {user}:", reply_markup=kb)
        else:
            bot.send_message(ADMIN_ID, f"Новая реклама от {user}:\n\n{ad['text']}", reply_markup=kb)

        bot.edit_message_text("Реклама отправлена на проверку.", call.message.chat.id, call.message.message_id)

        return

    # === АДМИН ПРИНЯЛ ===
    if call.data.startswith("ads_admin_ok_"):
        target = call.data.replace("ads_admin_ok_", "")

        ad = data["pending"][target]

        # Перенос в актив
        data["active_ads"].append(ad)
        del data["pending"][target]
        save(data)

        bot.edit_message_text("Реклама одобрена.", call.message.chat.id, call.message.message_id)

        bot.send_message(target, "Ваша реклама одобрена и запущена!")
        return

    # === АДМИН ОТКЛОНИЛ ===
    if call.data.startswith("ads_admin_no_"):
        target = call.data.replace("ads_admin_no_", "")
        del data["pending"][target]
        save(data)

        bot.edit_message_text("Реклама отклонена.", call.message.chat.id, call.message.message_id)
        bot.send_message(target, "❌ Ваша реклама отклонена.")
        return


# ==============================
# ВСТАВКА РЕКЛАМЫ В ДИАЛОГ
# ==============================
def attach_ad(bot, chat_id):
    data = load()
    ads_list = data["active_ads"]

    if not ads_list:
        return

    # Достаём первую рекламу с очереди (чередование)
    ad = ads_list.pop(0)
    save(data)

    # Уменьшаем количество показов
    ad["count"] -= 1

    # Показ
    if ad["photo_id"]:
        bot.send_photo(chat_id, ad["photo_id"], ad["text"])
    else:
        bot.send_message(chat_id, ad["text"])

    # Если есть отчеты
    rep = ad["report"]
    original_total = ad.get("original", ad["count"])

    if rep != "finish":
        threshold = int(rep)
        done = (original_total - ad["count"])
        if done % threshold == 0:
            bot.send_message(ad["owner"], f"📊 Ваша реклама показана {done} раз.")

    # Реклама закончилась
    if ad["count"] > 0:
        ads_list.append(ad)
    else:
        bot.send_message(ad["owner"], "✅ Ваша реклама полностью откручена.")

    save({"pending": data["pending"], "price": data["price"], "active_ads": ads_list})