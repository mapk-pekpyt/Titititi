# plugins/sisi.py
import os
from telebot.types import LabeledPrice
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from plugins.common import weighted_random, get_name
from plugins.bust_price import get_price
import os

PROVIDER_TOKEN = os.environ.get("PROVIDER_TOKEN", "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA")

def handle(bot, message):
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    # гарантируем запись в базе top_plugin
    ensure_user(chat, user)

    text = (message.text or "").strip()
    cmd = text.split()[0].lower()

    # ---- ежедневная игра /sisi ----
    if cmd == "/sisi":
        if was_today(chat, user, "last_sisi"):
            data = ensure_user(chat, user)
            current = data[str(chat)][str(user.id)]["sisi"]
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? Ты уже играл сегодня и твои вишенки сейчас {current} размера 😳🍒"
            )
        delta = weighted_random()
        # обновляем статистику через top_plugin
        update_stat(chat, user, "sisi", delta)
        update_date(chat, user, "last_sisi")
        data = ensure_user(chat, user)
        new_size = data[str(chat)][str(user.id)]["sisi"]
        return bot.reply_to(
            message,
            f"{name}, твои сисечки выросли на {delta:+d}, теперь твоя грудь {new_size} размера 😳🍒"
        )

    # ---- платный boost /boosts <amount> ----
    if cmd == "/boosts":
        parts = text.split()
        if len(parts) < 2:
            return bot.reply_to(message, "Использование: /boosts <положительное число>")
        try:
            boost = int(parts[1])
            if boost <= 0:
                raise ValueError
        except:
            return bot.reply_to(message, "Укажи корректное положительное целое число.")
        price_per_unit = get_price()  # цена из plugins/bust_price.py
        total_price = max(1, int(price_per_unit * boost))  # минимум 1
        prices = [LabeledPrice(label=f"Boost x{boost}", amount=total_price)]
        payload = f"boost_sisi:{chat}:{user.id}:{boost}"
        # отправляем настоящий инвойс Telegram (Stars)
        try:
            bot.send_invoice(
                message.chat.id,
                title=f"Boost груди +{boost}",
                description=f"Увеличение груди на {boost} размера(ов)",
                invoice_payload=payload,
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices,
                start_parameter="boost_sisi"
            )
        except Exception as e:
            return bot.reply_to(message, f"❌ Ошибка создания счёта: {e}")