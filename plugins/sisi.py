# plugins/sisi.py
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date
from .bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

def handle(bot, message):
    user = message.from_user
    chat_id = message.chat.id
    ensure_user(chat_id, user)
    data = ensure_user(chat_id, user)

    text = (message.text or "").strip().lower()
    cmd = text.split()[0]

    # ----------------- /sisi -----------------
    if cmd.startswith("/sisi"):
        if data[str(chat_id)][str(user.id)]["last_sisi"] == str(bot.get_me().username):
            pass
        if message.text.split()[0].lower() == "/sisi":
            # ежедневный рост
            from plugins.top_plugin import was_today
            if was_today(chat_id, user, "last_sisi"):
                current = data[str(chat_id)][str(user.id)]["sisi"]
                bot.reply_to(
                    message,
                    f"{get_name(user)}, шалунишка ты мой, думал не замечу? "
                    f"Ты уже играл сегодня и твои вишенки сейчас {current} размера 😳🍒"
                )
                return
            delta = weighted_random()
            delta = max(delta, 0)
            update_stat(chat_id, user, "sisi", delta)
            update_date(chat_id, user, "last_sisi")
            new_size = data[str(chat_id)][str(user.id)]["sisi"] + delta
            bot.reply_to(
                message,
                f"{get_name(user)}, твои сисечки выросли на +{delta}, "
                f"теперь твоя грудь {new_size} размера 😳🍒"
            )
        return

    # ----------------- /boosts -----------------
    if cmd.startswith("/boosts"):
        if len(text.split()) < 2:
            bot.reply_to(message, "⚠️ Укажи на сколько увеличить размер: /boosts 5")
            return
        try:
            delta = int(text.split()[1])
            if delta <= 0:
                raise ValueError()
        except:
            bot.reply_to(message, "❗ Используй положительное число: /boosts 5")
            return

        price = load_price()
        total = delta * price

        if price <= 0:
            update_stat(chat_id, user, "sisi", delta)
            update_date(chat_id, user, "last_sisi")
            new_size = data[str(chat_id)][str(user.id)]["sisi"] + delta
            bot.reply_to(
                message,
                f"{get_name(user)}, твои сисечки выросли на +{delta}, "
                f"теперь твоя грудь {new_size} размера 😳🍒"
            )
            return

        try:
            bot.send_invoice(
                chat_id=chat_id,
                title="Буст сисек",
                description=f"{get_name(user)} увеличивает сисечки на {delta} размера",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=[LabeledPrice("Boost", total)],
                invoice_payload=f"boost:{chat_id}:{user.id}:sisi:{delta}"
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка оплаты: {e}")