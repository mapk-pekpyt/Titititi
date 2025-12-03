from telebot.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from plugins.common import get_name
import time

PRICE_STARS = 0  # ставишь свою цену
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"


def handle(bot, message):
    chat_id = message.chat.id
    user = message.from_user
    payer_name = get_name(user)

    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Укажи кого мутить: /mut @username или реплай")

    # Кто будет замучен
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        username = args[1].replace("@", "")
        target = bot.get_chat_member(chat_id, username).user if username else None

    if not target:
        return bot.reply_to(message, "Не могу найти пользователя.")

    target_name = get_name(target)

    duration = 60  # 1 минута (не меняем логику)

    # Бесплатный мут
    if PRICE_STARS == 0:
        bot.restrict_chat_member(chat_id, target.id, until_date=time.time() + duration)
        return bot.send_message(
            chat_id,
            f"🔇 {target_name}, ну ты и лошара… {payer_name} велел заткнуть тебя, видимо ты всех заебал🥲"
        )

    # Платный мут
    prices = [LabeledPrice(label="Мут", amount=PRICE_STARS)]

    bot.send_invoice(
        chat_id,
        title="Покупка мута",
        description=f"Мут для {target_name}",
        provider_token=PROVIDER_TOKEN,
        currency="XTR",  # обязательно для Stars
        prices=prices,
        start_parameter="mut_purchase",
        invoice_payload=f"{chat_id}:{target.id}:{payer_name}:{target_name}:{duration}"
    )


def handle_successful(bot, message):
    payload = message.successful_payment.invoice_payload
    chat_id, target_id, payer_name, target_name, duration = payload.split(":")

    chat_id = int(chat_id)
    target_id = int(target_id)
    duration = int(duration)

    # Выдаем мут
    bot.restrict_chat_member(chat_id, target_id, until_date=time.time() + duration)

    # Сообщение после оплаты
    bot.send_message(
        chat_id,
        f"🔇 {target_name}, ну ты и лошара🤣 {payer_name} велел заткнуть тебя, "
        f"видимо ты его так заебал, что он оплатил твоё молчание💰"
    )