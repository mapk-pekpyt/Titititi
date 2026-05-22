def handle(bot, message):
    text = (message.text or "").lower().strip()

    cmd = text.split()[0].split("@")[0]

    if cmd != "удалить":
        return

    # нужно ответить на сообщение
    if not message.reply_to_message:
        bot.reply_to(message, "ответь на сообщение, которое надо удалить")
        return

    try:
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        bot.reply_to(message, f"не смог удалить: {e}")