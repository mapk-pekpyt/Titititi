from core import db_execute
from telebot import types

GAMES = ["sisi", "hui", "klitor"]
EMOJIS = {"sisi":"👙", "hui":"🍆", "klitor":"🍑"}

def setup(bot):
    @bot.message_handler(commands=["top"])
    def top_cmd(message):
        chat_id = str(message.chat.id)
        for game in GAMES:
            rows = db_execute(
                "SELECT user_id, value FROM game_data WHERE chat_id=? AND game=? ORDER BY value DESC LIMIT 5",
                (chat_id, game),
                fetch=True
            )
            text = f"{EMOJIS[game]} Топ игроков в {game}:\n"
            if not rows:
                text += "Пусто 😢"
            else:
                for i, (user_id, value) in enumerate(rows, 1):
                    text += f"{i}. <a href='tg://user?id={user_id}'>Пользователь</a> — {value}\n"
            bot.send_message(chat_id, text, parse_mode="HTML")