from plugins import loto  # импортируем лото

def handle_successful(bot, message):
    """
    Вызывается при successful_payment (main должен направлять сюда сообщение)
    распознаёт payload и применяет буст для s i s i
    """
    if not hasattr(message, "successful_payment") or not message.successful_payment:
        return

    payload = getattr(message.successful_payment, "invoice_payload", "") or \
              getattr(message.successful_payment, "payload", "")

    if not payload.startswith("boost:"):
        return

    parts = payload.split(":")
    if len(parts) != 5:
        return
    _, chat_s, payer_s, stat, n_s = parts
    if stat != "sisi":
        return

    try:
        chat_id = int(chat_s)
        payer_id = int(payer_s)
        n = int(n_s)
    except:
        return

    # payer is message.from_user
    payer = message.from_user
    # ensure user exists
    top_plugin.ensure_user(chat_id, payer)

    # apply and save
    top_plugin.update_stat(chat_id, payer, "sisi", n)
    top_plugin.update_date(chat_id, payer, "last_sisi")

    # -----------------------------
    # здесь добавляем лото-банк
    # -----------------------------
    try:
        # каждая звезда = 1 бонусная единица
        loto.add_stars(chat_id, payer.id, n)
    except Exception as e:
        print(f"❌ Ошибка при добавлении звезд в лото: {e}")

    data = top_plugin.load()
    new_size = data[str(chat_id)][str(payer.id)]["sisi"]

    # final message
    bot.send_message(chat_id, f"{get_name(payer)}, твои сисечки выросли на +{n}, теперь твоя грудь {new_size} размера 😳🍒")