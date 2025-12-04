# plugins/sisi.py
from .common import weighted_random, german_date, get_name
from .top_plugin import ensure_user, update_stat, update_date, was_today, load
from .bust_price import load_price
from telebot.types import LabeledPrice

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

# вспомогательный: положительный взвешенный для буста
def weighted_boost_positive():
    r = __import__("random").randint(1,100)
    if r <= 65:
        return __import__("random").randint(1,5)
    elif r <= 85:
        return __import__("random").randint(6,8)
    else:
        return __import__("random").randint(9,10)

def handle_successful(bot, message):
    # payload: boost:sisi:{chat_id}:{payer_id}
    payload = getattr(message.successful_payment, "invoice_payload", "") or ""
    if not payload.startswith("boost:sisi:"):
        return
    try:
        _, _, chat_s, payer_s = payload.split(":")
        chat_id = int(chat_s); payer_id = int(payer_s)
    except:
        return

    # ensure and apply positive boost to payer
    # use top_plugin functions to update central data
    dummy_user = type("U",(object,),{"id": payer_id})
    ensure_user(chat_id, dummy_user)
    boost = weighted_boost_positive()
    update_stat(chat_id, dummy_user, "sisi", boost)
    # don't touch last_sisi date (boost is separate)
    data = load()
    new_size = data[str(chat_id)][str(payer_id)]["sisi"]
    name = data[str(chat_id)][str(payer_id)]["name"]
    bot.send_message(chat_id, f"🎉 {name}, твой буст: +{boost}, теперь твоя грудь {new_size} размера 😳🍒")

def handle(bot, message):
    text = (message.text or "").strip()
    if not text:
        return
    cmd_raw = text.split()[0].lower()
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw
    chat_id = message.chat.id
    uid = message.from_user.id
    name = get_name(message.from_user)

    # DAILY /sisi
    if cmd == "/sisi":
        ensure_user(chat_id, message.from_user)
        if was_today(chat_id, message.from_user, "last_sisi"):
            # get current
            data = load()
            current = data[str(chat_id)][str(uid)]["sisi"]
            bot.reply_to(message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твои вишенки сейчас {current} размера 😳🍒"
            )
            return

        delta = weighted_random()
        # update stat (update_stat will add delta)
        update_stat(chat_id, message.from_user, "sisi", delta)
        update_date(chat_id, message.from_user, "last_sisi")
        data = load()
        new_size = max(0, data[str(chat_id)][str(uid)]["sisi"])
        sign = f"{delta:+d}"
        bot.reply_to(message,
            f"{name}, твои сисечки выросли на {sign}, теперь твоя грудь {new_size} размера 😳🍒"
        )
        return

    # BOOST /boosts
    if cmd == "/boosts":
        price = load_price()
        if price <= 0:
            bot.reply_to(message, "Буст бесплатный — просто используй /sisi и получишь шанс.")
            return
        # invoice payload: boost:sisi:{chat_id}:{payer_id}
        payload = f"boost:sisi:{chat_id}:{uid}"
        prices = [LabeledPrice("Boost Sisi", price)]
        try:
            bot.send_invoice(
                chat_id=chat_id,
                title="Boost Sisi",
                description=f"{name} покупает буст сисек",
                invoice_payload=payload,
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка при выставлении счёта: {e}")