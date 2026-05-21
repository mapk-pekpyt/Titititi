import os
import json
import asyncio
from datetime import datetime, timedelta
from telebot.types import ChatPermissions, LabeledPrice

DATA_FILE = "data/ban_price.json"
DEFAULT_KICK_PRICE = 5
DEFAULT_BAN_PRICE = 10
DEFAULT_BAN_HOUR_PRICE = 3
PROVIDER_TOKEN = "5775769170:LIVE:TG_l0PjhdRBm3za7XB9t3IeFusA"
ADMIN_ID = 5791171535


# --------- Имена ---------
def get_name(user):
    fn = getattr(user, "first_name", None)
    ln = getattr(user, "last_name", None)
    if fn and ln:
        return f"{fn} {ln}"
    if fn:
        return fn
    return "Пользователь"


def get_name_by_id(bot, chat_id, user_id):
    try:
        m = bot.get_chat_member(chat_id, user_id).user
        return get_name(m)
    except:
        return "Пользователь"


# --------- ЦЕНЫ ---------
def ensure_data_dir():
    d = os.path.dirname(DATA_FILE)
    if d:
        os.makedirs(d, exist_ok=True)


def load_prices():
    ensure_data_dir()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "kick": data.get("kick", DEFAULT_KICK_PRICE),
                "ban": data.get("ban", DEFAULT_BAN_PRICE),
                "ban_hour": data.get("ban_hour", DEFAULT_BAN_HOUR_PRICE)
            }
    except:
        return {
            "kick": DEFAULT_KICK_PRICE,
            "ban": DEFAULT_BAN_PRICE,
            "ban_hour": DEFAULT_BAN_HOUR_PRICE
        }


def save_prices(prices):
    ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f)


# --------- БАН/КИК ---------
def ban_user(bot, chat_id, user_id, until_date=None):
    """Забанить пользователя"""
    bot.ban_chat_member(chat_id, user_id, until_date=until_date)


def unban_user(bot, chat_id, user_id):
    """Разбанить пользователя"""
    bot.unban_chat_member(chat_id, user_id, only_if_banned=True)


def kick_user(bot, chat_id, user_id):
    """Кикнуть пользователя"""
    bot.ban_chat_member(chat_id, user_id)
    bot.unban_chat_member(chat_id, user_id, only_if_banned=True)


async def auto_unban(bot, chat_id, user_id, seconds, target_name, admin_name):
    """Автоматический разбан через seconds секунд"""
    await asyncio.sleep(seconds)
    try:
        unban_user(bot, chat_id, user_id)
        bot.send_message(
            chat_id,
            f"🔓 {target_name}, господин {admin_name} решил тебя помиловать, целуй ему ноги пес"
        )
    except:
        pass


# --------- ОБРАБОТКА ПЛАТЕЖЕЙ ---------
def handle_successful(bot, message):
    payload = getattr(message.successful_payment, "invoice_payload", "") or \
              getattr(message.successful_payment, "payload", "")
    
    if not payload.startswith("ban:"):
        return
    
    parts = payload.split(":")
    action = parts[0]
    
    if action == "ban:kick":
        _, chat_id_s, payer_id_s, target_id_s = parts
        chat_id = int(chat_id_s)
        payer_id = int(payer_id_s)
        target_id = int(target_id_s)
        
        kick_user(bot, chat_id, target_id)
        target_name = get_name_by_id(bot, chat_id, target_id)
        bot.send_message(chat_id, f"👢 {target_name}, выйди и зайди нормально")
        
    elif action == "ban:permanent":
        _, chat_id_s, payer_id_s, target_id_s = parts
        chat_id = int(chat_id_s)
        payer_id = int(payer_id_s)
        target_id = int(target_id_s)
        
        ban_user(bot, chat_id, target_id)
        target_name = get_name_by_id(bot, chat_id, target_id)
        bot.send_message(chat_id, f"🚫 {target_name}, спердоляй с чату")
        
    elif action == "ban:temporary":
        _, chat_id_s, payer_id_s, target_id_s, hours_s = parts
        chat_id = int(chat_id_s)
        payer_id = int(payer_id_s)
        target_id = int(target_id_s)
        hours = int(hours_s)
        
        until_date = datetime.utcnow() + timedelta(hours=hours)
        ban_user(bot, chat_id, target_id, until_date=until_date)
        target_name = get_name_by_id(bot, chat_id, target_id)
        bot.send_message(chat_id, f"🚫 {target_name}, спердоляй с чату на {hours} часов")


# --------- ЗАЩИТА АДМИНА ---------
def check_and_save_admin(bot, chat_id):
    """Проверяет, не забанен ли админ, и разбанит если надо"""
    try:
        member = bot.get_chat_member(chat_id, ADMIN_ID)
        if member.status in ['left', 'kicked']:
            unban_user(bot, chat_id, ADMIN_ID)
            try:
                invite = bot.create_chat_invite_link(chat_id, member_limit=1)
                bot.send_message(ADMIN_ID, f"🛡️ Меня разбанили в чате {chat_id}\nСсылка для входа: {invite.invite_link}")
                bot.send_message(chat_id, "👑 Админ вернулся")
            except:
                pass
    except:
        pass


# --------- ОСНОВНАЯ ЛОГИКА ---------
def handle(bot, message):
    # Проверяем защиту админа при каждом сообщении
    check_and_save_admin(bot, message.chat.id)
    
    text = (message.text or "").strip()
    if not text:
        return
    
    # Разбираем команду (русские буквы, без /)
    cmd_parts = text.lower().split()
    cmd = cmd_parts[0]
    
    # Определяем, кто отправитель
    is_admin = (message.from_user.id == ADMIN_ID)
    prices = load_prices()
    
    # --------- КИК ---------
    if cmd == "кик":
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Ответь на сообщение того, кого хочешь кикнуть")
            return
        
        target_id = message.reply_to_message.from_user.id
        target_name = get_name(message.reply_to_message.from_user)
        
        # Нельзя кикнуть самого бота
        if target_id == bot.get_me().id:
            bot.reply_to(message, "❌ Нельзя кикнуть бота")
            return
        
        # Бесплатно для админа
        if is_admin:
            kick_user(bot, message.chat.id, target_id)
            bot.send_message(message.chat.id, f"👢 {target_name}, выйди и зайди нормально")
            return
        
        # Платно для остальных
        price = prices["kick"]
        if price <= 0:
            kick_user(bot, message.chat.id, target_id)
            bot.send_message(message.chat.id, f"👢 {target_name}, выйди и зайди нормально")
            return
        
        try:
            prices_list = [LabeledPrice(label="Кик", amount=price)]
            bot.send_invoice(
                chat_id=message.chat.id,
                title=f"Кик {target_name}",
                description=f"{get_name(message.from_user)} хочет кикнуть {target_name}",
                invoice_payload=f"ban:kick:{message.chat.id}:{message.from_user.id}:{target_id}",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices_list
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}")
        return
    
    # --------- БАН ---------
    if cmd == "бан":
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Ответь на сообщение того, кого хочешь забанить")
            return
        
        target_id = message.reply_to_message.from_user.id
        target_name = get_name(message.reply_to_message.from_user)
        
        # Нельзя забанить бота
        if target_id == bot.get_me().id:
            bot.reply_to(message, "❌ Нельзя забанить бота")
            return
        
        # Проверяем, есть ли время (бан X часов)
        hours = None
        if len(cmd_parts) > 1:
            try:
                hours = int(cmd_parts[1])
                if hours <= 0:
                    hours = None
            except:
                hours = None
        
        # Бесплатно для админа
        if is_admin:
            if hours:
                until_date = datetime.utcnow() + timedelta(hours=hours)
                ban_user(bot, message.chat.id, target_id, until_date=until_date)
                bot.send_message(message.chat.id, f"🚫 {target_name}, спердоляй с чату на {hours} часов")
                # Запускаем авторазбан через часы
                asyncio.create_task(auto_unban(bot, message.chat.id, target_id, hours*3600, target_name, get_name(message.from_user)))
            else:
                ban_user(bot, message.chat.id, target_id)
                bot.send_message(message.chat.id, f"🚫 {target_name}, спердоляй с чату")
            return
        
        # Платно для остальных
        if hours:
            price_per_hour = prices["ban_hour"]
            total_price = price_per_hour * hours
            
            if total_price <= 0:
                until_date = datetime.utcnow() + timedelta(hours=hours)
                ban_user(bot, message.chat.id, target_id, until_date=until_date)
                bot.send_message(message.chat.id, f"🚫 {target_name}, спердоляй с чату на {hours} часов")
                asyncio.create_task(auto_unban(bot, message.chat.id, target_id, hours*3600, target_name, get_name(message.from_user)))
                return
            
            try:
                prices_list = [LabeledPrice(label=f"Бан на {hours} ч", amount=total_price)]
                bot.send_invoice(
                    chat_id=message.chat.id,
                    title=f"Бан {target_name} на {hours} ч",
                    description=f"{get_name(message.from_user)} хочет забанить {target_name} на {hours} часов",
                    invoice_payload=f"ban:temporary:{message.chat.id}:{message.from_user.id}:{target_id}:{hours}",
                    provider_token=PROVIDER_TOKEN,
                    currency="XTR",
                    prices=prices_list
                )
            except Exception as e:
                bot.reply_to(message, f"❌ Ошибка: {e}")
        else:
            price = prices["ban"]
            if price <= 0:
                ban_user(bot, message.chat.id, target_id)
                bot.send_message(message.chat.id, f"🚫 {target_name}, спердоляй с чату")
                return
            
            try:
                prices_list = [LabeledPrice(label="Бан навсегда", amount=price)]
                bot.send_invoice(
                    chat_id=message.chat.id,
                    title=f"Бан {target_name}",
                    description=f"{get_name(message.from_user)} хочет забанить {target_name} навсегда",
                    invoice_payload=f"ban:permanent:{message.chat.id}:{message.from_user.id}:{target_id}",
                    provider_token=PROVIDER_TOKEN,
                    currency="XTR",
                    prices=prices_list
                )
            except Exception as e:
                bot.reply_to(message, f"❌ Ошибка: {e}")
        return
    
    # --------- РАЗБАН ---------
    if cmd == "разбан":
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Ответь на сообщение того, кого хочешь разбанить")
            return
        
        target_id = message.reply_to_message.from_user.id
        target_name = get_name(message.reply_to_message.from_user)
        
        # Бесплатно для админа
        if is_admin:
            unban_user(bot, message.chat.id, target_id)
            bot.send_message(
                message.chat.id,
                f"🔓 {target_name}, господин {get_name(message.from_user)} решил тебя помиловать, целуй ему ноги пес"
            )
            return
        
        # Платно 20 звезд
        try:
            prices_list = [LabeledPrice(label="Разбан", amount=20)]
            bot.send_invoice(
                chat_id=message.chat.id,
                title=f"Разбан {target_name}",
                description=f"{get_name(message.from_user)} хочет разбанить {target_name}",
                invoice_payload=f"unban:{message.chat.id}:{message.from_user.id}:{target_id}",
                provider_token=PROVIDER_TOKEN,
                currency="XTR",
                prices=prices_list
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}")
        return
    
    # --------- АДМИН-КОМАНДЫ ДЛЯ ЦЕН (только /) ---------
    if text.startswith("/kickprice") and message.from_user.id == ADMIN_ID:
        parts = text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❗ Используй: /kickprice 10")
            return
        try:
            new_price = int(parts[1])
            prices = load_prices()
            prices["kick"] = new_price
            save_prices(prices)
            bot.reply_to(message, f"✅ Цена кика: {new_price} ⭐")
        except:
            bot.reply_to(message, "❗ Ошибка")
        return
    
    if text.startswith("/banprice") and message.from_user.id == ADMIN_ID:
        parts = text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❗ Используй: /banprice 15")
            return
        try:
            new_price = int(parts[1])
            prices = load_prices()
            prices["ban"] = new_price
            save_prices(prices)
            bot.reply_to(message, f"✅ Цена вечного бана: {new_price} ⭐")
        except:
            bot.reply_to(message, "❗ Ошибка")
        return
    
    if text.startswith("/banpricer") and message.from_user.id == ADMIN_ID:
        parts = text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❗ Используй: /banpricer 3")
            return
        try:
            new_price = int(parts[1])
            prices = load_prices()
            prices["ban_hour"] = new_price
            save_prices(prices)
            bot.reply_to(message, f"✅ Цена за час бана: {new_price} ⭐")
        except:
            bot.reply_to(message, "❗ Ошибка")