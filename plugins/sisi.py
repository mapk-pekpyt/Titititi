# plugins/sisi.py
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"


def handle(bot, message):
    text = (message.text or "").strip()
    cmd = text.split()[0].lower().split("@")[0]

    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    top_plugin.ensure_user(chat, user)

    # =========================
    # 🍒 ЕЖЕДНЕВНЫЕ СИСЬКИ
    # =========================
    if cmd in ("/sisi", "сиськи"):
        if top_plugin.was_today(chat, user, "last_sisi"):
            data = top_plugin.load()
            cur = data[str(chat)][str(user.id)]["sisi"]
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твои вишенки сейчас {cur} размера 😳🍒"
            )

        delta = max(weighted_random(), 0)
        top_plugin.update_stat(chat, user, "sisi", delta)
        top_plugin.update_date(chat, user, "last_sisi")

        data = top_plugin.load()
        new_size = data[str(chat)][str(user.id)]["sisi"]

        bot.reply_to(
            message,
            f"{name}, твои сисечки выросли на +{delta}, "
            f"теперь твоя грудь {new_size} размера 😳🍒"
        )
        return

    # =========================
    # 💸 БУСТ СИСЕК
    # =========================
    if cmd in ("/boosts", "бусты"):
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
            top_plugin.update_stat(chat, user, "sisi", n)
            top_plugin.update_date(chat, user, "last_sisi")
            data = top_plugin.load()
            new_size = data[str(chat)][str(user.id)]["sisi"]

            return bot.reply_to(
                message,
                f"{name}, твои сисечки выросли на +{n}, "
                f"теперь твоя грудь {new_size} размера 😳🍒"
            )

        prices = [LabeledPrice(label=f"Буст сисек +{n}", amount=total)]
        bot.send_invoice(
            chat_id=chat,
            title="🔥 Буст сисек",
            description=(
                f"{name} хочет грудь побольше 😈\n\n"
                f"➕ +{n} размера\n"
                f"💰 {total} ⭐️"
            ),
            invoice_payload=f"boost:{chat}:{user.id}:sisi:{n}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )


def handle_successful(bot, message):
    if not getattr(message, "successful_payment", None):
        return

    # 🔥 УДАЛЯЕМ INVOICE
    try:
        if message.reply_to_message:
            bot.delete_message(
                message.chat.id,
                message.reply_to_message.message_id
            )
    except:
        pass

    payload = message.successful_payment.invoice_payload
    if not payload.startswith("boost:"):
        return

    _, chat_s, _, stat, n_s = payload.split(":")
    if stat != "sisi":
        return

    chat_id = int(chat_s)
    n = int(n_s)
    user = message.from_user

    top_plugin.ensure_user(chat_id, user)
    top_plugin.update_stat(chat_id, user, "sisi", n)
    top_plugin.update_date(chat_id, user, "last_sisi")

    data = top_plugin.load()
    new_size = data[str(chat_id)][str(user.id)]["sisi"]

    bot.send_message(
        chat_id,
        f"{get_name(user)}, твои сисечки выросли на +{n}, "
        f"теперь твоя грудь {new_size} размера 😳🍒"
    )