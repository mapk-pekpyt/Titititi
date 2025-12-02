PRICE_FILE = "data/mut_price.json"
import json
import os

def load_price():
    if not os.path.exists(PRICE_FILE):
        return 2  # по умолчанию 2 звезды за минуту
    with open(PRICE_FILE, "r") as f:
        return json.load(f)["price"]

def save_price(price):
    with open(PRICE_FILE, "w") as f:
        json.dump({"price": price}, f)

def handle(bot, message):
    text = message.text
    user_id = message.from_user.id

    # /price x для админа @Sugar_Daddy_rip
    if text.startswith("/price") and message.from_user.username == "Sugar_Daddy_rip":
        try:
            price = int(text.split()[1])
            save_price(price)
            bot.send_message(message.chat.id, f"Цена за минуту Мута установлена на {price} ⭐")
        except:
            bot.send_message(message.chat.id, "Ошибка! Укажите число после /price")
        return

    # Мут на другого пользователя
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "Чтобы выдать мут, ответьте на сообщение пользователя с /mut X")
        return
    try:
        minutes = int(text.split()[1])
    except:
        bot.send_message(message.chat.id, "Укажите количество минут после /mut")
        return

    price_per_minute = load_price()
    total_price = price_per_minute * minutes
    target_user = message.reply_to_message.from_user

    # Здесь должна быть интеграция оплаты ⭐
    bot.send_message(message.chat.id,
                     f"@{target_user.username} будет отключен на {minutes} минут, "
                     f"цена: {total_price} ⭐. Оплатите, чтобы завершить операцию.")