from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

STAT_NAME = "klitor"
STAT_RU = ["клитор", "клитора"]

def fmt(mm): 
    return f"{mm/10:.1f}"

def handle(bot, message):
    text = (message.text or "").lower().strip()
    parts = text.split()

    chat = message.chat.id
    payer = message.from_user
    target = message.reply_to_message.from_user if message.reply_to_message else payer

    top_plugin.ensure_user(chat, target)

    # ---------- ежедневка ----------
    if parts[0] in ["/klitor", "клитор"]:
        if top_plugin.was_today(chat, target, "last_klitor"):
            cur = top_plugin.load()[str(chat)][str(target.id)]["klitor"]
            return bot.reply_to(message, f"{get_name(target)}, уже играл — {fmt(cur)} см 😳🍑")

        delta = max(weighted_random(), 0)
        top_plugin.update_stat(chat, target, "klitor", delta)
        top_plugin.update_date(chat, target, "last_klitor")

        new = top_plugin.load()[str(chat)][str(target.id)]["klitor"]
        return bot.reply_to(message, f"{get_name(target)}, +{delta} мм → {fmt(new)} см 😳🍑")

    # ---------- БУСТ ----------
    if parts[0] == "буст" and len(parts) >= 2 and parts[1] in STAT_RU:
        n = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 1

        price = load_price()
        total = price * n

        if price <= 0:
            top_plugin.update_stat(chat, target, "klitor", n)
            new = top_plugin.load()[str(chat)][str(target.id)]["klitor"]
            return bot.reply_to(message, f"{get_name(target)}, +{n} мм → {fmt(new)} см 😳🍑")

        prices = [LabeledPrice(label="Boost Klitor", amount=total)]
        bot.send_invoice(
            chat_id=chat,
            title="Буст клитора",
            description=f"{get_name(payer)} бустит клитор на +{n} мм",
            invoice_payload=f"boost:{chat}:{target.id}:klitor:{n}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )

def handle_successful(bot, message):
    payload = message.successful_payment.invoice_payload
    if not payload.startswith("boost:"):
        return

    _, chat, target, stat, n = payload.split(":")
    if stat != "klitor":
        return

    chat = int(chat)
    target = int(target)
    n = int(n)

    fake_user = type("U", (), {"id": target, "first_name": "Игрок"})
    top_plugin.ensure_user(chat, fake_user)

    top_plugin.update_stat(chat, fake_user, "klitor", n)
    new = top_plugin.load()[str(chat)][str(target)]["klitor"]

    bot.send_message(chat, f"{get_name(fake_user)}, +{n} мм → {fmt(new)} см 😳🍑")