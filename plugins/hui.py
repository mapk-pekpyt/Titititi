# plugins/hui.py
import os
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

def handle(bot, message):
    text = (message.text or "").strip()
    cmd_raw = text.split()[0].lower() if text else ""
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw

    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    top_plugin.ensure_user(chat, user)

    # ---------- ежедневная игра /hui ----------
    if cmd == "/hui":
        if top_plugin.was_today(chat, user, "last_hui"):
            data = top_plugin.load()
            current = data.get(str(chat), {}).get(str(user.id), {}).get("hui", 0)
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл со своим дружком, твой болтик сейчас {current} см 😳 🍌"
            )

        delta = weighted_random()
        if delta < 0:
            delta = 0

        top_plugin.update_stat(chat, user, "hui", delta)
        top_plugin.update_date(chat, user, "last_hui")

        data = top_plugin.load()
        new_size = data[str(chat)][str(user.id)]["hui"]

        bot.reply_to(
            message,
            f"{name}, твой хуй вырос на +{delta} см, теперь твой болт {new_size} см 😳🍌"
        )
        return

    # ---------- платный буст /boosth [n] ----------
    if cmd == "/boosth":
        parts = text.split()
        n = 1
        if len(parts) >= 2:
            try:
                n = max(int(parts[1]), 1)
            except:
                n = 1

        price = load_price()
        total = price * n

        if price <= 0:
            top_plugin.update_stat(chat, user, "hui", n)
            top_plugin.update_date(chat, user, "last_hui")
            data = top_plugin.load()
            new_size = data[str(chat)][str(user.id)]["hui"]
            return bot.reply_to(
                message,
                f"{name}, твой хуй вырос на +{n} см, теперь твой болт {new_size} см 😳🍌"
            )

        try:
            prices = [LabeledPrice(label="Boost Hui", amount=total)]
            bot.send_invoice(
                chat_id=chat,
                title="Буст хуя",
                description=f"{name} хочет увеличить хуй на +{n} см",
                invoice_payload=f"boost:{chat}:{user.id}:hui:{n}",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка оплаты: {e}")

def handle_successful(bot, message):
    if not hasattr(message, "successful_payment") or not message.successful_payment:
        return
    payload = getattr(message.successful_payment, "invoice_payload", "") or \
              getattr(message.successful_payment, "payload", "")
    if not payload.startswith("boost:"):
        return

    parts = payload.split(":")
    if len(parts) != 5:
        return
    _, chat_s, payer_s, stat, n_s = parts
    if stat != "hui":
        return

    try:
        chat_id = int(chat_s)
        payer_id = int(payer_s)
        n = int(n_s)
    except:
        return

    payer = message.from_user
    top_plugin.ensure_user(chat_id, payer)

    top_plugin.update_stat(chat_id, payer, "hui", n)
    top_plugin.update_date(chat_id, payer, "last_hui")

    data = top_plugin.load()
    new_size = data[str(chat_id)][str(payer.id)]["hui"]

    bot.send_message(chat_id, f"{get_name(payer)}, твой хуй вырос на +{n} см, теперь твой болт {new_size} см 😳🍌")