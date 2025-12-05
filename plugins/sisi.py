# plugins/sisi.py
import os
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"  # если нужно — вынесу в env

def handle(bot, message):
    """
    Обработчик команды /sisi и /boosts
    """
    text = (message.text or "").strip()
    cmd_raw = text.split()[0].lower() if text else ""
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw

    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    # ensure user exists in top DB
    top_plugin.ensure_user(chat, user)

    # ---------- ежедневная игра /sisi ----------
    if cmd == "/sisi":
        if top_plugin.was_today(chat, user, "last_sisi"):
            data = top_plugin.load()
            current = data.get(str(chat), {}).get(str(user.id), {}).get("sisi", 0)
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твои вишенки сейчас {current} размера 😳🍒"
            )

        # delta — неотрицательное
        delta = weighted_random()
        if delta < 0:
            delta = 0

        top_plugin.update_stat(chat, user, "sisi", delta)
        top_plugin.update_date(chat, user, "last_sisi")

        data = top_plugin.load()
        new_size = data[str(chat)][str(user.id)]["sisi"]

        bot.reply_to(
            message,
            f"{name}, твои сисечки выросли на +{delta}, теперь твоя грудь {new_size} размера 😳🍒"
        )
        return

    # ---------- платный буст /boosts [n] ----------
    if cmd == "/boosts":
        parts = text.split()
        n = 1
        if len(parts) >= 2:
            try:
                n = max(int(parts[1]), 1)
            except:
                n = 1

        price = load_price()
        total = price * n

        # если цена 0 — даём сразу
        if price <= 0:
            top_plugin.update_stat(chat, user, "sisi", n)
            top_plugin.update_date(chat, user, "last_sisi")
            data = top_plugin.load()
            new_size = data[str(chat)][str(user.id)]["sisi"]
            return bot.reply_to(
                message,
                f"{name}, твои сисечки выросли на +{n}, теперь твоя грудь {new_size} размера 😳🍒"
            )

        try:
            prices = [LabeledPrice(label="Boost Sisi", amount=total)]
            bot.send_invoice(
                chat_id=chat,
                title="Буст сисек",
                description=f"{name} хочет увеличить сиськи на +{n}",
                invoice_payload=f"boost:{chat}:{user.id}:sisi:{n}",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка оплаты: {e}")

def handle_successful(bot, message):
    """
    Вызывается при successful_payment (main должен направлять сюда сообщение)
    распознаёт payload и применяет буст для s i s i
    """
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
    if stat != "sisi":
        return

    try:
        chat_id = int(chat_s)
        payer_id = int(payer_s)
        n = int(n_s)
    except:
        return

    # payer is message.from_user
    payer = message.from_user
    # ensure user exists
    top_plugin.ensure_user(chat_id, payer)

    # apply and save
    top_plugin.update_stat(chat_id, payer, "sisi", n)
    top_plugin.update_date(chat_id, payer, "last_sisi")

    data = top_plugin.load()
    new_size = data[str(chat_id)][str(payer.id)]["sisi"]

    # final message
    bot.send_message(chat_id, f"{get_name(payer)}, твои сисечки выросли на +{n}, теперь твоя грудь {new_size} размера 😳🍒")