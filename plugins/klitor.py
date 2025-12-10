# plugins/klitor.py
import os
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

def _format_klitor(mm: int) -> str:
    # mm stored; display cm with one decimal: mm/10 -> 1.1 см
    return f"{mm/10:.1f}"

def handle(bot, message):
    text = (message.text or "").strip()
    cmd_raw = text.split()[0].lower() if text else ""
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw

    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    top_plugin.ensure_user(chat, user)

    # ---------- ежедневная игра /klitor ----------
    if cmd == "/klitor":
        if top_plugin.was_today(chat, user, "last_klitor"):
            data = top_plugin.load()
            current = data.get(str(chat), {}).get(str(user.id), {}).get("klitor", 0)
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твоя валына сейчас {_format_klitor(current)} см 😳 🍑"
            )

        delta = weighted_random()
        if delta < 0:
            delta = 0

        # delta is in 'units' where 1 unit == 1 mm (we store mm)
        top_plugin.update_stat(chat, user, "klitor", delta)
        top_plugin.update_date(chat, user, "last_klitor")

        data = top_plugin.load()
        new_mm = data[str(chat)][str(user.id)]["klitor"]

        bot.reply_to(
            message,
            f"{name}, твой клитор вырос на +{delta} мм, теперь у тебя валына целых {_format_klitor(new_mm)} см 😳🍑"
        )
        return

    # ---------- платный буст /boostk [n] ----------
    if cmd == "/boost":
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
            top_plugin.update_stat(chat, user, "klitor", n)
            top_plugin.update_date(chat, user, "last_klitor")
            data = top_plugin.load()
            new_mm = data[str(chat)][str(user.id)]["klitor"]
            return bot.reply_to(
                message,
                f"{name}, твой клитор вырос на +{n} мм, теперь у тебя валына целых {_format_klitor(new_mm)} см 😳🍑"
            )

        try:
            prices = [LabeledPrice(label="Boost Klitor", amount=total)]
            bot.send_invoice(
                chat_id=chat,
                title="Буст клитора",
                description=f"{name} хочет увеличить клитор на +{n} мм",
                invoice_payload=f"boost:{chat}:{user.id}:klitor:{n}",
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
    if stat != "klitor":
        return

    try:
        chat_id = int(chat_s)
        payer_id = int(payer_s)
        n = int(n_s)
    except:
        return

    payer = message.from_user
    top_plugin.ensure_user(chat_id, payer)

    top_plugin.update_stat(chat_id, payer, "klitor", n)
    top_plugin.update_date(chat_id, payer, "last_klitor")

    data = top_plugin.load()
    new_mm = data[str(chat_id)][str(payer.id)]["klitor"]

    bot.send_message(chat_id, f"{get_name(payer)}, твой клитор вырос на +{n} мм, теперь у тебя валына целых {_format_klitor(new_mm)} см 😳🍑")