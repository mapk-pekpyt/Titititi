from core import db_execute

ADMIN_IDS = ["<твой Telegram ID>"]  # сюда добавь свой ID

def setup(bot):
    price_per_minute = 2

    @bot.message_handler(commands=["price"])
    def set_price(message):
        if str(message.from_user.id) not in ADMIN_IDS:
            return
        try:
            global price_per_minute
            price_per_minute = int(message.text.split()[1])
            bot.send_message(message.chat.id, f"Цена за 1 минуту мута: {price_per_minute} звезд")
        except:
            bot.send_message(message.chat.id, "Использование: /price <число>")

    @bot.message_handler(commands=["mut"])
    def give_mut(message):
        try:
            args = message.text.split()
            minutes = int(args[1])
            if minutes <= 0:
                return
            # Здесь должна быть проверка поступления звезд у пользователя
            # Пока просто пример
            bot.send_message(message.chat.id, f"Пользователь {message.from_user.first_name} получил мут на {minutes} минут")
        except:
            bot.send_message(message.chat.id, "Использование: /mut <минуты>")