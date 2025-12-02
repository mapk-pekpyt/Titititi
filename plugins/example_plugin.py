def setup(bot):
    @bot.message_handler(commands=["ping"])
    def ping(message):
        bot.send_message(message.chat.id, "Pong!")