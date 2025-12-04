# plugins/hui.py
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

    # ----------------- /hui -----------------
    if cmd.startswith("/hui"):
        from plugins.top_plugin import was_today
        if was_today(chat_id, user, "last_hui"):
            current = data[str(chat_id)][str(user.id)]["hui"]
            bot.reply_to(
                message,
                f"{get_name(user)}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твой хуй сейчас {current} см 🍌"
            )
            return
        delta = weighted_random()
        delta = max(delta, 0)
        update_stat(chat_id, user, "hui", delta)
        update_date(chat_id, user, "last_hui")
        new_size = data[str(chat_id)][str(user.id)]["hui"] + delta
        bot.reply_to(
            message,
            f"{get_name(user)}, твой хуй вырос на +{delta}, "
            f"теперь твой член {new_size} см 🍌"
        )
        return

    # ----------------- /boosth -----------------
    if cmd.startswith("/boosth"):
        if len(text.split()) < 2:
            bot.reply_to(message, "⚠️ Укажи на сколько увеличить: /boosth 5")
            return
        try:
            delta = int(text.split()[1])
            if delta <= 0:
                raise ValueError()
        except:
            bot.reply_to(message, "❗ Используй положительное число: /boosth 5")
            return

        price = load_price()
        total = delta * price

        if price <= 0:
            update_stat(chat_id, user, "hui", delta)
            update_date(chat_id, user, "last_hui")
            new_size = data[str(chat_id)][str(user.id)]["hui"] + delta
            bot.reply_to(
                message,
                f"{get_name(user)}, твой хуй вырос на +{delta}, "
                f"теперь твой член {new_size} см 🍌"
            )
            return

        try:
            bot.send_invoice(
                chat_id=chat_id,
                title="Буст хуя",
                description=f"{get_name(user)} увеличивает хуй на {delta} см",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=[LabeledPrice("Boost", total)],
                invoice_payload=f"boost:{chat_id}:{user.id}:hui:{delta}"
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка оплаты: {e}")