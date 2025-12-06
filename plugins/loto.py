from telebot import types
import random

bank = {}
donors = {}
lotoprice = {}

def init(bot):

    # /lotoprice
    @bot.message_handler(commands=['lotoprice'])
    def set_price(message):
        chat_id = message.chat.id
        args = message.text.split()

        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "Укажи цену: /lotoprice 100")
            return

        price = int(args[1])
        lotoprice[chat_id] = price

        if chat_id not in bank:
            bank[chat_id] = 0
        if chat_id not in donors:
            donors[chat_id] = {}

        bot.reply_to(message, f"🎯 Порог лото: {price} ⭐")

    # /boosts
    @bot.message_handler(commands=['boosts'])
    def boosts_handler(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        args = message.text.split()

        amount = 1
        if len(args) > 1 and args[1].isdigit():
            amount = int(args[1])

        add_to_bank(bot, chat_id, user_id, amount)
        bot.reply_to(message, f"🔥 Boost +{amount} ⭐")

    # /mut
    @bot.message_handler(commands=['mut'])
    def mute_handler(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        args = message.text.split()

        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "Используй: /mut 5")
            return

        minutes = int(args[1])
        amount = minutes * 2

        add_to_bank(bot, chat_id, user_id, amount)
        bot.reply_to(message, f"🔇 Мут {minutes} мин → +{amount} ⭐")

    # /gift
    @bot.message_handler(commands=['gift'])
    def manual_gift(message):
        run_loto(bot, message.chat.id)


def add_to_bank(bot, chat_id, user_id, amount):
    if chat_id not in bank:
        bank[chat_id] = 0
    if chat_id not in donors:
        donors[chat_id] = {}
    if user_id not in donors[chat_id]:
        donors[chat_id][user_id] = 0

    donors[chat_id][user_id] += amount
    bank[chat_id] += amount

    check_loto(bot, chat_id)


def check_loto(bot, chat_id):
    if chat_id in lotoprice and bank[chat_id] >= lotoprice[chat_id]:
        run_loto(bot, chat_id)


def run_loto(bot, chat_id):
    if chat_id not in donors or not donors[chat_id]:
        return

    users = list(donors[chat_id].keys())
    winner = random.choice(users)

    bank[chat_id] = 0
    donors[chat_id] = {}

    bot.send_message(
        chat_id,
        f"🎉 ЛОТО!\nПобедитель: [{winner}](tg://user?id={winner})\n🎁 50 Stars Gift!",
        parse_mode="Markdown"
    )