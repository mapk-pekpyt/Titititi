# plugins/minus.py
import os
from telebot.types import LabeledPrice
from plugins import top_plugin
from plugins.common import get_name
from plugins.bust_price import load_price  # если цена общая нужна (не обязательно)

# провайдер (тот же, что у тебя в других плагинах)
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"

# 1 звезда = 1 единица (sisi: размер, hui: см, klitor: мм)
PRICE_PER_UNIT = 1


STAT_MAP = {
    "s": {
        "key": "sisi",
        "label_obj": "сиську",
        "unit": "размера",
        "gender": "f",
        "display": "сиськи",
    },
    "h": {
        "key": "hui",
        "label_obj": "хуй",
        "unit": "см",
        "gender": "m",
        "display": "хуя",
    },
    "k": {
        "key": "klitor",
        "label_obj": "клитор",
        "unit": "мм",
        "gender": "m",
        "display": "клитора",
    },
}


def handle(bot, message):
    """
    Команды:
      /minuss N   - уменьшить (sisi) (ответ на сообщение => у того; иначе себе)
      /minush N   - уменьшить hui
      /minusk N   - уменьшить klitor (в мм)
    Поведение:
      - если команда ответом на чужое сообщение => уменьшение у того пользователя
      - иначе => уменьшение у автора команды (шутливое сообщение про "самообрез")
      - платная: выставляет invoice на stars (1 звезда = 1 единица)
    """
    text = (message.text or "").strip()
    if not text:
        return

    parts = text.split()
    cmd_raw = parts[0].lower()
    cmd = cmd_raw.split("@")[0]

    # определяем режим: /minus + буква или /minuss etc.
    if cmd.startswith("/minuss"):
        mode = "s"
    elif cmd.startswith("/minush"):
        mode = "h"
    elif cmd.startswith("/minusk"):
        mode = "k"
    else:
        return  # не наша команда

    info = STAT_MAP[mode]
    stat_key = info["key"]

    # количество единиц (N)
    if len(parts) >= 2:
        try:
            n = max(1, int(parts[1]))
        except:
            return bot.reply_to(message, "❗ Укажи целое число, например: /minush 3")
    else:
        n = 1

    # цель: если ответ на сообщение — уменьшаем target, иначе — себя
    if getattr(message, "reply_to_message", None) and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
        target_is_self = (target_user.id == message.from_user.id)
    else:
        target_user = message.from_user
        target_is_self = True

    chat_id = message.chat.id
    payer = message.from_user

    # Ensure target exists in DB
    top_plugin.ensure_user(chat_id, target_user)

    # счёт — берем цену на единицу (если есть общий модуль bust_price, можно взять оттуда)
    try:
        price_each = load_price()
    except Exception:
        price_each = PRICE_PER_UNIT
    total_price = price_each * n

    # Если цена <= 0 — делаем моментально (без оплаты)
    if price_each <= 0:
        # безопасное уменьшение (не делаем <0)
        data = top_plugin.load()
        chat_s = str(chat_id)
        uid_s = str(target_user.id)
        current = data.get(chat_s, {}).get(uid_s, {}).get(stat_key, 0)
        new_value = max(0, current - n)
        delta = new_value - current  # отрицательное или 0
        if delta != 0:
            top_plugin.update_stat(chat_id, target_user, stat_key, delta)
        # сообщение
        if target_is_self:
            # сам себе
            bot.reply_to(
                message,
                f"{get_name(target_user)}, аккуратнее играйся с ножом — ты случайно обрезал себе {info['label_obj']} на {n} {info['unit']}. Теперь {info['label_obj']} равен {new_value} {info['unit']}."
            )
        else:
            # уменьшили другого
            subj = get_name(message.from_user)
            targ = get_name(target_user)
            pron = "он" if info["gender"] == "m" else "она"
            bot.reply_to(
                message,
                f"{targ}, соболезную, но {subj} откусил тебе {info['label_obj']}. Теперь {pron} равен {new_value} {info['unit']}."
            )
        return

    # Иначе — платная операция: выставляем invoice (stars)
    try:
        prices = [LabeledPrice(label=f"Minus {info['display']}", amount=total_price)]
        # payload включит чат, payer, target, stat, amount
        payload = f"minus:{chat_id}:{payer.id}:{target_user.id}:{stat_key}:{n}"
        bot.send_invoice(
            chat_id=chat_id,
            title=f"Уменьшение {info['display']}",
            description=f"{get_name(payer)} хочет уменьшить {info['label_obj']} на {n} {info['unit']}",
            invoice_payload=payload,
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка оплаты: {e}")


def handle_successful(bot, message):
    """
    Обрабатывает successful_payment, парсит payload и применяет уменьшение к target.
    payload format: minus:chat:payer_id:target_id:stat_key:n
    """
    if not hasattr(message, "successful_payment") or not message.successful_payment:
        return

    # pyTelegramBotAPI may place payload in invoice_payload or payload
    payload = getattr(message.successful_payment, "invoice_payload", "") or getattr(message.successful_payment, "payload", "")
    if not payload.startswith("minus:"):
        return

    parts = payload.split(":")
    if len(parts) != 6:
        return

    _, chat_s, payer_s, target_s, stat_key, n_s = parts
    try:
        chat_id = int(chat_s)
        payer_id = int(payer_s)
        target_id = int(target_s)
        n = int(n_s)
    except:
        return

    # Load target user info via get_chat_member (best-effort) or create dummy object
    try:
        member = bot.get_chat_member(chat_id, target_id).user
    except Exception:
        # fallback: create minimal object for top_plugin.ensure_user
        class U:
            def __init__(self, id):
                self.id = id
                self.first_name = f"User{ id }"
                self.last_name = ""
                self.username = None
        member = U(target_id)

    # ensure user present
    top_plugin.ensure_user(chat_id, member)

    # get current and clamp
    data = top_plugin.load()
    chat_s = str(chat_id)
    uid_s = str(target_id)
    current = data.get(chat_s, {}).get(uid_s, {}).get(stat_key, 0)
    new_value = max(0, current - n)
    delta = new_value - current  # negative or zero

    if delta != 0:
        # apply update (update_stat adds delta)
        top_plugin.update_stat(chat_id, member, stat_key, delta)

    # Prepare message text
    # determine gender/pronoun
    gender = "m"
    for k, v in STAT_MAP.items():
        if v["key"] == stat_key:
            gender = v["gender"]
            label_obj = v["label_obj"]
            unit = v["unit"]
            break
    pron = "он" if gender == "m" else "она"

    # get names for display
    try:
        payer_user = bot.get_chat_member(chat_id, payer_id).user
    except:
        payer_user = message.from_user  # fallback

    payer_name = get_name(payer_user)
    target_name = get_name(member)

    if payer_id == target_id:
        # self-targeted (payer reduced self)
        bot.send_message(
            chat_id,
            f"{target_name}, аккуратнее играйся с ножом — ты случайно обрезал себе {label_obj} на {n} {unit}. Теперь {label_obj} равен {new_value} {unit}."
        )
    else:
        # someone reduced someone else
        bot.send_message(
            chat_id,
            f"{target_name}, соболезную, но {payer_name} откусил тебе {label_obj}. Теперь {pron} равен {new_value} {unit}."
        )