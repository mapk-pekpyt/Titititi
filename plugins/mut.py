
from core import db_execute
from telebot import types
import datetime

GAME_NAME = "mut"

def setup(bot):
    @bot.message_handler(commands=["price"])
    def set_price(message):
        if str(message.from_user.username) != "Sugar_Daddy_rip":
            bot.send_message(message.chat.id, "❌ Только админ может менять цену!")
            return
        try:
            price = int(message.text.split()[1])
            chat_id = str(message.chat.id)
            db_execute("REPLACE INTO mut_settings (chat_id, price_per_min) VALUES (?, ?)", (chat_id, price))
            bot.send_message(chat_id, f"💰 Цена за 1 минуту мута установлена: {price} ⭐")
        except:
            bot.send_message(message.chat.id, "❌ Используй: /price <число>")

    @bot.message_handler(commands=["mut"])
    def give_mut(message):
        if not message.reply_to_message:
            bot.send_message(message.chat.id, "❌ Команду нужно писать в ответ на сообщение пользователя.")
            return
        try:
            minutes = int(message.text.split()[1])
        except:
            bot.send_message(message.chat.id, "❌ Укажи число минут: /mut <минуты>")
            return

        chat_id = str(message.chat.id)
        price_row = db_execute("SELECT price_per_min FROM mut_settings WHERE chat_id=?", (chat_id,), fetch=True)
        price_per_min = price_row[0][0] if price_row else 2
        total_price = price_per_min * minutes

        target_user = message.reply_to_message.from_user
        sender_user = message.from_user

        # проверить баланс отправителя
        balance_row = db_execute("SELECT balance FROM stars_balance WHERE user_id=?", (sender_user.id,), fetch=True)
        balance = balance_row[0][0] if balance_row else 0

        if balance < total_price:
            bot.send_message(chat_id, f"⭐ У тебя недостаточно звезд. Нужно {total_price} ⭐")
            return

        # снимаем баланс
        db_execute("UPDATE stars_balance SET balance=balance-? WHERE user_id=?", (total_price, sender_user.id))

        # даем мут
        bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=int(datetime.datetime.now().timestamp()) + minutes*60
        )

        bot.send_message(
            chat_id,
            f"⛔ Пользователь {target_user.first_name} лишён голоса на {minutes} минут(ы), т.к. царь @{sender_user.username} оплатил {total_price} ⭐"
        )