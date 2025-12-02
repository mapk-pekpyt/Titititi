from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading, time

MUT_PRICE = 10  # ⭐
MUT_DURATION = 60  # сек

active_mutes = {}

def apply_mute(bot, chat_id, user_id, duration_sec, admin_name):
    bot.restrict_chat_member(chat_id, user_id, can_send_messages=False)
    bot.send_message(chat_id, f"🚫 Пользователь {user_id} лишён голоса на {duration_sec} сек. (царь {admin_name})")

    def unmute():
        time.sleep(duration_sec)
        bot.restrict_chat_member(chat_id, user_id, can_send_messages=True)
        bot.send_message(chat_id, f"✅ Пользователь {user_id} снова может писать!")

    threading.Thread(target=unmute).start()

def handle(bot, message):
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Нужно ответить на сообщение пользователя, которого мутим")
        return

    target_id = message.reply_to_message.from_user.id
    target_name = message.reply_to_message.from_user.first_name
    admin_name = message.from_user.first_name

    if MUT_PRICE == 0:
        apply_mute(bot, message.chat.id, target_id, MUT_DURATION, admin_name)
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"Оплатить {MUT_PRICE} ⭐", callback_data=f"pay_mut:{target_id}:{MUT_PRICE}:{MUT_DURATION}"))
    bot.send_message(message.chat.id, f"💰 {admin_name}, оплатите мут для {target_name}", reply_markup=markup)