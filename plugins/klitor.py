from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

def _fmt(mm: int) -> str:
    return f"{mm / 10:.1f}"

def handle(bot, message):
    text = (message.text or "").strip()
    cmd = text.split()[0].lower().split("@")[0]

    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    top_plugin.ensure_user(chat, user)

    # =========================
    # 🍑 ЕЖЕДНЕВНЫЙ КЛИТОР
    # =========================
    if cmd in ("/klitor", "клитор"):
        if top_plugin.was_today(chat, user, "last_klitor"):
            data = top_plugin.load_users(chat)
            cur = data[str(user.id)]["klitor"]
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, думал не замечу? "
                f"Ты уже играл сегодня и твоя валына сейчас {_fmt(cur)}см 😳🍑"
            )

        delta = max(weighted_random(), 0)
        top_plugin.update_stat(chat, user, "klitor", delta)
        top_plugin.update_date(chat, user, "last_klitor")

        new_mm = top_plugin.load_users(chat)[str(user.id)]["klitor"]
        bot.reply_to(
            message,
            f"{name}, твой клитор вырос на +{delta}.0мм, теперь эта валына {_fmt(new_mm)}см 😳🍑"
        )

    # =========================
    # 💸 БУСТ КЛИТОРА
    # =========================
    if cmd in ("/boostk", "бустк"):
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
            top_plugin.update_stat(chat, user, "klitor", n)
            top_plugin.update_date(chat, user, "last_klitor")
            new_mm = top_plugin.load_users(chat)[str(user.id)]["klitor"]
            return bot.reply_to(
                message,
                f"{name}, твой клитор вырос на +{n}.0мм, теперь эта валына {_fmt(new_mm)}см 😳🍑"
            )

        prices = [LabeledPrice(label=f"Буст клитора +{n}мм", amount=total)]
        bot.send_invoice(
            chat_id=chat,
            title="🔥 Буст клитора",
            description=(
                f"{name} решил прокачать валыну 😈\n\n"
                f"➕ +{n}мм\n"
                f"💰 {total} ⭐️"
            ),
            invoice_payload=f"boost:{chat}:{user.id}:klitor:{n}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )

def handle_successful(bot, message):
    if not getattr(message, "successful_payment", None):
        return

    payload = message.successful_payment.invoice_payload
    if not payload.startswith("boost:"):
        return

    _, chat_s, _, stat, n_s = payload.split(":")
    if stat != "klitor":
        return

    chat_id = int(chat_s)
    n = int(n_s)
    user = message.from_user
    top_plugin.ensure_user(chat_id, user)
    top_plugin.update_stat(chat_id, user, "klitor", n)
    top_plugin.update_date(chat_id, user, "last_klitor")
    new_mm = top_plugin.load_users(chat_id)[str(user.id)]["klitor"]

    bot.send_message(
        chat_id,
        f"{get_name(user)}, твой клитор вырос на +{n}.0мм, теперь эта валына {_fmt(new_mm)}см 😳🍑"
    )