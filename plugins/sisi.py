from core import db_execute, today_date, random_delta

GAME_NAME = "sisi"

def setup(bot):
    @bot.message_handler(commands=["sisi"])
    def sisi_game(message):
        chat_id = str(message.chat.id)
        user_id = str(message.from_user.id)
        today = today_date()

        row = db_execute(
            "SELECT value, last_play FROM game_data WHERE chat_id=? AND user_id=? AND game=?",
            (chat_id, user_id, GAME_NAME),
            fetch=True
        )
        if row and row[0][1] == today:
            bot.send_message(chat_id, f"Упс, ты уже играл сегодня! Твой размер: {row[0][0]}")
            return

        current = row[0][0] if row else 0
        delta = random_delta(-10, 10)
        new_value = max(0, current + delta)

        db_execute(
            "REPLACE INTO game_data (chat_id, user_id, game, value, last_play) VALUES (?, ?, ?, ?, ?)",
            (chat_id, user_id, GAME_NAME, new_value, today)
        )

        bot.send_message(chat_id, f"{message.from_user.first_name}, твой размер груди вырос на {delta}, теперь он равен {new_value}")