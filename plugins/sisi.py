from plugins.common import weighted_random, get_name
from plugins.top_plugin import ensure_user, update_stat, update_date, was_today
from plugins.bust_price import price_data, save_price
import json


# =============================
#         /sisi — игра
# =============================
def handle(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id

    data = ensure_user(chat, user)
    user_data = data[str(chat)][str(user.id)]

    # Проверяем лимит раз в день
    if was_today(chat, user, "last_sisi"):
        cur = user_data["sisi"]

        # защита от минуса
        if cur < 0:
            cur = 0
            user_data["sisi"] = 0

        return bot.reply_to(
            message,
            f"{name}, ты сегодня уже играла 😳\n"
            f"Твои вишенки: **{cur}** 🍒"
        )

    delta = weighted_random()
    old = user_data["sisi"]
    new_val = max(0, old + delta)
    user_data["sisi"] = new_val

    update_date(chat, user, "last_sisi")

    bot.reply_to(
        message,
        f"{name}, твои сисечки изменились на **{delta:+}**, "
        f"теперь размер **{new_val}** 🍒"
    )


# =============================
#     /busts — буст за звезды
# =============================
def handle_busts(bot, message):
    user = message.from_user
    name = get_name(user)
    chat = message.chat.id
    uid = str(user.id)

    data = ensure_user(chat, user)
    user_data = data[str(chat)][uid]

    cost = price_data["price"]

    if user_data.get("stars", 0) < cost:
        return bot.reply_to(
            message,
            f"{name}, у тебя недостаточно ⭐\n"
            f"Нужно: **{cost}**, у тебя: **{user_data.get('stars', 0)}**"
        )

    # списание
    user_data["stars"] -= cost
    user_data["sisi"] += 1

    bot.reply_to(
        message,
        f"{name}, ✨ Твои сисечки стали больше!\n"
        f"Теперь размер: **{user_data['sisi']}** 🍒"
    )


# =============================
#   /bustprice X — изменить цену
# =============================
def handle_bustprice(bot, message):
    parts = message.text.split()

    if len(parts) < 2 or not parts[1].isdigit():
        return bot.reply_to(message, "Использование: /bustprice 5")

    new_price = int(parts[1])
    price_data["price"] = new_price
    save_price(new_price)

    bot.reply_to(message, f"Новая цена буста: **{new_price} ⭐**")