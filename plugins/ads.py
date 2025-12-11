# plugins/ads.py
import os
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

DATA_FILE = "plugins/ads_data.json"
ADMIN_ID = 5791171535  # твой TG ID — ты сказал 5791171535

# -------------------------
# Хранилище
# -------------------------
def load():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "price": 1.0, "active_ads": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"pending": {}, "price": 1.0, "active_ads": []}

def save(data):
    os.makedirs(os.path.dirname(DATA_FILE) or ".", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------------
# Утилиты по клавиатурам
# -------------------------
def kb_yes_no(a="Да", b="Нет", da="ads_ok", db="ads_cancel"):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(a, callback_data=da),
           InlineKeyboardButton(b, callback_data=db))
    return kb

def kb_preview():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Всё верно", callback_data="ads_ok"),
           InlineKeyboardButton("✏️ Изменить текст", callback_data="ads_edit_text"))
    kb.add(InlineKeyboardButton("🖼️ Изменить фото", callback_data="ads_edit_photo"),
           InlineKeyboardButton("🔢 Изменить количество", callback_data="ads_edit_count"))
    return kb

def kb_admin_for_user(user_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Одобрить", callback_data=f"ads_admin_ok_{user_id}"),
           InlineKeyboardButton("Отклонить", callback_data=f"ads_admin_no_{user_id}"))
    return kb

def kb_report_options():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Каждые 10", callback_data="ads_rep_10"),
           InlineKeyboardButton("Каждые 50", callback_data="ads_rep_50"))
    kb.add(InlineKeyboardButton("Каждые 100", callback_data="ads_rep_100"),
           InlineKeyboardButton("Только по завершению", callback_data="ads_rep_finish"))
    return kb

# -------------------------
# /priser - установить цену (ADMIN)
# -------------------------
def handle_priser(bot, message):
    if message.chat.type != "private":
        bot.reply_to(message, "Команда доступна только в личке бота.")
        return

    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Только админ может менять цену.")
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        bot.reply_to(message, f"Текущая цена: {load()['price']} ⭐ за 1 показ. Укажите новую: /priser 0.1")
        return

    try:
        price = float(parts[1].replace(",", "."))
    except:
        bot.reply_to(message, "Ошибка: укажи число, например /priser 0.1")
        return

    data = load()
    data["price"] = price
    save(data)
    bot.reply_to(message, f"✅ Цена установлена: {price} ⭐ за 1 показ")

# -------------------------
# /buy_ads - старт диалога покупки (в личке)
# -------------------------
def handle_buy(bot, message):
    if message.chat.type != "private":
        bot.reply_to(message, "Запускай процесс в личке бота.")
        return

    user = str(message.from_user.id)
    data = load()
    data["pending"][user] = {
        "step": "text",       # text -> photo_choice -> wait_photo -> count -> report -> preview -> admin
        "text": None,
        "photo_id": None,
        "count": 0,
        "report": "finish"
    }
    save(data)
    bot.send_message(message.chat.id, f"Стоимость: {data['price']} ⭐ за 1 показ.\n\nОтправьте текст вашей рекламы (можно отправить фото с подписью — тогда подпись станет текстом).")

# -------------------------
# Основной шаговый хендлер (перехват сообщений в main)
# Пришёл текст/фото от user, который в pending
# -------------------------
def handle(bot, message):
    # работает только в личке
    if message.chat.type != "private":
        return

    user = str(message.from_user.id)
    data = load()
    if user not in data.get("pending", {}):
        return

    state = data["pending"][user]
    step = state.get("step")

    # если пользователь прислал фото и подписал — caption будет использоваться
    content = None
    if message.content_type == "photo":
        # если он в состоянии дать фото (wait_photo) — обработаем ниже
        content = message.caption or ""
    else:
        content = message.text or ""

    # STEP: текст
    if step == "text":
        if not content.strip():
            bot.send_message(message.chat.id, "Введите текст рекламы (не пусто).")
            return
        state["text"] = content.strip()
        state["step"] = "photo_choice"
        save(data)

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Добавить фото", callback_data="ads_add_photo"),
               InlineKeyboardButton("Без фото", callback_data="ads_no_photo"))

        bot.send_message(message.chat.id, "Хотите добавить фото к рекламе?", reply_markup=kb)
        return

    # STEP: waiting photo (если пользователь отправил фото when step=wait_photo)
    if step == "wait_photo":
        if message.content_type != "photo":
            bot.send_message(message.chat.id, "Отправьте фото или нажмите 'Без фото'.")
            return
        file_id = message.photo[-1].file_id
        state["photo_id"] = file_id
        state["step"] = "count"
        save(data)
        bot.send_message(message.chat.id, "Отлично. Введите количество показов (число):")
        return

    # STEP: count
    if step == "count":
        if not (message.text and message.text.strip().isdigit()):
            bot.send_message(message.chat.id, "Введите целое число показов (например 10):")
            return
        state["count"] = int(message.text.strip())
        state["step"] = "report"
        save(data)
        bot.send_message(message.chat.id, "Как часто уведомлять об успешных показах?", reply_markup=kb_report_options())
        return

    # Если пришло сообщение на других шагах — игнорируем
    return

# -------------------------
# callback handler — все inline-кнопки
# -------------------------
def callback(bot, call):
    user = str(call.from_user.id)
    data = load()

    # --- кнопки в личке пользователя, если он в pending ---
    if call.data == "ads_add_photo" or call.data == "ads_no_photo":
        # только владелец может пользоваться этими кнопками
        if user not in data.get("pending", {}):
            bot.answer_callback_query(call.id, "Это не ваше действие.")
            return

        state = data["pending"][user]

        # удаляем клавиатуру
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except:
            pass

        if call.data == "ads_add_photo":
            state["step"] = "wait_photo"
            save(data)
            bot.send_message(call.message.chat.id, "Отправьте фото (можно с подписью):")
            return
        else:
            state["photo_id"] = None
            state["step"] = "count"
            save(data)
            bot.send_message(call.message.chat.id, "Введите количество показов (число):")
            return

    # --- частота отчетов ---
    if call.data.startswith("ads_rep_"):
        if user not in data.get("pending", {}):
            bot.answer_callback_query(call.id, "Это не ваше действие.")
            return
        state = data["pending"][user]
        rep = call.data.replace("ads_rep_", "")
        state["report"] = rep
        state["step"] = "preview"
        save(data)

        # удаляем клавиатуру
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except:
            pass

        # отправляем предпросмотр
        preview_text = f"📢 *Предпросмотр рекламы*\n\n{state['text']}\n\nПоказов: {state['count']}\nОтчёты: {rep}\n\nЦена за показ: {data.get('price',1)} ⭐"
        if state.get("photo_id"):
            bot.send_photo(call.message.chat.id, state["photo_id"], preview_text, parse_mode="Markdown", reply_markup=kb_preview())
        else:
            bot.send_message(call.message.chat.id, preview_text, parse_mode="Markdown", reply_markup=kb_preview())
        return

    # --- редактирование текста / фото / кол-ва ---
    if call.data in ("ads_edit_text", "ads_edit_photo", "ads_edit_count"):
        if user not in data.get("pending", {}):
            bot.answer_callback_query(call.id, "Это не ваше действие.")
            return
        state = data["pending"][user]
        # удаляем клавиатуру
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except:
            pass

        if call.data == "ads_edit_text":
            state["step"] = "text"
            save(data)
            bot.send_message(call.message.chat.id, "Введите новый текст рекламы:")
            return
        if call.data == "ads_edit_photo":
            state["step"] = "wait_photo"
            save(data)
            bot.send_message(call.message.chat.id, "Отправьте новое фото (или нажмите 'Без фото' в предыдущем шаге):")
            return
        if call.data == "ads_edit_count":
            state["step"] = "count"
            save(data)
            bot.send_message(call.message.chat.id, "Введите новое количество показов (число):")
            return

    # --- пользователь подтвердил — отправляем админу ---
    if call.data == "ads_ok":
        if user not in data.get("pending", {}):
            bot.answer_callback_query(call.id, "Это не ваше действие.")
            return
        state = data["pending"][user]
        # удаляем клавиатуру
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except:
            pass

        # прикрутим поле original = count для отсчёта
        ad = {
            "owner": user,
            "text": state.get("text"),
            "photo_id": state.get("photo_id"),
            "count": state.get("count"),
            "original": state.get("count"),
            "report": state.get("report")
        }

        # отправляем админу на проверку (кнопки только у админа)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Одобрить", callback_data=f"ads_admin_ok_{user}"),
               InlineKeyboardButton("Отклонить", callback_data=f"ads_admin_no_{user}"))

        if ad["photo_id"]:
            bot.send_photo(ADMIN_ID, ad["photo_id"], f"Новая реклама от {user}:\n\n{ad['text']}", reply_markup=kb)
        else:
            bot.send_message(ADMIN_ID, f"Новая реклама от {user}:\n\n{ad['text']}", reply_markup=kb)

        bot.send_message(call.message.chat.id, "Реклама отправлена на проверку администратора.")
        return

    # --- админ отклонил/одобрил ---
    if call.data.startswith("ads_admin_ok_") or call.data.startswith("ads_admin_no_"):
        # только админ может нажимать админ-кнопки
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Только админ может выполнить это действие.")
            return

        # получаем target
        if call.data.startswith("ads_admin_ok_"):
            target = call.data.replace("ads_admin_ok_", "")
            # проверим, есть ли pending у target
            if target not in data.get("pending", {}):
                bot.answer_callback_query(call.id, "Заявка уже обработана.")
                try:
                    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                except:
                    pass
                return

            # перевести в active_ads
            ad = data["pending"].pop(target)
            # add fields owner/original/report ensured
            active_entry = {
                "owner": target,
                "text": ad.get("text"),
                "photo_id": ad.get("photo_id"),
                "count": ad.get("count"),
                "original": ad.get("count"),
                "report": ad.get("report")
            }
            data.setdefault("active_ads", []).append(active_entry)
            save(data)

            # удаляем кнопки у сообщения у админа и подтверждаем
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except:
                pass
            bot.send_message(call.message.chat.id, "Реклама одобрена и поставлена в очередь.")
            # уведомляем владельца
            bot.send_message(int(target), "✅ Ваша реклама одобрена и запущена.")
            return

        else:
            # админ отклонил
            target = call.data.replace("ads_admin_no_", "")
            if target in data.get("pending", {}):
                data["pending"].pop(target)
                save(data)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except:
                pass
            bot.send_message(call.message.chat.id, "Реклама отклонена.")
            bot.send_message(int(target), "❌ Ваша реклама отклонена администратором.")
            return

    # --- пользователь нажал "отмена" или др. ---
    if call.data == "ads_cancel":
        if user in data.get("pending", {}):
            data["pending"].pop(user)
            save(data)
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except:
            pass
        bot.send_message(call.message.chat.id, "Процесс рекламы отменён.")
        return

    # прочие callback'и — игнор
    bot.answer_callback_query(call.id, "Нажатие обработано.")

# -------------------------
# attach_ad - вставка рекламы в чат (вызывается из main, после отправки сообщения ботом)
# -------------------------
def attach_ad(bot, chat_id):
    data = load()
    ads_list = data.get("active_ads", [])
    if not ads_list:
        return

    # берем рекламу циклично
    ad = ads_list.pop(0)

    # Сколько показов осталось?
    if ad.get("count", 0) <= 0:
        # пропускаем (не добавляем назад)
        save(data)
        return

    # отправляем рекламу
    try:
        if ad.get("photo_id"):
            bot.send_photo(chat_id, ad["photo_id"], ad.get("text") or "")
        else:
            bot.send_message(chat_id, ad.get("text") or "")
    except Exception as e:
        # не падаем
        print("ads.attach_ad send error:", e)

    # уменьшаем счётчик
    ad["count"] = ad.get("count", 0) - 1

    # уведомления владельцу по порогу
    rep = ad.get("report", "finish")
    if rep != "finish":
        try:
            threshold = int(rep)
        except:
            threshold = None
        if threshold:
            shown = ad.get("original", 0) - ad.get("count", 0)
            if shown > 0 and shown % threshold == 0:
                try:
                    bot.send_message(int(ad["owner"]), f"📊 Ваша реклама показана {shown} раз.")
                except:
                    pass

    # если остался показ — добавить назад в очередь
    if ad["count"] > 0:
        ads_list.append(ad)
    else:
        try:
            bot.send_message(int(ad["owner"]), "✅ Ваша реклама полностью отработана.")
        except:
            pass

    data["active_ads"] = ads_list
    save(data)