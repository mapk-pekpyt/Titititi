# plugins/mut.py
import os
import json
from datetime import datetime, timedelta
from telebot.types import ChatPermissions, LabeledPrice

DATA_FILE = "data/price.json"
DEFAULT_PRICE = 2
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"
ADMIN_ID = 5791171535


# --------- Имена ---------
def get_name(user):
    fn = getattr(user, "first_name", None)
    ln = getattr(user, "last_name", None)

    if fn and ln:
        return f"{fn} {ln}"
    if fn:
        return fn
    return "Пользователь"


def get_name_by_id(bot, chat_id, user_id):
    try:
        m = bot.get_chat_member(chat_id, user_id).user
        return get_name(m)
    except:
        return "Пользователь"


# --------- ЦЕНА ---------
def ensure_data_dir():
    d = os.path.dirname(DATA_FILE)
    if d:
        os.makedirs(d, exist_ok=True)

def load_price():
    ensure_data_dir()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f).get("price", DEFAULT_PRICE))
    except:
        return DEFAULT_PRICE

def save_price(v):
    ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"price": int(v)}, f)


# --------- МУТ ---------
def apply_mute(bot, chat_id, target_id, minutes):
    until_ts = int((datetime.utcnow() + timedelta(minutes=minutes)).timestamp())

    perms = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )

    bot.restrict_chat_member(chat_id, target_id, permissions=perms, until_date=until_ts)


# --------- УСПЕШНАЯ ОПЛАТА ---------
def handle_successful(bot, message):
    payload = getattr(message.successful_payment, "invoice_payload", "") or \
              getattr(message.successful_payment, "payload", "")

    if not payload.startswith("mut:"):
        return

    _, chat_id_s, payer_id_s, target_id_s, minutes_s = payload.split(":")

    chat_id = int(chat_id_s)
    payer_id = int(payer_id_s)
    target_id = int(target_id_s)
    minutes = int(minutes_s)

    price_per_min = load_price()

    payer = get_name_by_id(bot, chat_id, payer_id)
    target = get_name_by_id(bot, chat_id, target_id)

    # выдаём мут
    apply_mute(bot, chat_id, target_id, minutes)

    # отправляем ОДНО сообщение в зависимости от цены
    if price_per_min <= 0:
        bot.send_message(
            chat_id,
            f"🔇 {target}, ну ты и лошара… {payer} велел заткнуть тебя, видимо ты всех заебал🥲"
        )
    else:
        bot.send_message(
            chat_id,
            f"🔇 {target}, ну ты и лошара🤣 {payer} велел завалить твой пиздак, "
            f"видимо ты его так заебал что он оплатил твоё молчание💰"
        )


# --------- ОБРАБОТЧИК КОМАНД ---------
def handle(bot, message):
    text = (message.text or "").strip()
    if not text:
        return

    cmd_raw = text.split()[0].lower()
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw

    # ----- /price -----
    if cmd == "/price":
        parts = text.split()

        # показать цену
        if len(parts) == 1:
            bot.reply_to(message, f"💰 Текущая цена: {load_price()} ⭐ за минуту.")
            return

        # изменить цену
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ Только админ может менять цену.")
            return

        try:
            new_price = int(parts[1])
            save_price(new_price)
            bot.reply_to(message, f"✅ Цена обновлена: {new_price} ⭐ за минуту.")
        except:
            bot.reply_to(message, "❗ Используй: /price 3")
        return

    # ----- /mut -----
    if cmd != "/mut":
        return

    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Ответь на сообщение того, кого хочешь замутить.\nПример: /mut 5")
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
        bot.reply_to(message, "❗ Минуты должны быть > 0")
        return

    payer_name = get_name(message.from_user)
    target_name = get_name(message.reply_to_message.from_user)

    price_per_min = load_price()
    total_stars = price_per_min * minutes

    # бесплатный мут
    if price_per_min <= 0:
        apply_mute(bot, message.chat.id, message.reply_to_message.from_user.id, minutes)
        bot.send_message(
            message.chat.id,
            f"🔇 {target_name}, ну ты и лошара… {payer_name} велел заткнуть тебя, видимо ты всех заебал🥲"
        )
        return

    # платный мут — инвойс
    try:
        prices = [LabeledPrice(label="Mute", amount=total_stars)]

        bot.send_invoice(
            chat_id=message.chat.id,
            title=f"Мут для {target_name}",
            description=f"{payer_name} хочет замутить {target_name} на {minutes} минут.",
            invoice_payload=f"mut:{message.chat.id}:{message.from_user.id}:{message.reply_to_message.from_user.id}:{minutes}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка оплаты: {e}")