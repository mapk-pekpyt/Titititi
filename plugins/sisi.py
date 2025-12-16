# plugins/sisi.py
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"


def handle(bot, message):
    text = (message.text or "").strip().lower()
    if not text:
        return

    parts = text.split()
    cmd = parts[0]
    args = parts[1:]

    chat = message.chat.id
    sender = message.from_user

    # цель буста — по умолчанию сам отправитель
    target_user = sender

    # если ответом — бустим того, кому ответили
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user

    sender_name = get_name(sender)
    target_name = get_name(target_user)

    # гарантируем наличие пользователей
    top_plugin.ensure_user(chat, sender)
    top_plugin.ensure_user(chat, target_user)

    # =====================================================
    # 🎮 СИСИ (ежедневно)
    # =====================================================
    if cmd in ("/sisi", "sisi", "сиси", "сиськи", "сисечки"):
        if top_plugin.was_today(chat, sender, "last_sisi"):
            data = top_plugin.load()
            current = data.get(str(chat), {}).get(str(sender.id), {}).get("sisi", 0)
            bot.reply_to(
                message,
                f"{sender_name}, ты уже сегодня играла 😳\n"
                f"Размер сейчас: {current} 🍒"
            )
            return

        delta = weighted_random()
        if delta < 0:
            delta = 0

        top_plugin.update_stat(chat, sender, "sisi", delta)
        top_plugin.update_date(chat, sender, "last_sisi")

        data = top_plugin.load()
        new_size = data[str(chat)][str(sender.id)]["sisi"]

        bot.reply_to(
            message,
            f"{sender_name}, твои сисечки выросли на +{delta} 😳🍒\n"
            f"Теперь размер: {new_size}"
        )
        return

    # =====================================================
    # 💸 БУСТ СИСЕК
    # =====================================================
    if cmd == "буст" and len(args) >= 1 and args[0] == "сиськи":
        n = 1
        if len(args) >= 2:
            try:
                n = max(int(args[1]), 1)
            except:
                n = 1

        price = load_price()
        total = price * n

        # бесплатный буст
        if price <= 0:
            top_plugin.update_stat(chat, target_user, "sisi", n)
            top_plugin.update_date(chat, target_user, "last_sisi")

            data = top_plugin.load()
            new_size = data[str(chat)][str(target_user.id)]["sisi"]

            bot.reply_to(
                message,
                f"🔥 {sender_name} увеличил сиськи {target_name}!\n"
                f"+{n} 🍒 → теперь {new_size}"
            )
            return

        # платный буст
        prices = [LabeledPrice(label="Boost Sisi", amount=total)]
        bot.send_invoice(
            chat_id=chat,
            title="Буст сисек",
            description=f"{sender_name} увеличивает сиськи {target_name} на +{n}",
            invoice_payload=f"boost:{chat}:{sender.id}:{target_user.id}:{n}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )


def handle_successful(bot, message):
    if not hasattr(message, "successful_payment"):
        return

    payload = (
        getattr(message.successful_payment, "invoice_payload", "")
        or getattr(message.successful_payment, "payload", "")
    )

    if not payload.startswith("boost:"):
        return

    parts = payload.split(":")
    if len(parts) != 5:
        return

    _, chat_s, payer_s, target_s, n_s = parts

    try:
        chat_id = int(chat_s)
        target_id = int(target_s)
        n = int(n_s)
    except:
        return

    payer = message.from_user

    # фейковый user-объект не нужен — берём из message
    target_user = payer
    if target_id != payer.id:
        target_user = message.reply_to_message.from_user if message.reply_to_message else payer

    top_plugin.ensure_user(chat_id, target_user)
    top_plugin.update_stat(chat_id, target_user, "sisi", n)
    top_plugin.update_date(chat_id, target_user, "last_sisi")

    data = top_plugin.load()
    new_size = data[str(chat_id)][str(target_user.id)]["sisi"]

    bot.send_message(
        chat_id,
        f"💸 Оплата прошла!\n"
        f"{get_name(target_user)} получил +{n} 🍒\n"
        f"Теперь размер: {new_size}"
    )