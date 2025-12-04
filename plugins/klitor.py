# plugins/klitor.py
from .common import weighted_random, german_date, get_name
from .top_plugin import ensure_user, update_stat, update_date, was_today, load
from .bust_price import load_price
from telebot.types import LabeledPrice

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

def mm_to_cm(mm: int) -> str:
    return f"{mm/10:.1f}"

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
    if not payload.startswith("boost:klitor:"):
        return
    try:
        _, _, chat_s, payer_s = payload.split(":")
        chat_id = int(chat_s); payer_id = int(payer_s)
    except:
        return

    dummy_user = type("U",(object,),{"id": payer_id})
    ensure_user(chat_id, dummy_user)
    boost_mm = weighted_boost_positive()
    # klitor stored in mm
    update_stat(chat_id, dummy_user, "klitor", boost_mm)
    data = load()
    new_mm = max(0, data[str(chat_id)][str(payer_id)]["klitor"])
    name = data[str(chat_id)][str(payer_id)]["name"]
    bot.send_message(chat_id, f"🎉 {name}, буст клитора: +{boost_mm} мм → {mm_to_cm(new_mm)} см 🍑")

def handle(bot, message):
    text = (message.text or "").strip()
    if not text:
        return
    cmd_raw = text.split()[0].lower()
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw
    chat_id = message.chat.id
    uid = message.from_user.id
    name = get_name(message.from_user)

    if cmd == "/klitor":
        ensure_user(chat_id, message.from_user)
        if was_today(chat_id, message.from_user, "last_klitor"):
            data = load()
            current_mm = data[str(chat_id)][str(uid)]["klitor"]
            bot.reply_to(message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твоя валына сейчас {mm_to_cm(current_mm)} см 😳 🍑"
            )
            return

        delta = weighted_random()
        # delta is in mm for klitor? earlier weighted_random returned ints; keep same units: treat as mm
        update_stat(chat_id, message.from_user, "klitor", delta)
        update_date(chat_id, message.from_user, "last_klitor")
        data = load()
        new_mm = max(0, data[str(chat_id)][str(uid)]["klitor"])
        sign = f"{delta:+d}"
        bot.reply_to(message,
            f"{name}, твой клитор вырос на {sign} мм, теперь он {mm_to_cm(new_mm)} см 😳 🍑"
        )
        return

    if cmd == "/boostk":
        price = load_price()
        if price <= 0:
            bot.reply_to(message, "Буст бесплатный — просто используй /klitor")
            return
        payload = f"boost:klitor:{chat_id}:{uid}"
        prices = [LabeledPrice("Boost Klitor", price)]
        try:
            bot.send_invoice(
                chat_id=chat_id,
                title="Boost Klitor",
                description=f"{name} покупает буст клитора",
                invoice_payload=payload,
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка при выставлении счёта: {e}")