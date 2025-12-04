# plugins/hui.py
from .common import weighted_random, german_date, get_name
from .top_plugin import ensure_user, update_stat, update_date, was_today, load
from .bust_price import load_price
from telebot.types import LabeledPrice

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

def weighted_boost_positive():
    r = __import__("random").randint(1,100)
    if r <= 65:
        return __import__("random").randint(1,5)
    elif r <= 85:
        return __import__("random").randint(6,8)
    else:
        return __import__("random").randint(9,10)

def handle_successful(bot, message):
    payload = getattr(message.successful_payment, "invoice_payload", "") or ""
    if not payload.startswith("boost:hui:"):
        return
    try:
        _, _, chat_s, payer_s = payload.split(":")
        chat_id = int(chat_s); payer_id = int(payer_s)
    except:
        return

    dummy_user = type("U",(object,),{"id": payer_id})
    ensure_user(chat_id, dummy_user)
    boost = weighted_boost_positive()
    update_stat(chat_id, dummy_user, "hui", boost)
    data = load()
    new_size = data[str(chat_id)][str(payer_id)]["hui"]
    name = data[str(chat_id)][str(payer_id)]["name"]
    bot.send_message(chat_id, f"🎉 {name}, твой буст: +{boost} см, теперь — {new_size} см 🍌")

def handle(bot, message):
    text = (message.text or "").strip()
    if not text:
        return
    cmd_raw = text.split()[0].lower()
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw
    chat_id = message.chat.id
    uid = message.from_user.id
    name = get_name(message.from_user)

    if cmd == "/hui":
        ensure_user(chat_id, message.from_user)
        if was_today(chat_id, message.from_user, "last_hui"):
            data = load()
            current = data[str(chat_id)][str(uid)]["hui"]
            bot.reply_to(message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твое достоинство сейчас {current} см 😳 🍌"
            )
            return

        delta = weighted_random()
        update_stat(chat_id, message.from_user, "hui", delta)
        update_date(chat_id, message.from_user, "last_hui")
        data = load()
        new_size = max(0, data[str(chat_id)][str(uid)]["hui"])
        sign = f"{delta:+d}"
        bot.reply_to(message,
            f"{name}, твой хуй вырос на {sign} см, теперь он {new_size} см 😳 🍌"
        )
        return

    if cmd == "/boosth":
        price = load_price()
        if price <= 0:
            bot.reply_to(message, "Буст бесплатный — просто используй /hui")
            return
        payload = f"boost:hui:{chat_id}:{uid}"
        prices = [LabeledPrice("Boost Hui", price)]
        try:
            bot.send_invoice(
                chat_id=chat_id,
                title="Boost Hui",
                description=f"{name} покупает буст хуя",
                invoice_payload=payload,
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка при выставлении счёта: {e}")