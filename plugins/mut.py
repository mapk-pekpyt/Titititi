import telebot
import datetime
from main import bot, db_execute

# Ваш Telegram username, кто может менять цену
BOT_OWNER = "Sugar_Daddy_rip"

# Таблица для активных мутов
db_execute("""
CREATE TABLE IF NOT EXISTS active_mutes (
    chat_id TEXT,
    user_id TEXT,
    end_time TEXT,
    PRIMARY KEY(chat_id, user_id)
)
""")

# Таблица для хранения цены 1 минуты мьюта
db_execute("""
CREATE TABLE IF NOT EXISTS mute_price (
    id INTEGER PRIMARY KEY,
    price INTEGER
)
""")

# Инициализация цены (по умолчанию 2 звезды)
if not db_execute("SELECT price FROM mute_price", fetch=True):
    db_execute("INSERT INTO mute_price(id, price) VALUES (1,2)")

def get_mute_price() -> int:
    row = db_execute("SELECT price FROM mute_price WHERE id=1", fetch=True)
    return row[0]['price'] if row else 2

def set_mute_price(new_price: int):
    db_execute("UPDATE mute_price SET price=? WHERE id=1", (new_price,))

def unmute_expired():
    """Снимает мут с пользователей, если время закончилось."""
    now = datetime.datetime.utcnow()
    rows = db_execute("SELECT chat_id, user_id, end_time FROM active_mutes", fetch=True)
    for r in rows:
        end_time = datetime.datetime.fromisoformat(r['end_time'])
        if now >= end_time:
            db_execute("DELETE FROM active_mutes WHERE chat_id=? AND user_id=?", (r['chat_id'], r['user_id']))

# Команда для установки цены /price (только для владельца)
@bot.message_handler(commands=['price'])
def cmd_price(m):
    if m.from_user.username != BOT_OWNER:
        return
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, f"Текущая цена 1 минуты мьюта: {get_mute_price()} ⭐")
        return
    try:
        new_price = int(parts[1])
        set_mute_price(new_price)
        bot.reply_to(m, f"💰 Цена за 1 минуту мьюта изменена на {new_price} ⭐")
    except ValueError:
        bot.reply_to(m, "Используй: /price <число>")

# Команда для выдачи мута /mut
@bot.message_handler(commands=['mut'])
def cmd_mut(m):
    chat_id = m.chat.id
    parts = m.text.split()
    
    if len(parts) < 3:
        bot.reply_to(m, "Используй: /mut <минуты> @пользователь")
        return
    
    try:
        minutes = int(parts[1])
    except ValueError:
        bot.reply_to(m, "Неверный формат времени. Укажи число минут.")
        return
    
    target_username = parts[2].lstrip('@')
    cost_per_minute = get_mute_price()
    total_cost = minutes * cost_per_minute
    
    # Получаем текущий баланс бота (реальные звезды поступают через Telegram)
    # Здесь предполагается, что баланс обновляется из реальной оплаты
    row = db_execute("SELECT balance FROM bot_balance WHERE chat_id=?", (str(chat_id),), fetch=True)
    current_balance = row[0]['balance'] if row else 0
    
    if current_balance < total_cost:
        bot.reply_to(m, f"Недостаточно звезд на счёте бота. Нужно {total_cost} ⭐, доступно {current_balance} ⭐")
        return
    
    # Списываем звезды
    db_execute("UPDATE bot_balance SET balance=balance-? WHERE chat_id=?", (total_cost, str(chat_id)))
    
    # Выдаём мут
    end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
    db_execute("INSERT OR REPLACE INTO active_mutes(chat_id,user_id,end_time) VALUES (?,?,?)",
               (str(chat_id), target_username, end_time.isoformat()))
    
    bot.reply_to(m, f"🔇 Пользователь @{target_username} замьючен на {minutes} минут. ⭐ Потрачено: {total_cost}")

# Проверка и снятие мутов при любом сообщении
@bot.message_handler(func=lambda message: True)
def remove_expired_mutes(message):
    unmute_expired()