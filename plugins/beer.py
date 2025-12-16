# plugins/beer.py
from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"


def handle(bot, message):
    text = (message.text or "").strip().lower()
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    top_plugin.ensure_user(chat, user)

    # =========================
    # 🍺 ВЫПИТЬ ПИВА
    # =========================
    if text == "выпить пива":
        if top_plugin.was_today(chat, user, "last_beer"):
            data = top_plugin.load()
            cur = data[str(chat)][str(user.id)].get("beer", 0)
            return bot.reply_to(
                message,
                f"{name}, алкаш ебаный, думал не замечу? "
                f"Ты уже выпил сегодня и всего ты всасал {cur} литров пива🍺"
            )

        delta = max(weighted_random(), 0)
        top_plugin.update_stat(chat, user, "beer", delta)
        top_plugin.update_date(chat, user, "last_beer")

        data = top_plugin.load()
        new_ml = data[str(chat)][str(user.id)]["beer"]

        bot.reply_to(
            message,
            f"{name}, ты выпил +{delta} Л. пива, "
            f"долбоеб, ты выжрал {new_ml} Литров пива 🍺"
        )
        return

    # =========================
    # 💸 ДОЛИТЬ ПИВА
    # =========================
    if text.startswith("долить пива"):
        # если ответ на сообщение — бустим того, кому ответили
        target_user = message.from_user
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user

        parts = text.split()
        n = 50  # стандартная порция мл
        if len(parts) >= 3:
            try:
                n = max(int(parts[2]), 1)
            except:
                n = 50

        price = load_price()
        total = price * n

        if price <= 0:
            top_plugin.update_stat(chat, target_user, "beer", n)
            top_plugin.update_date(chat, target_user, "last_beer")
            data = top_plugin.load()
            new_ml = data[str(chat)][str(target_user.id)]["beer"]
            return bot.reply_to(
                message,
                f"{get_name(target_user)}, тебе долили +{n} Литров пива 🍺 "
                f"теперь в тебе {new_ml} Литров"
            )

        prices = [LabeledPrice(label=f"Долить пива +{n} л", amount=total)]
        bot.send_invoice(
            chat_id=chat,
            title="🍺 Доливка пива",
            description=(
                f"{name} хочет долить {n} л пива {get_name(target_user)} 😈\n"
                f"💰 {total} ⭐️"
            ),
            invoice_payload=f"boost:{chat}:{target_user.id}:beer:{n}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )


def handle_successful(bot, message):
    if not getattr(message, "successful_payment", None):
        return

    # удаляем сообщение с кнопкой оплаты
    try:
        if message.reply_to_message:
            bot.delete_message(
                message.chat.id,
                message.reply_to_message.message_id
            )
    except:
        pass

    payload = message.successful_payment.invoice_payload
    if not payload.startswith("boost:"):
        return

    _, chat_s, target_s, stat, n_s = payload.split(":")
    if stat != "beer":
        return

    chat_id = int(chat_s)
    target_id = int(target_s)
    n = int(n_s)

    data = top_plugin.load()
    # находим target_user по id в чате
    # создаем пустого если нет
    if str(chat_id) not in data:
        data[str(chat_id)] = {}
    if str(target_id) not in data[str(chat_id)]:
        data[str(chat_id)][str(target_id)] = {"beer": 0}

    # обновляем
    top_plugin.update_stat(chat_id, type('User', (object,), {'id': target_id})(), "beer", n)
    top_plugin.update_date(chat_id, type('User', (object,), {'id': target_id})(), "last_beer")
    data = top_plugin.load()
    new_ml = data[str(chat_id)][str(target_id)]["beer"]

    bot.send_message(
        chat_id,
        f"{get_name(type('User', (object,), {'id': target_id})())}, тебе долили +{n} мл пива 🍺 "
        f"теперь кружка {new_ml} мл"
    )