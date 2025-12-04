# plugins/klitor.py
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

    # ---- ежедневная игра /klitor ----
    if cmd == "/klitor":
        if was_today(chat, user, "last_klitor"):
            data = ensure_user(chat, user)
            current = data[str(chat)][str(user.id)]["klitor"]
            # top_plugin stores mm, _format_klitor divides by 10 to get cm; but here show mm
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? Ты уже играл сегодня и твой клитор сейчас нехуйная валына, целых {current} мм 😳🍑"
            )
        delta = weighted_random()       # delta in integer mm
        update_stat(chat, user, "klitor", delta)
        update_date(chat, user, "last_klitor")
        data = ensure_user(chat, user)
        new_size = data[str(chat)][str(user.id)]["klitor"]
        return bot.reply_to(
            message,
            f"{name}, твой клитор вырос на {delta:+d} мм, теперь он {new_size} мм 😳🍑"
        )

    # ---- платный boost /boostk <amount_mm> ----
    if cmd == "/boostk":
        parts = text.split()
        if len(parts) < 2:
            return bot.reply_to(message, "Использование: /boostk <положительное число (мм)>")
        try:
            boost = int(parts[1])
            if boost <= 0:
                raise ValueError
        except:
            return bot.reply_to(message, "Укажи корректное положительное целое число (мм).")
        price_per_unit = get_price()
        total_price = max(1, int(price_per_unit * boost))
        prices = [LabeledPrice(label=f"Boost x{boost} мм", amount=total_price)]
        payload = f"boost_klitor:{chat}:{user.id}:{boost}"
        try:
            bot.send_invoice(
                message.chat.id,
                title=f"Boost клитора +{boost} мм",
                description=f"Увеличение клитора на {boost} мм",
                invoice_payload=payload,
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices,
                start_parameter="boost_klitor"
            )
        except Exception as e:
            return bot.reply_to(message, f"❌ Ошибка создания счёта: {e}")