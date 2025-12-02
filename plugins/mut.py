from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time

# Настройки мутов
MUT_PRICE = 10  # цена за мут в тг звездах, 0 = бесплатный мут
MUT_DURATION_DEFAULT = 60  # сек

# Словарь для хранения активных мутов
active_mutes = {}

def apply_mute(bot, chat_id, user_id, duration_sec, admin_name):
    # Выключаем возможность писать
    bot.restrict_chat_member(chat_id, user_id, can_send_messages=False)
    bot.send_message(chat_id, f"🚫 Пользователь {user_id} лишён голоса на {duration_sec} сек. (царь {admin_name})")

    # Запускаем таймер для восстановления
    def unmute():
        time.sleep(duration_sec)
        bot.restrict_chat_member(chat_id, user_id, can_send_messages=True)
        bot.send_message(chat_id, f"✅ Пользователь {user_id} снова может писать!")

    threading.Thread(target=unmute).start()

def handle_mut(bot, message, price=MUT_PRICE):
    # получаем id того, на кого мут
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Нужно ответить на сообщение пользователя, которого мутим")
        return

    target_id = message.reply_to_message.from_user.id
    target_name = message.reply_to_message.from_user.first_name
    admin_name = message.from_user.first_name

    # Если цена 0 — сразу мутим
    if price == 0:
        apply_mute(bot, message.chat.id, target_id, MUT_DURATION_DEFAULT, admin_name)
        return

    # Иначе — кнопка оплаты
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"Оплатить {price} ⭐", callback_data=f"pay_mut:{target_id}:{price}:{MUT_DURATION_DEFAULT}"))
    bot.send_message(message.chat.id, f"💰 {admin_name}, оплатите мут для {target_name}", reply_markup=markup)