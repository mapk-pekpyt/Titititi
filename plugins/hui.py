from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

STAT_NAME = "hui"
STAT_RU = ["хуй", "хуя"]

def handle(bot, message):
    text = (message.text or "").lower().strip()
    parts = text.split()

    chat = message.chat.id
    payer = message.from_user
    target = message.reply_to_message.from_user if message.reply_to_message else payer

    top_plugin.ensure_user(chat, target)

    # ---------- ежедневка ----------
    if parts[0] in ["/hui", "хуй"]:
        if top_plugin.was_today(chat, target, "last_hui"):
            cur = top_plugin.load()[str(chat)][str(target.id)]["hui"]
            return bot.reply_to(message, f"{get_name(target)}, уже играл — {cur} см 😳🍌")

        delta = max(weighted_random(), 0)
        top_plugin.update_stat(chat, target, "hui", delta)
        top_plugin.update_date(chat, target, "last_hui")

        new = top_plugin.load()[str(chat)][str(target.id)]["hui"]
        return bot.reply_to(message, f"{get_name(target)}, +{delta} см → {new} см 😳🍌")

    # ---------- БУСТ ----------
    if parts[0] == "буст" and len(parts) >= 2 and parts[1] in STAT_RU:
        n = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 1

        price = load_price()
        total = price * n

        if price <= 0:
            top_plugin.update_stat(chat, target, "hui", n)
            new = top_plugin.load()[str(chat)][str(target.id)]["hui"]
            return bot.reply_to(message, f"{get_name(target)}, +{n} см → {new} см 😳🍌")

        prices = [LabeledPrice(label="Boost Hui", amount=total)]
        bot.send_invoice(
            chat_id=chat,
            title="Буст хуя",
            description=f"{get_name(payer)} бустит хуй на +{n} см",
            invoice_payload=f"boost:{chat}:{target.id}:hui:{n}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )

def handle_successful(bot, message):
    payload = message.successful_payment.invoice_payload
    if not payload.startswith("boost:"):
        return

    _, chat, target, stat, n = payload.split(":")
    if stat != "hui":
        return

    chat = int(chat)
    target = int(target)
    n = int(n)

    fake_user = type("U", (), {"id": target, "first_name": "Игрок"})
    top_plugin.ensure_user(chat, fake_user)

    top_plugin.update_stat(chat, fake_user, "hui", n)
    new = top_plugin.load()[str(chat)][str(target)]["hui"]

    bot.send_message(chat, f"{get_name(fake_user)}, +{n} см → {new} см 😳🍌")