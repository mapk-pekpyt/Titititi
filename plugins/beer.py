from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"
DOMBAS_ID = 1076426555  # Пивной Домбасёнок

def handle(bot, message):
    text = (message.text or "").lower().strip()
    chat = message.chat.id
    user = message.from_user
    name = get_name(user)

    top_plugin.ensure_user(chat, user)

    # -------- ВЫПИТЬ --------
    if text == "выпить пива":
        if top_plugin.was_today(chat, user, "last_beer"):
            cur = top_plugin.load_users(chat)[str(user.id)]["beer"]
            return bot.reply_to(
                message,
                f"{name}, ты уже бухал 🍺\nВсего: {cur} л"
            )

        delta = max(weighted_random(), 0)
        top_plugin.update_stat(chat, user, "beer", delta)
        top_plugin.update_date(chat, user, "last_beer")

        new = top_plugin.load_users(chat)[str(user.id)]["beer"]
        return bot.reply_to(
            message,
            f"{name} всосал {delta} л пива 🍺\n"
            f"Всего: {new} л"
        )

    # -------- ДОЛИТЬ --------
    if text.startswith("долить пива"):
        target = message.reply_to_message.from_user if message.reply_to_message else user

        # 🍺 ПИВНОЙ ДОМБАСЁНОК
        if user.id == DOMBAS_ID:
            n = max(weighted_random(), 1)
            top_plugin.update_stat(chat, target, "beer", n)
            return bot.reply_to(
                message,
                f"🍺 ПИВНОЙ ДОМБАСЁНОК РАЗЛИВАЕТ!\n\n"
                f"{get_name(target)} получил +{n} л халявы 💪\n"
                f"Разлито с душой и матом 😈"
            )

        parts = text.split()
        n = int(parts[2]) if len(parts) >= 3 else 50

        price = load_price()
        total = price * n

        if price <= 0:
            top_plugin.update_stat(chat, target, "beer", n)
            top_plugin.update_date(chat, target, "last_beer")
            new = top_plugin.load_users(chat)[str(target.id)]["beer"]
            return bot.reply_to(
                message,
                f"{get_name(target)}, тебе долили +{n} л 🍺\nТеперь: {new} л"
            )

        prices = [LabeledPrice(label=f"Долить пива +{n} л", amount=total)]
        bot.send_invoice(
            chat_id=chat,
            title="🍺 Доливка пива",
            description=f"{name} хочет долить {n} л пива {get_name(target)} 😈",
            invoice_payload=f"boost:{chat}:{target.id}:beer:{n}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )