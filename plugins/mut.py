from main import bot, get_display_name, ADMIN_ID
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

DATA_FILE = "data/mut.json"
PRICE_PER_MIN = 10  # цена за минуту в ТГ-звездах

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@bot.message_handler(commands=["mut"])
def mut_user(message):
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Ответь на сообщение пользователя, которого хочешь замутить.")
        return

    try:
        minutes = int(message.text.split()[1])
    except:
        bot.reply_to(message, "⚠️ Укажи количество минут в формате /mut 5")
        return

    target = message.reply_to_message.from_user
    user_name = get_display_name(target)
    admin_name = get_display_name(message)

    if minutes == 0 or ADMIN_ID == message.from_user.id:
        # мгновенный мут от администратора или за 0 ТГ-звезд
        bot.restrict_chat_member(message.chat.id, target.id, can_send_messages=False)
        bot.reply_to(message, f"🔒 {user_name} лишен голоса на {minutes} минут! Царь {admin_name} 👑 сделал это мгновенно.")
        return

    # кнопка для оплаты ТГ-звездами
    markup = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton(text=f"💫 Оплатить {minutes*PRICE_PER_MIN} звезд", callback_data=f"pay_mut:{target.id}:{minutes}")
    markup.add(pay_button)

    bot.reply_to(message, f"💰 {admin_name} хочет замутить {user_name} на {minutes} минут. Оплати ТГ-звезды:", reply_markup=markup)

# обработка оплаты
@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_mut:"))
def pay_mut_callback(call):
    _, target_id, minutes = call.data.split(":")
    target_id = int(target_id)
    minutes = int(minutes)

    # здесь должна быть логика проверки оплаты (симуляция)
    # если оплата успешна:
    bot.restrict_chat_member(call.message.chat.id, target_id, can_send_messages=False)
    bot.answer_callback_query(call.id, "✅ Оплата прошла успешно!")
    bot.edit_message_text(f"🔒 Пользователь лишен голоса на {minutes} минут! 💫", call.message.chat.id, call.message.message_id)