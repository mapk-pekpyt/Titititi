if text.startswith("продать ") and text.split()[1].isdigit():
    n = int(text.split()[1])

    if weed < n:
        return bot.reply_to(
            message,
            f"❌ Ты не можешь впарить {n}\nНе хватает {n - weed}"
        )

    # риск подставы
    if random.random() < 0.15:
        add(user.id, "weed", -n)
        return bot.reply_to(
            message,
            f"🚨 Подстава!\n"
            f"Покупатель оказался ментом.\n"
            f"Ты сбросил {n} грамм и свалил."
        )

    earn = n * 1
    add(user.id, "weed", -n)
    add(user.id, "money", earn)

    return bot.reply_to(
        message,
        f"💸 Впарил травку {n} грамм\n"
        f"Получил {earn} 💶"
    )