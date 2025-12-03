# plugins/mut.py
import os
import json
from datetime import datetime, timedelta
from telebot.types import ChatPermissions, LabeledPrice

# --- Настройки ---
DATA_FILE = "data/price.json"
DEFAULT_PRICE = 2                       # ⭐ за минуту, если файла нет
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"
ADMIN_ID = 5791171535                   # твой id — только он может менять /price

# --- Файловые утилиты ---
def ensure_data_dir():
    d = os.path.dirname(DATA_FILE)
    if d:
        os.makedirs(d, exist_ok=True)

def load_price():
    ensure_data_dir()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return int(data.get("price", DEFAULT_PRICE))
    except Exception:
        return DEFAULT_PRICE

def save_price(p: int):
    ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"price": int(p)}, f)

# --- Имя пользователя (красиво) ---
def get_name(user):
    if getattr(user, "username", None):
        return f"@{user.username}"
    if getattr(user, "first_name", None) and getattr(user, "last_name", None):
        return f"{user.first_name} {user.last_name}"
    if getattr(user, "first_name", None):
        return user.first_name
    return "Пользователь"

def get_name_by_id(bot, chat_id, user_id):
    try:
        m = bot.get_chat_member(chat_id, user_id).user
        return get_name(m)
    except:
        return "Пользователь"

# --- Выдача мута ---
def apply_mute(bot, chat_id, target_id, minutes, payer_name, target_name=None):
    until_ts = int((datetime.utcnow() + timedelta(minutes=minutes)).timestamp())
    try:
        perms = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        bot.restrict_chat_member(chat_id, target_id, permissions=perms, until_date=until_ts)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Не удалось выдать мут: {e}")
        return

    if not target_name:
        target_name = get_name_by_id(bot, chat_id, target_id)

    bot.send_message(
        chat_id,
        f"🔇 {target_name}, ну ты и лошара… {payer_name} велел заткнуть тебя, видимо ты всех заебал🥲",
        parse_mode="HTML"
    )

# --- Обработка успешной оплаты (вызывается из main.py) ---
def handle_successful(bot, message):
    # поддерживаем оба поля: invoice_payload (новые) и payload (на всякий)
    payload = getattr(message.successful_payment, "invoice_payload", None) or getattr(message.successful_payment, "payload", "")
    if not payload or not payload.startswith("mut:"):
        return

    try:
        _, chat_id_s, payer_id_s, target_id_s, minutes_s = payload.split(":")
        chat_id = int(chat_id_s); payer_id = int(payer_id_s)
        target_id = int(target_id_s); minutes = int(minutes_s)
    except Exception:
        bot.send_message(message.chat.id, "❌ Ошибка разбора payload после оплаты.")
        return

    payer_name = get_name_by_id(bot, chat_id, payer_id)
    target_name = get_name_by_id(bot, chat_id, target_id)

    # выдаём мут и красивое сообщение
    apply_mute(bot, chat_id, target_id, minutes, payer_name, target_name)
    # более "праздничное" сообщение (отличается для платного мута)
    try:
        bot.send_message(
            chat_id,
            f"🔇 {target_name}, ну ты и лошара🤣 {payer_name} велел заткнуть тебя, видимо ты его так заебал что он оплатил твое молчание💰",
            parse_mode="HTML"
        )
    except:
        pass

# --- Основной обработчик команды /mut и /price ---
def handle(bot, message):
    text = (message.text or "").strip()
    if not text:
        return

    # Поддерживаем варианты: /price, /price@BotName
    first_token = text.split()[0].lower()
    if "@" in first_token:
        cmd = first_token.split("@")[0]
    else:
        cmd = first_token

    # --- /price (только админ может менять) ---
    if cmd == "/price":
        parts = text.split()
        # показать текущую цену, если нет аргумента
        if len(parts) == 1:
            current = load_price()
            bot.reply_to(message, f"💰 Текущая цена: {current} ⭐ за 1 минуту.")
            return

        # попытка изменить цену
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "⛔ Только админ может менять цену.")
            return

        try:
            newp = int(parts[1])
            save_price(newp)
            bot.reply_to(message, f"✅ Цена за 1 минуту установлена: {newp} ⭐")
        except Exception:
            bot.reply_to(message, "❗ Укажи целое число: /price 3")
        return

    # --- /mut (поддерживаем /mut, /mut@BotName) ---
    if cmd != "/mut":
        return

    # Нужен reply на сообщение того, кого мутят
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Чтобы выдать мут, ответь на сообщение пользователя и введи /mut <минуты>")
        return

    parts = text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❗ Укажи минуты: /mut 5")
        return

    try:
        minutes = int(parts[1])
        if minutes <= 0:
            raise ValueError()
    except:
        bot.reply_to(message, "❗ Минуты должны быть целым числом > 0")
        return

    payer = message.from_user
    target = message.reply_to_message.from_user
    payer_name = get_name(payer)
    target_name = get_name(target)

    price_per_min = load_price()
    total_stars = price_per_min * minutes

    # бесплатный мут (цена 0 или отрицательная)
    if price_per_min <= 0 or total_stars <= 0:
        apply_mute(bot, message.chat.id, target.id, minutes, payer_name, target_name)
        return

    # платный мут — создаём инвойс (pyTelegramBotAPI 4.23+)
    try:
        prices = [LabeledPrice(label="Mute", amount=total_stars)]
        bot.send_invoice(
            chat_id=message.chat.id,
            title=f"Мут для {target_name}",
            description=f"{payer_name} хочет замутить {target_name} на {minutes} минут. Стоимость: {total_stars} ⭐",
            invoice_payload=f"mut:{message.chat.id}:{payer.id}:{target.id}:{minutes}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка выставления счёта: {e}")