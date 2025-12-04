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

    # --------- /hui (ежедневная игра) ---------
    if cmd == "/hui":
        if was_today(chat, user, "last_hui"):
            current = data[str(chat)][str(user.id)]["hui"]
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твой хуй сейчас {current} см 🍌"
            )
        delta = max(weighted_random(),0)
        update_stat(chat, user, "hui", delta)
        update_date(chat, user, "last_hui")
        new_size = data[str(chat)][str(user.id)]["hui"]
        bot.reply_to(
            message,
            f"{name}, твой хуй вырос на +{delta}, теперь {new_size} см 🍌"
        )
        return

    # --------- /boosth (платный буст) ---------
    if cmd == "/boosth":
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
            update_stat(chat, user, "hui", delta)
            update_date(chat, user, "last_hui")
            new_size = data[str(chat)][str(user.id)]["hui"]
            bot.reply_to(message, f"{name}, твой хуй вырос на +{delta}, теперь {new_size} см 🍌")
            return
        try:
            prices = [LabeledPrice(label="Boost Hui", amount=total)]
            bot.send_invoice(
                chat_id=chat,
                title="Буст хуя",
                description=f"{name} хочет увеличить хуй на +{delta} см",
                invoice_payload=f"boost:{chat}:{user.id}:hui:{delta}",
                provider_token="5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA",
                currency="XTR",
                prices=prices
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка оплаты: {e}")

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
    if stat == "hui":
        bot.send_message(chat_id, f"{get_name(message.from_user)}, твой хуй вырос на +{delta}, теперь {new_size} см 🍌")