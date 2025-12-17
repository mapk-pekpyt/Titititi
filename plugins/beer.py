from telebot.types import LabeledPrice
from plugins.common import weighted_random, get_name
from plugins import top_plugin
from plugins.bust_price import load_price

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"
DOMBAS_ID = 1076426555  # 🍺 Пивной Домбасёнок


def handle(bot, message):
    text = (message.text or "").strip().lower()
    user = message.from_user
    chat = message.chat.id
    name = get_name(user)

    # гарантируем пользователя
    top_plugin.ensure_user(chat, user)

    # =========================
    # 🍺 ВЫПИТЬ ПИВА
    # =========================
    if text == "выпить пива":
        if top_plugin.was_today(chat, user, "last_beer"):
            users = top_plugin.load_users(chat)
            cur = users[str(user.id)].get("beer", 0)
            return bot.reply_to(
                message,
                f"{name}, алкаш ебаный, думал не замечу? "
                f"Ты уже выпил сегодня и всего ты всасал {cur} литров пива🍺"
            )

        delta = max(weighted_random(), 0)

        top_plugin.update_stat(chat, user, "beer", delta)
        top_plugin.update_date(chat, user, "last_beer")

        users = top_plugin.load_users(chat)
        new_ml = users[str(user.id)]["beer"]

        bot.reply_to(
            message,
            f"{name}, ты всосал еще {delta} Л. пива! "
            f"Всего, ты долбоебина такая, выжрал {new_ml} Литров пива, гордись собой🍺"
        )
        return

    # =========================
    # 💸 ДОЛИТЬ ПИВА
    # =========================
    if text.startswith("долить пива"):
        # если ответ — льём тому, кому ответили
        target_user = user
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user

        # сколько лить
        parts = text.split()
        n = 50
        if len(parts) >= 3:
            try:
                n = max(int(parts[2]), 1)
            except:
                n = 50

        # =========================
        # 🍺 ПИВНОЙ ДОМБАСЁНОК (ХАЛЯВА)
        # =========================
        if user.id == DOMBAS_ID:
            top_plugin.ensure_user(chat, target_user)
            top_plugin.update_stat(chat, target_user, "beer", n)
            top_plugin.update_date(chat, target_user, "last_beer")

            users = top_plugin.load_users(chat)
            new_ml = users[str(target_user.id)]["beer"]

            return bot.reply_to(
                message,
                f"🍺 **ПИВНОЙ ДОМБАСЁНОК В ДЕЛЕ**\n\n"
                f"{get_name(target_user)}, тебе БЕСПЛАТНО долили +{n} Л 🍻\n"
                f"Теперь в тебе {new_ml} Л пива\n\n"
                f"_Разлив произведён с матом, любовью и презрением к трезвости_ 😈"
            )

        # =========================
        # 💰 ОБЫЧНАЯ ЛОГИКА (ОПЛАТА)
        # =========================
        price = load_price()
        total = price * n

        # бесплатно (если цена 0)
        if price <= 0:
            top_plugin.update_stat(chat, target_user, "beer", n)
            top_plugin.update_date(chat, target_user, "last_beer")

            users = top_plugin.load_users(chat)
            new_ml = users[str(target_user.id)]["beer"]

            return bot.reply_to(
                message,
                f"{get_name(target_user)}, тебе долили +{n} Литров пива 🍺 "
                f"теперь в тебе {new_ml} Литров"
            )

        # платно
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


# =========================
# ✅ УСПЕШНАЯ ОПЛАТА
# =========================
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

    # фейковый user-объект для update_stat
    TargetUser = type("User", (), {"id": target_id})

    top_plugin.ensure_user(chat_id, TargetUser())
    top_plugin.update_stat(chat_id, TargetUser(), "beer", n)
    top_plugin.update_date(chat_id, TargetUser(), "last_beer")

    users = top_plugin.load_users(chat_id)
    new_ml = users[str(target_id)]["beer"]

    bot.send_message(
        chat_id,
        f"{get_name(TargetUser())}, тебе долили +{n} мл пива 🍺 "
        f"теперь кружка {new_ml} мл"
    )