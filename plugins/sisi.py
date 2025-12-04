from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from .bust_price import load_price

def handle(bot, message):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)
    data = ensure_user(chat, user)

    text = (message.text or "").strip().lower()
    cmd_raw = text.split()[0]
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw

    # --------- /sisi (ежедневная игра) ---------
    if cmd == "/sisi":
        if was_today(chat, user, "last_sisi"):
            current = data[str(chat)][str(user.id)]["sisi"]
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твои вишенки сейчас {current} размера 😳🍒"
            )
        delta = max(weighted_random(),0)
        update_stat(chat, user, "sisi", delta)
        update_date(chat, user, "last_sisi")
        new_size = data[str(chat)][str(user.id)]["sisi"]
        bot.reply_to(
            message,
            f"{name}, твои сисечки выросли на +{delta}, "
            f"теперь твоя грудь {new_size} размера 😳🍒"
        )
        return

    # --------- /boosts (платный буст) ---------
    if cmd == "/boosts":
        parts = text.split()
        delta = 1
        if len(parts) >= 2:
            try:
                delta = max(int(parts[1]),1)
            except:
                delta = 1
        price = load_price()
        total = price * delta
        if price <= 0:
            update_stat(chat, user, "sisi", delta)
            update_date(chat, user, "last_sisi")
            new_size = data[str(chat)][str(user.id)]["sisi"]
            bot.reply_to(message, f"{name}, твои сисечки выросли на +{delta}, теперь {new_size} размера 😳🍒")
            return
        try:
            prices = [LabeledPrice(label="Boost Sisi", amount=total)]
            bot.send_invoice(
                chat_id=chat,
                title="Буст сисек",
                description=f"{name} хочет увеличить сиськи на +{delta}",
                invoice_payload=f"boost:{chat}:{user.id}:sisi:{delta}",
                provider_token="5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA",
                currency="XTR",
                prices=prices
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка оплаты: {e}")

# --------- успешная оплата для сисек ---------
def handle_successful_payment(bot, message):
    if not hasattr(message, "successful_payment") or not message.successful_payment:
        return
    payload = getattr(message.successful_payment, "invoice_payload", "") or \
              getattr(message.successful_payment, "payload", "")
    if not payload.startswith("boost:"):
        return
    try:
        _, chat_id_s, payer_id_s, stat, delta_s = payload.split(":")
        chat_id = int(chat_id_s)
        payer_id = int(payer_id_s)
        delta = int(delta_s)
    except:
        return
    from plugins.top_plugin import ensure_user, update_stat, update_date
    chat_data = ensure_user(chat_id, message.from_user)
    update_stat(chat_id, message.from_user, stat, delta)
    update_date(chat_id, message.from_user, f"last_{stat}")
    new_size = chat_data[str(chat_id)][str(payer_id)][stat]
    if stat == "sisi":
        bot.send_message(chat_id, f"{get_name(message.from_user)}, твои сисечки выросли на +{delta}, теперь {new_size} размера 😳🍒")