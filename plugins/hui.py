import os
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

def handle(bot, message):
    text = (message.text or "").strip()
    cmd_raw = text.split()[0].lower() if text else ""
    cmd = cmd_raw.split("@")[0] if "@" in cmd_raw else cmd_raw

    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    # Получаем пользователя, на которого ответили (если есть)
    target_user = user
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user

    top_plugin.ensure_user(chat, target_user)

    # ---------- ежедневная игра ----------
    if cmd in ["/hui", "хуй", "дружок"]:
        if top_plugin.was_today(chat, user, "last_hui"):
            data = top_plugin.load()
            current = data.get(str(chat), {}).get(str(user.id), {}).get("hui", 0)
            return bot.reply_to(
                message,
                f"{name}, шалунишка ты мой, уже играл сегодня! Твой болтик {current} см 😳🍌"
            )

        delta = weighted_random()
        if delta < 0: delta = 0

        top_plugin.update_stat(chat, target_user, "hui", delta)
        top_plugin.update_date(chat, target_user, "last_hui")

        data = top_plugin.load()
        new_size = data[str(chat)][str(target_user.id)]["hui"]

        bot.reply_to(
            message,
            f"{get_name(target_user)}, твой хуй вырос на +{delta} см, теперь болт {new_size} см 😳🍌"
        )
        return

    # ---------- платный буст ----------
    if cmd in ["/boosth", "буст хуя", "буст хуй"]:
        parts = text.split()
        n = 1
        if len(parts) >= 2:
            try: n = max(int(parts[1]), 1)
            except: n = 1

        price = load_price()
        total = price * n

        if price <= 0:
            top_plugin.update_stat(chat, target_user, "hui", n)
            top_plugin.update_date(chat, target_user, "last_hui")
            data = top_plugin.load()
            new_size = data[str(chat)][str(target_user.id)]["hui"]
            return bot.reply_to(
                message,
                f"{get_name(target_user)}, твой хуй вырос на +{n} см, теперь болт {new_size} см 😳🍌"
            )

        try:
            prices = [LabeledPrice(label="Буст хуя", amount=total)]
            bot.send_invoice(
                chat_id=chat,
                title="Буст хуя",
                description=f"{name} хочет увеличить хуй на +{n} см для {get_name(target_user)}",
                invoice_payload=f"boost:{chat}:{target_user.id}:hui:{n}",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка оплаты: {e}")

def handle_successful(bot, message):
    if not hasattr(message, "successful_payment") or not message.successful_payment:
        return

    payload = getattr(message.successful_payment, "invoice_payload", "") or \
              getattr(message.successful_payment, "payload", "")

    if not payload.startswith("boost:"): return

    parts = payload.split(":")
    if len(parts) != 5: return
    _, chat_s, target_s, stat, n_s = parts
    if stat != "hui": return

    try:
        chat_id = int(chat_s)
        target_id = int(target_s)
        n = int(n_s)
    except: return

    target_user = type('User', (), {'id': target_id, 'first_name': 'Игрок'})()
    top_plugin.ensure_user(chat_id, target_user)

    top_plugin.update_stat(chat_id, target_user, "hui", n)
    top_plugin.update_date(chat_id, target_user, "last_hui")

    data = top_plugin.load()
    new_size = data[str(chat_id)][str(target_user.id)]["hui"]
    bot.send_message(chat_id, f"{get_name(target_user)}, твой хуй вырос на +{n} см, теперь болт {new_size} см 😳🍌")