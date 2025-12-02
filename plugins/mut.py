# plugins/mut.py
import datetime
from telebot.types import ChatPermissions
from main import bot
from core import db_execute, get_bot_balance, set_bot_balance, get_price, set_price

ADMIN_USERNAME = "Sugar_Daddy_rip"

# Ensure table active_mutes exists (core.init_db already created, but safe)
db_execute("""CREATE TABLE IF NOT EXISTS active_mutes (
    chat_id TEXT,
    user_identifier TEXT,
    end_time TEXT,
    PRIMARY KEY(chat_id, user_identifier)
)""")

@bot.message_handler(commands=['price'])
def cmd_price(message):
    # allow only admin (by username) to change price; works in LS or group
    username = getattr(message.from_user, "username", None)
    if username != ADMIN_USERNAME:
        return  # silently ignore non-admins
    parts = message.text.split()
    if len(parts) < 2:
        price = get_price()
        bot.reply_to(message, f"Текущая цена за 1 минуту: {price} ⭐")
        return
    try:
        newp = int(parts[1])
    except:
        bot.reply_to(message, "Используй: /price <целое число>")
        return
    set_price(newp)
    bot.reply_to(message, f"✅ Цена за 1 минуту мьюта установлена: {newp} ⭐")

def unmute_expired():
    now = datetime.datetime.utcnow()
    rows = db_execute("SELECT chat_id, user_identifier, end_time FROM active_mutes", fetch=True)
    for r in rows:
        try:
            end = datetime.datetime.fromisoformat(r['end_time'])
        except:
            continue
        if now >= end:
            # try remove restriction if we have numeric id
            uid = r['user_identifier']
            try:
                uid_int = int(uid)
            except:
                uid_int = None
            if uid_int:
                try:
                    perms = ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                            can_send_other_messages=True, can_add_web_page_previews=True)
                    bot.restrict_chat_member(int(r['chat_id']), uid_int, permissions=perms)
                except Exception:
                    pass
            db_execute("DELETE FROM active_mutes WHERE chat_id=? AND user_identifier=?", (r['chat_id'], r['user_identifier']))

@bot.message_handler(commands=['mut'])
def cmd_mut(message):
    chat_id = str(message.chat.id)
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "Используй: /mut <минуты> <@username или user_id>")
        return
    try:
        minutes = int(parts[1])
        if minutes <= 0:
            raise ValueError()
    except:
        bot.reply_to(message, "Неверное время. Укажи целое количество минут.")
        return

    target = parts[2]
    target_identifier = target.lstrip('@')

    price_per_minute = get_price()
    total_cost = minutes * price_per_minute

    current_balance = get_bot_balance(chat_id)
    if current_balance < total_cost:
        bot.reply_to(message, f"Недостаточно звёзд на счёте бота. Нужно {total_cost} ⭐, доступно {current_balance} ⭐")
        return

    # списываем со счёта бота
    set_bot_balance(chat_id, current_balance - total_cost)

    # try to resolve username->id
    target_id = None
    try:
        target_id = int(target_identifier)
    except:
        # try find in chat
        try:
            member = bot.get_chat_member(int(chat_id), target_identifier)
            target_id = member.user.id
        except Exception:
            target_id = None

    until = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
    until_iso = until.isoformat()

    stored_ident = str(target_id) if target_id else str(target_identifier)
    db_execute("INSERT OR REPLACE INTO active_mutes(chat_id, user_identifier, end_time) VALUES (?,?,?)",
               (chat_id, stored_ident, until_iso))

    if target_id:
        try:
            perms = ChatPermissions(can_send_messages=False)
            bot.restrict_chat_member(int(chat_id), int(target_id), permissions=perms, until_date=until)
        except Exception:
            pass

    bot.reply_to(message, f"🔇 {target} замьючен(а) на {minutes} минут. Потрачено: {total_cost} ⭐")

# check and unmute on any message (lightweight)
@bot.message_handler(func=lambda m: True)
def _unmute_check(m):
    try:
        unmute_expired()
    except Exception:
        pass