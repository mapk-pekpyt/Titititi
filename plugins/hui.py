# plugins/hui.py
import os
from telebot.types import LabeledPrice
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from plugins.common import weighted_random, get_name
from plugins.bust_price import get_price

PROVIDER_TOKEN = os.environ.get("PROVIDER_TOKEN", "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA")

def handle(bot, message):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    ensure_user(chat, user)

    text = (message.text or "").strip()
    cmd = text.split()[0].lower()

    # ---- ежедневная игра /hui ----
    if cmd == "/hui":
        if was_today(chat, user, "last_hui"):
            data = ensure_user(chat, user)
            current = data[str(chat)][str(user.id)]["hui"]
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? Ты уже играл сегодня и твой хуй сейчас {current} см 😳🍌"
            )
        delta = weighted_random()
        update_stat(chat, user, "hui", delta)
        update_date(chat, user, "last_hui")
        data = ensure_user(chat, user)
        new_size = data[str(chat)][str(user.id)]["hui"]
        return bot.reply_to(
            message,
            f"{name}, твой хуй вырос на {delta:+d} см, теперь он {new_size} см 😳🍌"
        )

    # ---- платный boost /boosth <amount> ----
    if cmd == "/boosth":
        parts = text.split()
        if len(parts) < 2:
            return bot.reply_to(message, "Использование: /boosth <положительное число>")
        try:
            boost = int(parts[1])
            if boost <= 0:
                raise ValueError
        except:
            return bot.reply_to(message, "Укажи корректное положительное целое число.")
        price_per_unit = get_price()
        total_price = max(1, int(price_per_unit * boost))
        prices = [LabeledPrice(label=f"Boost x{boost}", amount=total_price)]
        payload = f"boost_hui:{chat}:{user.id}:{boost}"
        try:
            bot.send_invoice(
                message.chat.id,
                title=f"Boost хуя +{boost} см",
                description=f"Увеличение члена на {boost} см",
                invoice_payload=payload,
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices,
                start_parameter="boost_hui"
            )
        except Exception as e:
            return bot.reply_to(message, f"❌ Ошибка создания счёта: {e}")