#import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

#DATA_FILE = "plugins/ads_data.json"

ADMIN_CHAT = -5037660983     # Админский чат
BASE_PRICE = 1.0             # цена за 1 показ
WAIT_PRICE = {}              # ожидание цены от админа


def load():
    if not os.path.exists(DATA_FILE):
        return {"pending": {}, "approved": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        #json.dump(data, f, indent=2, ensure_ascii=False)


# =====================================================
# /buy_ads  → пользователь создает заявку
# =====================================================
def handle_buy(bot, msg):
    uid = str(msg.from_user.id)
    data = load()

    data["pending"][uid] = {
        "step": "photo",
        "user": msg.from_user.username,
    }
    save(data)

    bot.send_message(uid, "📸 Отправьте фото вашей рекламы:")


# =====================================================
# Главная обработка сообщений
# =====================================================
def handle(bot, msg):
    uid = str(msg.from_user.id)
    data = load()

    if uid not in data["pending"]:
        return

    ad = data["pending"][uid]

    # ----------
    # Фото
    # ----------
    if ad["step"] == "photo":
        if msg.content_type != "photo":
            bot.send_message(uid, "Отправьте фото!")
            return

        ad["photo"] = msg.photo[-1].file_id
        ad["step"] = "count"
        save(data)
        bot.send_message(uid, "🔢 Введите количество показов:")
        return

    # ----------
    # Количество
    # ----------
    if ad["step"] == "count":
        try:
            count = int(msg.text)
            if count <= 0:
                raise Exception
        except:
            bot.send_message(uid, "Введите целое число.")
            return

        ad["count"] = count
        ad["approx"] = BASE_PRICE * count
        ad["step"] = "preview"
        save(data)

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Всё верно", callback_data=f"ads_confirm_{uid}"))
        kb.add(InlineKeyboardButton("📸 Изменить фото", callback_data=f"ads_change_photo_{uid}"))
        kb.add(InlineKeyboardButton("🔢 Изменить количество", callback_data=f"ads_change_count_{uid}"))
        kb.add(InlineKeyboardButton("❌ Отменить", callback_data=f"ads_cancel_{uid}"))

        bot.send_photo(
            uid,
            ad["photo"],
            caption=(
                f"📋 Предпросмотр:\n"
                f"Показы: {count}\n"
                f"💰 Примерная стоимость: {ad['approx']} Stars"
            ),
            reply_markup=kb
        )
        return


# =====================================================
# CALLBACK-и: пользователь → админ
# =====================================================
def handle_callback(bot, call):
    data = load()
    parts = call.data.split("_")
    action = parts[1]
    uid = parts[2]

    # --------------------------------------------------
    # ОТМЕНА ПОЛЬЗОВАТЕЛЕМ
    # --------------------------------------------------
    if action == "cancel":
        data["pending"].pop(uid, None)
        save(data)
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "❌ Заявка отменена.")
        return

    # --------------------------------------------------
    # ИЗМЕНЕНИЕ ФОТО
    # --------------------------------------------------
    if action == "change" and parts[2] == "photo":
        data["pending"][uid]["step"] = "photo"
        save(data)
        bot.answer_callback_query(call.id)
        bot.send_message(int(uid), "📸 Отправьте новое фото:")
        return

    # --------------------------------------------------
    # ИЗМЕНЕНИЕ КОЛИЧЕСТВА
    # --------------------------------------------------
    if action == "change" and parts[2] == "count":
        data["pending"][uid]["step"] = "count"
        save(data)
        bot.answer_callback_query(call.id)
        bot.send_message(int(uid), "🔢 Введите новое количество:")
        return

    # --------------------------------------------------
    # ВСЁ ВЕРНО → ОТПРАВИТЬ АДМИНАМ
    # --------------------------------------------------
    if action == "confirm":
        ad = data["pending"][uid]

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"ads_ok_{uid}"))
        kb.add(InlineKeyboardButton("💰 Одобрить с ценой", callback_data=f"ads_price_{uid}"))
        kb.add(InlineKeyboardButton("❌ Отклонить", callback_data=f"ads_reject_{uid}"))

        bot.send_photo(
            ADMIN_CHAT,
            ad["photo"],
            caption=(
                f"📢 Новая заявка!\n"
                f"👤 @{ad['user']}\n"
                f"ID: {uid}\n\n"
                f"Показы: {ad['count']}\n"
                f"💰 Примерная цена: {ad['approx']}"
            ),
            reply_markup=kb
        )

        bot.answer_callback_query(call.id)
        bot.send_message(int(uid), "📤 Заявка отправлена на модерацию!")
        save(data)
        return

    # --------------------------------------------------
    # ОТКЛОНЕНИЕ
    # --------------------------------------------------
    if action == "reject":
        bot.answer_callback_query(call.id)
        bot.send_message(int(uid), "❌ Ваша реклама отклонена.")
        data["pending"].pop(uid, None)
        save(data)
        return

    # --------------------------------------------------
    # ОДОБРИТЬ БЕЗ ИЗМЕНЕНИЯ ЦЕНЫ
    # --------------------------------------------------
    if action == "ok":
        ad = data["pending"][uid]
        price = ad["approx"]
        bot.answer_callback_query(call.id)
        send_payment(bot, uid, price)
        return

    # --------------------------------------------------
    # ОДОБРИТЬ С УСТАНОВКОЙ ЦЕНЫ
    # --------------------------------------------------
    if action == "price":
        WAIT_PRICE[call.from_user.id] = uid
        bot.answer_callback_query(call.id)
        bot.send_message(ADMIN_CHAT, f"Введите новую цену для заявки {uid}:")
        return


# =====================================================
# Админ вводит цену вручную
# =====================================================
def admin_set_price(bot, msg):
    admin = msg.from_user.id

    if admin not in WAIT_PRICE:
        return

    uid = WAIT_PRICE[admin]

    try:
        price = float(msg.text)
    except:
        bot.send_message(ADMIN_CHAT, "Введите корректное число.")
        return

    del WAIT_PRICE[admin]

    send_payment(bot, uid, price)
    bot.send_message(ADMIN_CHAT, f"💰 Цена {price} отправлена пользователю.")


# =====================================================
# ОТПРАВКА ОПЛАТЫ (Telegram Stars)
# =====================================================
def send_payment(bot, uid, stars_amount):
    stars = int(stars_amount * 100)  # Telegram Stars → integer
    prices = [LabeledPrice(label="Размещение рекламы", amount=stars)]

    bot.send_invoice(
        int(uid),
        title="Оплата рекламы",
        description="Оплата рекламной кампании",
        provider_token="5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA",
        currency="XTR",
        prices=prices,
        payload="ads_payment"
    )


# =====================================================
# После оплаты
# =====================================================
def handle_successful(bot, msg):
    uid = str(msg.from_user.id)
    data = load()
    if uid not in data["pending"]:
        return

    ad = data["pending"].pop(uid)
    data["approved"][uid] = ad
    save(data)

    bot.send_message(uid, "✅ Оплата получена! Ваша реклама поставлена в очередь.")