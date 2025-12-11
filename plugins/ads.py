# plugins/ads.py
import json
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

DATA_FILE = "plugins/ads_data.json"
PROVIDER_TOKEN = os.environ.get("PROVIDER_TOKEN")  # required for invoices
# Админы (личные) — добавь/убери id по потребности
ADMINS = [5791171535, 5037660983]
# Админские чаты (numeric ids). Если хочешь — добавь сюда id группового админ-чата.
ADMIN_CHATS = []  # e.g. [-1001234567890]

# default price (звезды) за 1 показ
DEFAULT_PRICE = 1.0

# -----------------------------
def load_ads():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {"pending": {}, "approved": [], "price": DEFAULT_PRICE, "stats": {}}
    return {"pending": {}, "approved": [], "price": DEFAULT_PRICE, "stats": {}}

def save_ads(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------
# /buy_ads — старт процесса (в ЛС)
def handle_buy(bot, message):
    if message.chat.type != "private":
        bot.send_message(message.chat.id, "❌ Реклама работает только в личных сообщениях с ботом.")
        return
    user_id = str(message.from_user.id)
    data = load_ads()

    # ограничение — не более одной активной заявки у одного пользователя
    if user_id in data.get("pending", {}):
        bot.send_message(message.chat.id, "У вас уже есть заявка в обработке. Завершите её или отмените.")
        return

    # создаём заготовку
    data["pending"][user_id] = {
        "step": "text",
        "user_id": int(user_id),
        "user_name": message.from_user.username or message.from_user.first_name or "пользователь",
        "created_at": int(time.time())
    }
    save_ads(data)
    bot.send_message(message.chat.id, "✏️ Введите текст вашей рекламы (одно сообщение).")

# -----------------------------
# Универсальный message handler для ЛС (и админов при ожидании)
def handle(bot, message):
    """
    Используется для обработки состояния покупки/редактирования рекламы.
    main.py должен направлять сюда личные сообщения пользователей, которые находятся в pending.
    """
    # работаем только в ЛС (процесс покупки проходит в ЛС)
    if message.chat.type != "private":
        return

    user_id = str(message.from_user.id)
    data = load_ads()

    # special: админ присылает /priser <price> или /priser <price> <user_id> -> handled in handle_price
    # здесь обрабатываем только users в pending
    if user_id not in data.get("pending", {}):
        # но также поддерживаем админский ввод цены для сделки, если админ в состоянии awaiting_price
        # handled via handle_price command, not here
        return

    ad = data["pending"][user_id]

    # step: text
    if ad.get("step") == "text":
        text = (message.text or "").strip()
        if not text:
            bot.send_message(message.chat.id, "❌ Текст пустой. Введите текст рекламы (одно сообщение).")
            return
        ad["text"] = text
        ad["step"] = "photo"
        save_ads(data)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"ads_photo_yes_{user_id}"))
        kb.add(InlineKeyboardButton("Пропустить (без фото)", callback_data=f"ads_photo_no_{user_id}"))
        bot.send_message(message.chat.id, "Хотите прикрепить фото к рекламе?", reply_markup=kb)
        return

    # step: photo
    if ad.get("step") == "photo":
        # If user sent a photo — store it; if not (and user clicked 'no photo'), we already set
        if message.content_type == "photo":
            ad["photo"] = message.photo[-1].file_id
            # move to count
            ad["step"] = "count"
            save_ads(data)
            bot.send_message(message.chat.id, "📊 Сколько показов нужно отправить? Введите число (например, 10).")
            return
        else:
            # user might click "Пропустить" and then send text — ignore here
            bot.send_message(message.chat.id, "❗ Отправьте фото или нажмите кнопку 'Пропустить'.")
            return

    # step: count
    if ad.get("step") == "count":
        txt = (message.text or "").strip()
        try:
            count = int(txt)
            if count <= 0:
                raise ValueError()
            ad["count"] = count
            # default notification policy -> only on finish
            ad["notify_every"] = None  # can be set via buttons below
            ad["step"] = "confirm"
            save_ads(data)
            # show confirmation with options for notifications
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ Всё верно — опубликовать", callback_data=f"ads_confirm_{user_id}"))
            kb.add(InlineKeyboardButton("✏️ Изменить текст", callback_data=f"ads_change_text_{user_id}"))
            kb.add(InlineKeyboardButton("🖼️ Изменить фото", callback_data=f"ads_change_photo_{user_id}"))
            kb.add(InlineKeyboardButton("🔢 Изменить количество", callback_data=f"ads_change_count_{user_id}"))
            # notification options
            kb2 = InlineKeyboardMarkup()
            kb2.add(InlineKeyboardButton("Уведомлять каждые 10", callback_data=f"ads_notify_10_{user_id}"))
            kb2.add(InlineKeyboardButton("Уведомлять каждые 50", callback_data=f"ads_notify_50_{user_id}"))
            kb2.add(InlineKeyboardButton("Уведомлять каждые 100", callback_data=f"ads_notify_100_{user_id}"))
            kb2.add(InlineKeyboardButton("Уведомлять только по завершению", callback_data=f"ads_notify_end_{user_id}"))
            # send preview (photo if exists)
            preview = f"📩 Проверьте вашу рекламу:\n\n{ad['text']}\n\n📊 Показов: {ad['count']}\n\nВыберите частоту уведомлений или подтвердите публикацию."
            if ad.get("photo"):
                bot.send_photo(int(user_id), ad["photo"], caption=preview, reply_markup=kb)
            else:
                bot.send_message(int(user_id), preview, reply_markup=kb)
            # send notification options separately (so buttons don't clutter preview)
            bot.send_message(int(user_id), "Выберите, как часто уведомлять вас о прогрессе:", reply_markup=kb2)
            return
        except:
            bot.send_message(message.chat.id, "❌ Неверное число. Введите положительное целое число показов.")
            return

# -----------------------------
# Отправка подтверждения админу + пользователю (внутренняя fn)
def _notify_admin_new_ad(bot, user_id, ad):
    kb_admin = InlineKeyboardMarkup()
    kb_admin.add(InlineKeyboardButton("Одобрить", callback_data=f"ads_admin_approve_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Одобрить с ценой", callback_data=f"ads_admin_approve_price_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Отклонить (ввести комментарий)", callback_data=f"ads_admin_reject_{user_id}"))
    kb_admin.add(InlineKeyboardButton("Отменить", callback_data=f"ads_admin_cancel_{user_id}"))

    txt = f"📩 Новая реклама от @{ad.get('user_name') or ad.get('user_id')}:\n\n{ad.get('text')}\n\n📊 Показов: {ad.get('count')}\n🕒 id заявки: {user_id}"
    # send to personal admins
    if ad.get("photo"):
        for aid in ADMINS:
            try:
                bot.send_photo(aid, ad["photo"], caption=txt, reply_markup=kb_admin)
            except Exception as e:
                print("ads: error sending admin photo:", e)
    else:
        for aid in ADMINS:
            try:
                bot.send_message(aid, txt, reply_markup=kb_admin)
            except Exception as e:
                print("ads: error sending admin msg:", e)
    # send to admin chats if any
    for chat in ADMIN_CHATS:
        try:
            if ad.get("photo"):
                bot.send_photo(chat, ad["photo"], caption=txt, reply_markup=kb_admin)
            else:
                bot.send_message(chat, txt, reply_markup=kb_admin)
        except Exception as e:
            print("ads: error sending to admin chat:", e)

# -----------------------------
# Callback handler
def handle_callback(bot, call):
    """
    callback_data patterns:
    ads_photo_yes_<user_id>, ads_photo_no_<user_id>
    ads_confirm_<user_id>, ads_change_text_<user_id>, ads_change_photo_<user_id>, ads_change_count_<user_id>
    ads_notify_10_<user_id> / ads_notify_50_... / ads_notify_100_... / ads_notify_end_...
    admin callbacks:
      ads_admin_approve_<user_id>
      ads_admin_approve_price_<user_id>
      ads_admin_reject_<user_id>
      ads_admin_cancel_<user_id>
      ads_setprice_<user_id>_<price>  (used if admin sets price via command)
    """
    data = load_ads()
    parts = call.data.split("_")
    if len(parts) < 3:
        bot.answer_callback_query(call.id, "❌ Некорректный callback")
        return
    prefix = parts[0]
    typ = parts[1]
    # extract user id (last part)
    user_id = parts[-1]

    # ensure pending exists
    if user_id not in data.get("pending", {}) and typ.startswith("confirm") == False and not typ.startswith("admin"):
        bot.answer_callback_query(call.id, "❌ Заявка не найдена или уже обработана.")
        return

    # --- handle photo choice ---
    if typ == "photo":
        # parts: ads_photo_yes_USER or ads_photo_no_USER -> parts[2] is yes/no
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        if parts[2] == "yes":
            data["pending"][user_id]["step"] = "photo"
            save_ads(data)
            bot.send_message(int(user_id), "📸 Отправьте фото для рекламы:")
        else:
            # skip photo
            data["pending"][user_id]["step"] = "count"
            save_ads(data)
            bot.send_message(int(user_id), "📊 Введите количество показов рекламы (например, 10):")
        bot.answer_callback_query(call.id)
        return

    # --- confirmation / change ---
    if typ in ("confirm", "change"):
        action = parts[1] if parts[1] else ""
        # change actions: ads_change_text_USER etc
    # direct patterns e.g. ads_confirm_USER
    if typ == "confirm":
        # user confirmed and now we notify admins for moderation
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        ad = data["pending"][user_id]
        # mark waiting moderation
        ad["status"] = "awaiting_moderation"
        save_ads(data)
        bot.send_message(int(user_id), "⏳ Заявка отправлена на модерацию. Ожидайте решения администратора.")
        # notify admins
        _notify_admin_new_ad(bot, user_id, ad)
        bot.answer_callback_query(call.id, "Отправлено на модерацию")
        return

    if typ == "change":
        # patterns: ads_change_text_USER / ads_change_photo_USER / ads_change_count_USER
        sub = parts[1]  # actually 'change'
        # get the ending e.g. 'text' is parts[2] sometimes if format 'ads_change_text_userid' (we used that)
        # we built callback as ads_change_text_USERID -> so parts[2] == 'text'
        if len(parts) >= 4:
            what = parts[2]
        else:
            # fallback: try to parse 'ads_change_text_USERID' -> parts[2] == 'text'
            what = parts[2] if len(parts) >= 3 else ""
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        if what == "text":
            data["pending"][user_id]["step"] = "text"
            save_ads(data)
            bot.send_message(int(user_id), "✏️ Введите новый текст для рекламы:")
            bot.answer_callback_query(call.id, "Введите новый текст")
            return
        if what == "photo":
            data["pending"][user_id]["step"] = "photo"
            save_ads(data)
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("Добавить фото", callback_data=f"ads_photo_yes_{user_id}"))
            kb.add(InlineKeyboardButton("Пропустить (без фото)", callback_data=f"ads_photo_no_{user_id}"))
            bot.send_message(int(user_id), "Хотите прикрепить фото?", reply_markup=kb)
            bot.answer_callback_query(call.id)
            return
        if what == "count":
            data["pending"][user_id]["step"] = "count"
            save_ads(data)
            bot.send_message(int(user_id), "🔢 Введите новое количество показов:")
            bot.answer_callback_query(call.id)
            return

    # notification choices: ads_notify_10_USER etc
    if typ == "notify":
        # parts like ['ads','notify','10','USER'] or we used ads_notify_10_USER -> parts[2] is '10' and last is user
        if len(parts) >= 4:
            every = parts[2]
        else:
            every = parts[2]  # if format different
        # set notify_every accordingly
        mapping = {"10":10, "50":50, "100":100, "end":None}
        val = mapping.get(every, None)
        data["pending"][user_id]["notify_every"] = val
        save_ads(data)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(int(user_id), f"✅ Частота уведомлений установлена: {'каждые '+str(val) if val else 'только по завершению'}.")
        bot.answer_callback_query(call.id)
        return

    # ---------------- admin actions ----------------
    if typ.startswith("admin"):
        # patterns: ads_admin_approve_USER, ads_admin_approve_price_USER, ads_admin_reject_USER, ads_admin_cancel_USER
        if len(parts) < 4:
            bot.answer_callback_query(call.id, "❌ Некорректный админский callback")
            return
        admin_action = parts[2]
        uid = parts[3]
        if uid not in data.get("pending", {}):
            bot.answer_callback_query(call.id, "❌ Заявка уже обработана или не найдена.")
            return
        ad = data["pending"][uid]

        # approve straightforward
        if admin_action == "approve":
            # remove buttons
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except:
                pass
            # move to approved queue and publish or invoice
            # check price
            price = data.get("price", DEFAULT_PRICE)
            ad_record = ad.copy()
            ad_record["approved_at"] = int(time.time())
            ad_record["price_per_show"] = price
            data.setdefault("approved", []).append(ad_record)
            del data["pending"][uid]
            save_ads(data)
            # notify admin and user
            bot.send_message(call.from_user.id, f"✅ Реклама {uid} одобрена по цене {price} ⭐/показ.")
            bot.send_message(int(uid), f"✅ Ваша реклама одобрена. Цена: {price} ⭐/показ. Ожидайте публикации. Если цена > 0 — вам придет счёт.")
            # if price > 0 -> send invoice to user for total cost
            total_cost = price * ad_record["count"]
            if price > 0 and PROVIDER_TOKEN:
                try:
                    amount = int(round(total_cost * 100))  # cents
                    prices = [LabeledPrice(label="Реклама", amount=amount)]
                    bot.send_invoice(chat_id=int(uid),
                                     title="Оплата рекламы",
                                     description=f"Реклама: {ad_record['text']}\nПоказов: {ad_record['count']}",
                                     invoice_payload=f"ads_pay:{uid}:{int(time.time())}",
                                     provider_token=PROVIDER_TOKEN,
                                     currency="USD",
                                     prices=prices)
                except Exception as e:
                    print("ads: invoice error", e)
            else:
                # if price == 0 -> message user immediately
                if price == 0:
                    bot.send_message(int(uid), "✅ Ваша реклама опубликована бесплатно.")
            bot.answer_callback_query(call.id, "Одобрено")
            return

        # approve with price -> ask admin to set price via /priser <price> <user_id>
        if admin_action == "approve" and False:
            pass

        if admin_action == "approve_price":
            # remove markup
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except:
                pass
            # instruct admin how to set price for this user
            bot.send_message(call.from_user.id, f"Введите цену для сделки и примените её командой:\n/priser <price> {uid}\nПример: /priser 0.5 {uid}")
            # persist awaiting_price
            data.setdefault("awaiting_price", {})[str(call.from_user.id)] = uid
            save_ads(data)
            bot.answer_callback_query(call.id, "Введите цену в ЛС")
            return

        if admin_action == "reject":
            # remove markup
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except:
                pass
            # mark user pending as rejected but keep so admin can send comment
            data["pending"][uid]["status"] = "rejected_needs_comment"
            save_ads(data)
            bot.send_message(call.from_user.id, f"Введите комментарий для пользователя {uid} (будет отправлен ему).")
            # store awaiting_comment state
            data.setdefault("awaiting_comment", {})[str(call.from_user.id)] = uid
            save_ads(data)
            bot.answer_callback_query(call.id, "Введи комментарий")
            return

        if admin_action == "cancel":
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except:
                pass
            # remove pending
            try:
                del data["pending"][uid]
                save_ads(data)
            except:
                pass
            bot.send_message(call.from_user.id, "Заявка отменена.")
            bot.send_message(int(uid), "❌ Ваша заявка была отменена администратором.")
            bot.answer_callback_query(call.id)
            return

    bot.answer_callback_query(call.id, "Обработано")

# -----------------------------
# admin command: set global price or set deal price
def handle_price(bot, message):
    """
    /priser                -> show current price (admin only)
    /priser <price>        -> set global price (admin only)
    /priser <price> <user_id> -> set price for particular pending user (admin only) and auto-approve (publish/invoice)
    Also supports admin finishing a 'awaiting_price' by sending just price in private after pressing approve_with_price.
    """
    if message.from_user.id not in ADMINS:
        bot.send_message(message.chat.id, "❌ Только администраторы могут менять прайс.")
        return
    parts = (message.text or "").split()
    data = load_ads()
    if len(parts) == 1:
        bot.send_message(message.chat.id, f"Текущий глобальный прайс: {data.get('price', DEFAULT_PRICE)} ⭐/показ")
        return
    # parse price
    try:
        price = float(parts[1])
    except:
        bot.send_message(message.chat.id, "❌ Неверное число. Пример: /priser 0.5")
        return

    # if third arg user_id -> set per-deal
    if len(parts) >= 3:
        uid = parts[2]
        if uid not in data.get("pending", {}):
            bot.send_message(message.chat.id, "❌ Заявка не найдена.")
            return
        # approve this pending with given price
        ad = data["pending"][uid]
        ad_record = ad.copy()
        ad_record["approved_at"] = int(time.time())
        ad_record["price_per_show"] = price
        data.setdefault("approved", []).append(ad_record)
        del data["pending"][uid]
        save_ads(data)
        bot.send_message(message.chat.id, f"✅ Сделка для {uid} одобрена по цене {price} ⭐/показ.")
        bot.send_message(int(uid), f"✅ Ваша реклама одобрена по цене {price} ⭐/показ. Ожидайте публикации.")
        # if price > 0 => invoice
        total_cost = price * ad_record["count"]
        if price > 0 and PROVIDER_TOKEN:
            try:
                amount = int(round(total_cost * 100))
                prices = [LabeledPrice(label="Реклама", amount=amount)]
                bot.send_invoice(chat_id=int(uid),
                                 title="Оплата рекламы",
                                 description=f"Реклама: {ad_record['text']}\nПоказов: {ad_record['count']}",
                                 invoice_payload=f"ads_pay:{uid}:{int(time.time())}",
                                 provider_token=PROVIDER_TOKEN,
                                 currency="USD",
                                 prices=prices)
            except Exception as e:
                print("ads: invoice error", e)
        else:
            if price == 0:
                bot.send_message(int(uid), "✅ Ваша реклама опубликована бесплатно.")
        return

    # otherwise set global price
    data['price'] = price
    save_ads(data)
    bot.send_message(message.chat.id, f"✅ Глобальная цена установлена: {price} ⭐/показ")

# -----------------------------
# show admin lists /all and /chats
def handle_admin_list(bot, message):
    if message.from_user.id not in ADMINS:
        return
    data = load_ads()
    pending = data.get("pending", {})
    approved = data.get("approved", [])
    txt = "📋 Рекламные задачи:\n\nPending:\n"
    if not pending:
        txt += "- Нет\n"
    else:
        for uid, ad in pending.items():
            txt += f"- {uid} @{ad.get('user_name')} : {ad.get('count', 0)} показов\n"
    txt += "\nApproved queue:\n"
    if not approved:
        txt += "- Нет\n"
    else:
        for i, ad in enumerate(approved):
            txt += f"{i+1}. @{ad.get('user_name')} — {ad.get('count',0)} показов, price {ad.get('price_per_show', data.get('price'))}\n"
    bot.send_message(message.chat.id, txt)

def handle_chats(bot, message):
    if message.from_user.id not in ADMINS:
        return
    data = load_ads()
    stats = data.get("stats", {})
    if not stats:
        bot.send_message(message.chat.id, "Нет статистики по чатам.")
        return
    txt = "📊 Статистика по чатам (показов):\n"
    for chat_id, val in stats.items():
        txt += f"{chat_id}: {val}\n"
    bot.send_message(message.chat.id, txt)

# -----------------------------
# Функция отправки рекламы при любом действии (main вызывает ads.send_random_ads(bot, chat_id))
def send_random_ads(bot, chat_id):
    data = load_ads()
    if not data.get("approved"):
        return
    # get first approved ad
    ad = data["approved"].pop(0)
    # send
    try:
        if ad.get("photo"):
            bot.send_photo(chat_id, ad["photo"], caption=ad["text"])
        else:
            bot.send_message(chat_id, ad["text"])
    except Exception as e:
        print("ads: send error:", e)
    # post-send bookkeeping
    ad["count"] = ad.get("count", 0) - 1
    # stats
    stats = data.setdefault("stats", {})
    stats[str(chat_id)] = stats.get(str(chat_id), 0) + 1
    # notify purchaser if needed
    purchaser = str(ad.get("user_id"))
    notify_every = ad.get("notify_every")
    sent = ad.get("_sent", 0) + 1
    ad["_sent"] = sent
    if notify_every and notify_every > 0 and sent % notify_every == 0:
        try:
            bot.send_message(int(purchaser), f"ℹ️ Отправлено {sent} из {ad.get('count',0)+sent} показов вашей рекламы.")
        except:
            pass
    # if done -> notify purchaser
    if ad["count"] <= 0:
        try:
            bot.send_message(int(purchaser), f"✅ Рекламная кампания завершена. Всего показов: {sent}.")
        except:
            pass
    else:
        # re-enqueue if still has counts
        data.setdefault("approved", []).append(ad)
    save_ads(data)

# -----------------------------
# Exported utility names:
# load_ads, save_ads, handle_buy, handle, handle_callback, handle_price, send_random_ads, handle_admin_list, handle_chats