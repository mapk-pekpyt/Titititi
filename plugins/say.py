# plugins/say.py
import telebot
import random
import threading
import time
from datetime import datetime

TRIGGER = "/say"

# Карты Таро
CARDS = [
    "Дурак", "Маг", "Жрица", "Императрица", "Император", "Иерофант",
    "Влюбленные", "Колесница", "Сила", "Отшельник", "Колесо Фортуны",
    "Справедливость", "Повешенный", "Смерть", "Умеренность", "Дьявол",
    "Башня", "Звезда", "Луна", "Солнце", "Суд", "Мир"
]

# Стили предсказаний
STYLES = ["soft", "dark", "witch", "demon", "forest", "celtic"]

# Возможные эффекты порчи
CURSES = [
    "понос 💩", "спотыкание 🤕", "потеря ключей 🗝️", 
    "мокрый нос 🌧️", "сонливость 😴", "забывчивость 🤯",
    "несварение желудка 🤢", "неудачные свидания 💔"
]

# Примеры видений для автоматической рассылки
VISIONS = [
    "Я вижу, {name}, твой путь сегодня будет тернистым, но появится шанс 🌟",
    "Карты говорят, {name}, скоро встретится человек, который изменит всё 🔮",
    "Таро шепчет, {name}, будь осторожен с новыми знакомыми 🃏",
    "Вижу перемены, {name}, они будут резкими, но к лучшему 🌪️",
    "Судьба играет с тобой, {name}, не пытайся бороться с течением 🔥"
]

def get_name(user):
    if user.first_name:
        return user.first_name
    return "ты"

def draw_cards(n=3):
    return random.sample(CARDS, k=n)

def generate_prediction(user_name, n=3):
    cards = draw_cards(n)
    start = random.choice([
        "Я вижу", "Карты говорят", "Таро шепчет", "Судьба предвещает", "Предзнаменование ясно"
    ])
    middle = f"Выпали карты: {', '.join(cards)}."
    end = random.choice([
        "Это сулит изменения в личной жизни ✨",
        "Будь осторожен с финансами 💰",
        "Новые возможности появятся неожиданно 🌟",
        "В ближайшие дни возможны трудности 😵",
        "Судьба преподнесет испытание, но ты справишься 💪",
        "Сегодняшний день благоприятен для смелых решений ⚡"
    ])
    return f"{start}, {user_name}. {middle} {end}"

def handle_curse(bot, message):
    target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    target_name = get_name(target_user)
    effect = random.choice(CURSES)
    bot.reply_to(
        message,
        f"{target_name}, черная магия настигла тебя: {effect}!"
    )

def send_vision(bot, chat):
    try:
        members = bot.get_chat_administrators(chat.id)  # берем участников для примера
        if not members:
            return
        user = random.choice(members).user
        name = get_name(user)
        vision = random.choice(VISIONS)
        bot.send_message(chat.id, vision.format(name=name))
    except Exception:
        pass

def periodic_visions(bot, chats, interval=600):
    def run():
        while True:
            time.sleep(random.randint(interval, interval + 300))  # рандомно каждые 10–15 мин
            if not chats:
                continue
            chat = random.choice(chats)
            send_vision(bot, chat)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()

def handle(bot, message, chats=None):
    text = message.text or ""
    text_lower = text.lower()
    user_name = get_name(message.from_user)

    # Порча
    if "порча" in text_lower or "curse" in text_lower:
        handle_curse(bot, message)
        return

    # Определяем количество карт
    parts = text.split()
    n = 3
    if len(parts) >= 2:
        try:
            n_candidate = int(parts[1])
            if n_candidate in [3, 5, 7, 10]:
                n = n_candidate
        except:
            pass

    prediction = generate_prediction(user_name, n)
    bot.reply_to(message, prediction)

    # Регистрируем чат для периодических видений
    if chats is not None and message.chat not in chats:
        chats.append(message.chat)