import os
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

def _format_klitor(mm: int) -> str:
    return f"{mm/10:.1f}"

def handle(bot, message):
    text = (message.text or "").strip()
    cmd_raw = text.split()[0].lower() if text else ""
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw

    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    # target_user (если ответ на сообщение)
    target_user = message.reply_to_message.from_user if message.reply_to_message else user
    top_plugin.ensure_user(chat, target_user)

    if cmd in ["/klitor", "клитор", "/boostk", "бустк"]:
        if target_user != user and load_price() > 0:
            n = 1
        else:
            # бесплатный буст
            if top_plugin.was_today(chat, target_user, "last_klitor"):
                data = top_plugin.load()
                current = data.get(str(chat), {}).get(str(target_user.id), {}).get("klitor", 0)
                return bot.reply_to(
                    message,
                    f"{get_name(target_user)}, ты уже играл сегодня! "
                    f"Твоя валына сейчас {_format_klitor(current)} см 😳🍑"
                )
            n = weighted_random()
            if n < 0:
                n = 0
            top_plugin.update_stat(chat, target_user, "klitor", n)
            top_plugin.update_date(chat, target_user, "last_klitor")
            data = top_plugin.load()
            new_mm = data[str(chat)][str(target_user.id)]["klitor"]
            return bot.reply_to(
                message,
                f"{get_name(target_user)}, твой клитор вырос на +{n} мм, теперь {_format_klitor(new_mm)} см 😳🍑"
            )

        # платный буст
        price = load_price()
        total = price * n
        try:
            prices = [LabeledPrice(label="Boost Klitor", amount=total)]
            bot.send_invoice(
                chat_id=chat,
                title="Буст клитора",
                description=f"{name} хочет увеличить клитор на +{n} мм",
                invoice_payload=f"boost:{chat}:{target_user.id}:klitor:{n}",
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

    _, chat_s, payer_s, stat, n_s = payload.split(":")
    if stat != "klitor":
        return

    chat_id = int(chat_s)
    target_id = int(payer_s)
    n = int(n_s)

    target_user = top_plugin.ensure_user(chat_id, type('User', (object,), {'id': target_id, 'first_name': 'Игрок'})())
    top_plugin.update_stat(chat_id, target_user, "klitor", n)
    top_plugin.update_date(chat_id, target_user, "last_klitor")

    data = top_plugin.load()
    new_mm = data[str(chat_id)][str(target_user.id)]["klitor"]
    bot.send_message(chat_id, f"{get_name(target_user)}, твой клитор вырос на +{n} мм, теперь {_format_klitor(new_mm)} см 😳🍑")