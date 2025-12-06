from telebot import TeleBot, types
import random

bot = TeleBot("TOKEN")

# банк по чатам
bank = {}
# цена лото
lotoprice = {}
# донатеры по чатам
donors = {}

### УСТАНОВКА ПРАЙСА /lotoprice
@bot.message_handler(commands=['lotoprice'])
def set_price(message):
    chat_id = message.chat.id
    args = message.text.split()

    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "Укажи сумму: /lotoprice 100")
        return

    price = int(args[1])
    lotoprice[chat_id] = price
    bot.reply_to(message, f"🎯 Лото прайс установлен: {price} ⭐")

    if chat_id not in bank:
        bank[chat_id] = 0
    if chat_id not in donors:
        donors[chat_id] = {}

### УЧЁТ ОПЛАТЫ ЧЕРЕЗ КОМАНДУ BOOSTS
@bot.message_handler(commands=['boosts'])
def boosts(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    args = message.text.split()

    # если /boosts без числа → 1
    amount = 1

    if len(args) > 1 and args[1].isdigit():
        amount = int(args[1])

    add_to_bank(chat_id, user_id, amount)
    bot.reply_to(message, f"🔥 Boost добавлен: +{amount} ⭐")

### УЧЁТ МУТА: 2 звезды за минуту
@bot.message_handler(commands=['mut'])
def mute_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "Используй: /mut 5  (5 минут)")
        return

    minutes = int(args[1])
    amount = minutes * 2

    add_to_bank(chat_id, user_id, amount)
    bot.reply_to(message, f"🔇 Мут: {minutes} мин → +{amount} ⭐")

### ДОБАВЛЕНИЕ В БАНК
def add_to_bank(chat_id, user_id, amount):
    if chat_id not in bank:
        bank[chat_id] = 0
    if chat_id not in donors:
        donors[chat_id] = {}
    if user_id not in donors[chat_id]:
        donors[chat_id][user_id] = 0

    donors[chat_id][user_id] += amount
    bank[chat_id] += amount

    check_loto(chat_id)

### ПРОВЕРКА РОЗЫГРЫША
def check_loto(chat_id):
    if chat_id not in lotoprice:
        return

    if bank[chat_id] >= lotoprice[chat_id]:
        run_loto(chat_id)

### РОЗЫГРЫШ
def run_loto(chat_id):
    users = list(donors[chat_id].keys())

    if not users:
        return

    winner = random.choice(users)

    # сбрасываем банк
    bank[chat_id] = 0
    donors[chat_id] = {}

    bot.send_message(
        chat_id,
        f"🎉 *ЛОТО!* Победитель: [{winner}](tg://user?id={winner})\n"
        f"Подарок: 🎁 50 Stars Gift",
        parse_mode="Markdown"
    )

    # кнопка подарка
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🎁 Подарить 50⭐", pay=True)
    markup.add(btn)

    bot.send_invoice(
        chat_id,
        title="50 Stars Gift",
        description="Приз победителю лото",
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice("Gift", 50)],
        invoice_payload="gift50",
        reply_markup=markup
    )

### РУЧНАЯ КОМАНДА /gift
@bot.message_handler(commands=['gift'])
def manual_gift(message):
    chat_id = message.chat.id
    run_loto(chat_id)

bot.polling()