# plugins/minus.py
import os
from telebot.types import LabeledPrice
from plugins import top_plugin
from plugins.common import get_name

PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

PRICE_PER_UNIT = 1  # 1 звезда = -1 единица

STAT_MAP = {
    "s": {
        "key": "sisi",
        "label": "Сиськи",
        "unit": "размера",
        "gender": "f",  # женский
    },
    "h": {
        "key": "hui",
        "label": "Хуй",
        "unit": "см",
        "gender": "m",  # мужской
    },
    "k": {
        "key": "klitor",
        "label": "Клитор",
        "unit": "мм",
        "gender": "m",  # мужской род
    },
}

def handle(bot, message):
    """
    /minus(s,h,k) X
    Пример: /minuss 3  → уменьшить сиськи на 3
    """
    text = (message.text or "").strip().lower()
    cmd_raw = text.split()[0]
    cmd = cmd_raw.split("@")[0]

    if not cmd.startswith("/minus"):
        return

    chat_id = message.chat.id
    user = message.from_user
    name = get_name(user)

    # тип уменьшения — последняя буква: s, h, k
    mode = cmd.replace("/minus", "")
    if mode not in STAT_MAP:
        bot.reply_to(message, "❌ Используй: /minuss, /minush, /minusk")
        return

    stat = STAT_MAP[mode]["key"]
    unit = STAT_MAP[mode]["unit"]
    gender = STAT_MAP[mode]["gender"]

    parts = text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Укажи число. Например: /minuss 3")
        return

    try:
        value = max(1, int(parts[1]))
    except:
        bot.reply_to(message, "❌ Неверное число")
        return

    total_price = value * PRICE_PER_UNIT

    top_plugin.ensure_user(chat_id, user)

    # отправляем инвойс
    try:
        prices = [LabeledPrice(label=f"Уменьшение {stat}", amount=total_price)]
        bot.send_invoice(
            chat_id=chat_id,
            title="Уменьшение размера",
            description=f"{name} хочет уменьшить {stat} на {value}",
            invoice_payload=f"minus:{chat_id}:{user.id}:{stat}:{value}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка оплаты: {e}")


def handle_successful(bot, message):
    """
    Платёж прошёл → выполняем уменьшение
    """
    if not hasattr(message, "successful_payment") or not message.successful_payment:
        return

    payload = message.successful_payment.invoice_payload

    if not payload.startswith("minus:"):
        return

    parts = payload.split(":")
    if len(parts) != 5:
        return

    _, chat_s, user_s, stat, amount_s = parts

    try:
        chat_id = int(chat_s)
        user_id = int(user_s)
        amount = int(amount_s)
    except:
        return

    # Пользователь
    payer = message.from_user
    top_plugin.ensure_user(chat_id, payer)

    # Загружаем текущее значение
    data = top_plugin.load()
    current = data.get(str(chat_id), {}).get(str(user_id), {}).get(stat, 0)

    new_value = max(0, current - amount)

    # сохраняем
    top_plugin.update_stat(chat_id, payer, stat, -amount)

    # для текста
    mapping = {
        "sisi": ("сиську", "она"),
        "hui": ("хуй", "он"),
        "klitor": ("клитор", "он"),
    }
    part_name, pron = mapping[stat]
    unit_map = {
        "sisi": "размера",
        "hui": "см",
        "klitor": "мм"
    }

    bot.send_message(
        chat_id,
        f"{get_name(payer)}, соболезную, но {get_name(payer)} откусил тебе {part_name}. "
        f"Теперь {pron} равен {new_value} {unit_map[stat]}."
    )