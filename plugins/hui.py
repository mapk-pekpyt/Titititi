# plugins/hui_db.py
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import db_top_plugin as top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

def handle(bot, message):
    text = (message.text or "").strip()
    cmd_raw = text.split()[0].lower() if text else ""
    cmd = cmd_raw.split("@")[0]

    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    top_plugin.ensure_user(chat, user)

    # =========================
    # 🍌 ЕЖЕДНЕВНЫЙ ХУЙ
    # =========================
    if cmd in ("/hui", "хуй"):
        if top_plugin.was_today(chat, user, "last_hui"):
            cursor_data = top_plugin.load_users(chat)
            current = cursor_data[str(user.id)]["hui"]
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл со своим дружком, твой болтик сейчас {current} см 😳 🍌"
            )

        delta = max(weighted_random(), 0)
        top_plugin.update_stat(chat, user, "hui", delta)
        top_plugin.update_date(chat, user, "last_hui")

        cursor_data = top_plugin.load_users(chat)
        new_size = cursor_data[str(user.id)]["hui"]

        bot.reply_to(
            message,
            f"{name}, твой хуй вырос на +{delta} см, "
            f"теперь твой болт {new_size} см 😳🍌"
        )

    # =========================
    # 💸 БУСТ ХУЯ
    # =========================
    if cmd in ("/boosth", "бустх"):
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
            new_size = top_plugin.load_users(chat)[str(user.id)]["hui"]
            return bot.reply_to(
                message,
                f"{name}, твой хуй вырос на +{n} см, теперь твой болт {new_size} см 😳🍌"
            )

        try:
            prices = [LabeledPrice(label=f"Буст хуя +{n} см", amount=total)]
            bot.send_invoice(
                chat_id=chat,
                title="🔥 Буст хуя",
                description=(
                    f"{name} решил подкачать достоинство 😈\n\n"
                    f"➕ +{n} см\n"
                    f"💰 Цена: {total} ⭐️\n\n"
                    f"Нажми кнопку ниже, чтобы подтвердить оплату 👇"
                ),
                invoice_payload=f"boost:{chat}:{user.id}:hui:{n}",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка оплаты: {e}")


def handle_successful(bot, message):
    if not getattr(message, "successful_payment", None):
        return

    payload = (
        message.successful_payment.invoice_payload
        if hasattr(message.successful_payment, "invoice_payload")
        else ""
    )
    if not payload.startswith("boost:"):
        return

    parts = payload.split(":")
    if len(parts) != 5:
        return

    _, chat_s, user_s, stat, n_s = parts
    if stat != "hui":
        return

    payer = message.from_user
    top_plugin.ensure_user(chat_s, payer)
    top_plugin.update_stat(chat_s, payer, "hui", int(n_s))
    top_plugin.update_date(chat_s, payer, "last_hui")
    new_size = top_plugin.load_users(chat_s)[str(payer.id)]["hui"]

    bot.send_message(
        chat_s,
        f"{get_name(payer)}, твой хуй вырос на +{n_s} см, теперь твой болт {new_size} см 😳🍌"
    )