# plugins/mut.py
import datetime
from telebot.types import ChatPermissions
from main import bot
from core import db_execute

# Админ по username (укажи свой username без @)
ADMIN_USERNAME = "Sugar_Daddy_rip"

# Стоимость за 1 минуту (по умолчанию 2 звезд)
def get_price():
    row = db_execute("SELECT balance FROM bot_balance WHERE chat_id=?",( "price_store",), fetch=True)
    # Используем специальную запись в bot_balance для хранения цены (hack: key "price_store")
    # Если нет — вернём 2
    return int(row[0]['balance']) if row else 2

def set_price(new_price:int):
    # Запишем в bot_balance ключ "price_store" (string)
    db_execute("INSERT OR REPLACE INTO bot_balance(chat_id,balance) VALUES (?,?)", ("price_store", int(new_price)))

# Получить баланс бота для конкретного чата (в звёздах)
def get_bot_balance(chat_id:str) -> int:
    row = db_execute("SELECT balance FROM bot_balance WHERE chat_id=?", (str(chat_id),), fetch=True)
    return int(row[0]['balance']) if row else 0

def set_bot_balance(chat_id:str, val:int):
    db_execute("INSERT OR REPLACE INTO bot_balance(chat_id,balance) VALUES (?,?)", (str(chat_id), int(val)))

# Добавим таблицу active_mutes (если не создано — core.init_db уже создал, но дублировать безопасно)
db_execute("""CREATE TABLE IF NOT EXISTS active_mutes (
    chat_id TEXT,
    user_identifier TEXT,
    end_time TEXT,
    PRIMARY KEY(chat_id, user_identifier)
)""")

# Команда для владельца: /price <x> (работает если отправлено владельцем в ЛС или в любом чате)
@bot.message_handler(commands=['price'])
def cmd_price(message):
    # Разрешаем менять только если username совпадает
    if getattr(message.from_user, "username", None) != ADMIN_USERNAME:
        return  # silently ignore для не-админа
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"Текущая цена за 1 минуту: {get_price()} ⭐")
        return
    try:
        newp = int(parts[1])
    except:
        bot.reply_to(message, "Используй: /price <целое число>")
        return
    set_price(newp)
    bot.reply_to(message, f"✅ Цена за 1 минуту мьюта установлена: {newp} ⭐")

# Вспомогательная функция: снятие просроченных мутов (проверка и удаление записей)
def unmute_expired(chat_id:str=None):
    now = datetime.datetime.utcnow()
    rows = db_execute("SELECT chat_id, user_identifier, end_time FROM active_mutes", fetch=True)
    for r in rows:
        end = datetime.datetime.fromisoformat(r['end_time'])
        if now >= end:
            # можно попытаться снять ограничения у пользователя (если сохранили id), но часто мы храним username
            try:
                # пробуем снимать по username — но Telegram требует id; если у нас есть id в user_identifier, используем
                uid = r['user_identifier']
                # Если user_identifier — число, используем int
                try:
                    uid_int = int(uid)
                except:
                    uid_int = None
                if uid_int:
                    # даём стандартные права
                    permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                                  can_send_other_messages=True, can_add_web_page_previews=True)
                    bot.restrict_chat_member(int(r['chat_id']), uid_int, permissions=permissions)
            except Exception:
                # игнорируем ошибки снятия — возможно бот не имеет прав
                pass
            # удаляем запись о муте
            db_execute("DELETE FROM active_mutes WHERE chat_id=? AND user_identifier=?", (r['chat_id'], r['user_identifier']))

# Команда /mut <minutes> @username_OR_userid
@bot.message_handler(commands=['mut'])
def cmd_mut(message):
    chat_id = str(message.chat.id)
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "Используй: /mut <минуты> <@username или user_id>")
        return
    # parse minutes
    try:
        minutes = int(parts[1])
        if minutes <= 0:
            raise ValueError()
    except:
        bot.reply_to(message, "Неверное время. Укажи целое количество минут.")
        return

    target = parts[2]
    # если указан @username — убираем @
    target_identifier = target.lstrip('@')

    price_per_minute = get_price()
    total_cost = minutes * price_per_minute

    # проверяем баланс бота для данного чата (глобально — на кого зачисляются звезды — у тебя может быть один аккаунт бота)
    current_balance = get_bot_balance(chat_id)
    if current_balance < total_cost:
        bot.reply_to(message, f"Недостаточно звёзд на счёте бота в этом чате. Нужно {total_cost} ⭐, доступно {current_balance} ⭐")
        return

    # списываем звёзды (запись в базе)
    set_bot_balance(chat_id, current_balance - total_cost)

    # выставляем мут: если target_identifier — число (id), используем id, иначе пытаемся найти пользователя по username
    target_id = None
    try:
        target_id = int(target_identifier)
    except:
        # попробуем получить участника по username (работает только если бот знает пользователя в чате)
        try:
            member = bot.get_chat_member(int(chat_id), target_identifier)
            target_id = member.user.id
        except Exception:
            target_id = None

    # рассчитываем until_date UTC
    until = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
    until_iso = until.isoformat()

    # сохраняем мут в базе — сохраняем user identifier (если есть id — его, иначе username)
    ident_to_store = str(target_id) if target_id else str(target_identifier)
    db_execute("INSERT OR REPLACE INTO active_mutes(chat_id, user_identifier, end_time) VALUES (?,?,?)",
               (chat_id, ident_to_store, until_iso))

    # попытаемся применить ограничение через API, если у нас есть id
    if target_id:
        permissions = ChatPermissions(can_send_messages=False)
        try:
            bot.restrict_chat_member(int(chat_id), int(target_id), permissions=permissions, until_date=until)
        except Exception:
            # если не удалось (неадмин или другое) — всё равно считаем, что мут активен в БД
            pass

    bot.reply_to(message, f"🔇 {target} замьючен(а) на {minutes} минут. Потрачено: {total_cost} ⭐")

# Обработчик: при любом сообщении проверяем просроченные мьюты и удаляем их
@bot.message_handler(func=lambda m: True)
def _mut_check_every_message(m):
    try:
        unmute_expired()
    except Exception:
        pass