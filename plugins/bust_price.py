import os
from telebot.types import Message

BUST_PRICE_FILE = "plugins/bust_price.py"
ADMIN_ID = 5791171535  # твой ID

def handle_boostprice(bot, message: Message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только админ может менять цену буста.")

    parts = (message.text or "").split()
    if len(parts) < 2:
        # показать текущую цену
        try:
            from plugins import bust_price
            current_price = int(bust_price.price_data)
        except:
            current_price = 0
        return bot.reply_to(message, f"Текущая цена буста: {current_price} ⭐")

    try:
        new_price = int(parts[1])
    except:
        return bot.reply_to(message, "❗ Укажи целое число: /boostprice 1000")

    # сохраняем в файл
    with open(BUST_PRICE_FILE, "w", encoding="utf-8") as f:
        f.write(f"price_data = {new_price}")

    bot.reply_to(message, f"✅ Цена буста установлена: {new_price} ⭐")