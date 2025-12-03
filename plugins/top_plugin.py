import json
import os

# Пути к обычным файлам игр — они создаются/обновляются твоими плагинами sisi/hui/klitor
FILES = {
    "sisi": "data/sisi.json",
    "hui": "data/hui.json",
    "klitor": "data/klitor.json"
}

EMOJI = {
    "sisi": "🎀",
    "hui": "🍌",
    "klitor": "🍑"
}


def _load_file(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)
    except Exception:
        return {}


def _user_name_from_info_or_api(info, bot, chat_id, user_id):
    # 1) prefer stored name
    name = None
    if isinstance(info, dict):
        name = info.get("name")
        # some old files stored numeric names — skip those
        if isinstance(name, str) and name.strip() and not name.isdigit():
            return name

    # 2) try API (safe: wrap in try/except)
    try:
        member = bot.get_chat_member(chat_id, int(user_id))
        u = member.user
        full = getattr(u, "full_name", None)
        if full:
            return full
        if getattr(u, "first_name", None):
            if getattr(u, "last_name", None):
                return f"{u.first_name} {u.last_name}"
            return u.first_name
        if getattr(u, "username", None):
            return "@" + u.username
    except Exception:
        pass

    # 3) fallback
    return f"User{user_id}"


def _format_top_from_file(game, chat_id, bot):
    """
    Возвращает текст топа для конкретной игры.
    game: 'sisi'|'hui'|'klitor'
    chat_id: integer or str
    """
    file = FILES.get(game)
    data = _load_file(file)
    cid = str(chat_id)

    if cid not in data or not data[cid]:
        return f"{EMOJI[game]} Топ по {game}: Тут ещё никто не играл 😢"

    # data[cid] expected structure: { user_id: { "name":..., "size":... OR "size_mm":... } }
    rows = []
    for uid, info in data[cid].items():
        # determine size depending on game
        if game == "klitor":
            # try both keys
            mm = info.get("size_mm") if isinstance(info, dict) else None
            if mm is None:
                mm = info.get("size") if isinstance(info, dict) else 0
            try:
                mm = float(mm)
            except Exception:
                mm = 0.0
            rows.append((uid, info, mm))
        else:
            size = info.get("size") if isinstance(info, dict) else 0
            try:
                size = int(size)
            except Exception:
                size = 0
            rows.append((uid, info, size))

    # sort
    if game == "klitor":
        rows.sort(key=lambda x: x[2], reverse=True)  # by mm
    else:
        rows.sort(key=lambda x: x[2], reverse=True)

    # build message (top 10 or less)
    lines = [f"{EMOJI[game]} Топ по {game}:"]
    for i, (uid, info, size_val) in enumerate(rows[:10], start=1):
        name = _user_name_from_info_or_api(info, bot, chat_id, uid)
        if game == "klitor":
            # convert mm -> cm with one decimal (data stored in mm)
            cm = size_val / 10.0
            lines.append(f"{i}. {name} — {cm:.1f} см")
        elif game == "hui":
            lines.append(f"{i}. {name} — {size_val} см")
        else:  # sisi
            lines.append(f"{i}. {name} — {size_val} размер")

    return "\n".join(lines)


# функция, вызываемая из main: шлёт три отдельных сообщения (по одной игре)
def handle(bot, message):
    chat_id = message.chat.id

    # for each game build and send separate message
    for game in ("sisi", "hui", "klitor"):
        text = _format_top_from_file(game, chat_id, bot)
        try:
            bot.send_message(chat_id, text)
        except Exception:
            # в случае ошибки отправляем простым reply
            try:
                bot.reply_to(message, text)
            except Exception:
                pass


# /my handler (вызывается отдельным декоратором в main.py)
def handle_my(bot, message):
    chat_id = str(message.chat.id)
    uid = str(message.from_user.id)

    parts = []
    # build each stat by reading respective file
    for game in ("sisi", "hui", "klitor"):
        file = FILES[game]
        data = _load_file(file)
        if chat_id in data and uid in data[chat_id]:
            info = data[chat_id][uid]
            name = _user_name_from_info_or_api(info, bot, chat_id, uid)
            if game == "klitor":
                mm = info.get("size_mm") if isinstance(info, dict) else None
                if mm is None:
                    mm = info.get("size") if isinstance(info, dict) else 0
                try:
                    mm = float(mm)
                except Exception:
                    mm = 0.0
                parts.append(f"💎 Клитор: {mm/10:.1f} см")
            elif game == "hui":
                size = info.get("size") if isinstance(info, dict) else 0
                try:
                    size = int(size)
                except Exception:
                    size = 0
                parts.append(f"🍌 Хуй: {size} см")
            else:
                size = info.get("size") if isinstance(info, dict) else 0
                try:
                    size = int(size)
                except Exception:
                    size = 0
                parts.append(f"🎀 Сиськи: {size} размер")
        else:
            # no record
            if game == "klitor":
                parts.append(f"💎 Клитор: ещё не играл")
            elif game == "hui":
                parts.append(f"🍌 Хуй: ещё не играл")
            else:
                parts.append(f"🎀 Сиськи: ещё не играл")

    # Build name to display: try to prefer profile name
    display_name = None
    # try to read name from any game file
    for game in ("sisi", "hui", "klitor"):
        data = _load_file(FILES[game])
        if chat_id in data and uid in data[chat_id]:
            info = data[chat_id][uid]
            name = info.get("name") if isinstance(info, dict) else None
            if name:
                display_name = name
                break
    # fallback to API
    if not display_name:
        try:
            m = bot.get_chat_member(int(message.chat.id), int(uid))
            u = m.user
            display_name = getattr(u, "full_name", None) or getattr(u, "first_name", None) or ("@" + u.username if getattr(u, "username", None) else f"User{uid}")
        except Exception:
            display_name = f"User{uid}"

    out = f"👤 {display_name}\n\n" + "\n".join(parts)
    try:
        bot.send_message(message.chat.id, out)
    except Exception:
        bot.reply_to(message, out)