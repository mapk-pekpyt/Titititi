# plugins/top_plugin.py
import json
import os
from typing import Any, Dict

# Путь к файлам данных игр (подставь свои пути, если у тебя другие)
FILES = {
    "sisi": "data/sisi.json",
    "hui": "data/hui.json",
    "klitor": "data/klitor.json",
}

EMOJI = {
    "sisi": "🎀",
    "hui": "🍌",
    "klitor": "🍑",
}

# ------- Вспомогалки -------
def _load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)
    except Exception:
        return {}

def _safe_name_from_info(info: Any) -> str:
    try:
        if isinstance(info, dict):
            n = info.get("name") or info.get("display_name") or info.get("full_name")
            if isinstance(n, str) and n.strip() and not n.strip().isdigit():
                return n.strip()
    except Exception:
        pass
    return None

def _name_via_api(bot, chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, int(user_id))
        u = member.user
        if getattr(u, "first_name", None) and getattr(u, "last_name", None):
            return f"{u.first_name} {u.last_name}"
        if getattr(u, "first_name", None):
            return u.first_name
        if getattr(u, "username", None):
            return "@" + u.username
    except Exception:
        pass
    return None

def _get_display_name(bot, chat_id, user_id, info):
    # 1) try name from file
    name = _safe_name_from_info(info)
    if name:
        return name
    # 2) try API
    api_name = _name_via_api(bot, chat_id, user_id)
    if api_name:
        return api_name
    # 3) fallback
    return f"User{user_id}"

# ------- извлечение значений (гибко) -------
def _extract_sisi(info: Any) -> int:
    # prefer keys: 'size', 'sisi', 'sisi_size'
    if not isinstance(info, dict):
        return 0
    for k in ("size", "sisi", "sisi_size"):
        v = info.get(k)
        if v is not None:
            try:
                return int(v)
            except Exception:
                pass
    # try nested numeric values
    return 0

def _extract_hui(info: Any) -> int:
    # prefer 'size', 'size_cm', 'hui', 'hui_size'
    if not isinstance(info, dict):
        return 0
    for k in ("size", "size_cm", "hui", "hui_size"):
        v = info.get(k)
        if v is not None:
            try:
                return int(v)
            except Exception:
                pass
    return 0

def _extract_klitor_mm(info: Any) -> float:
    # try 'size_mm', 'size', 'klitor', 'klitor_size' — treat result as mm if likely mm, else if small treat as mm too
    if not isinstance(info, dict):
        return 0.0
    for k in ("size_mm", "klitor_size", "klitor", "size"):
        v = info.get(k)
        if v is not None:
            try:
                # accept floats and ints
                return float(v)
            except Exception:
                pass
    return 0.0

# ------- Форматирование топа для одной игры -------
def _format_top_for_game(bot, chat_id, game, top_n=10) -> str:
    path = FILES.get(game)
    data = _load_json(path)
    cid = str(chat_id)

    if cid not in data or not isinstance(data[cid], dict) or len(data[cid]) == 0:
        return f"{EMOJI[game]} Топ по {game}: Тут ещё никто не играл 😢"

    rows = []
    for uid, info in data[cid].items():
        if game == "sisi":
            val = _extract_sisi(info)
        elif game == "hui":
            val = _extract_hui(info)
        else:  # klitor
            # store in mm internally; some files may store mm or units—user code must be consistent
            val = _extract_klitor_mm(info)
        rows.append((uid, info, val))

    # сортировка (desc)
    rows.sort(key=lambda x: x[2], reverse=True)

    # build text
    lines = [f"{EMOJI[game]} Топ по {game}:"]
    for i, (uid, info, val) in enumerate(rows[:top_n], start=1):
        name = _get_display_name(bot, chat_id, uid, info)
        if game == "sisi":
            lines.append(f"{i}. {name} — {int(val)} размер")
        elif game == "hui":
            lines.append(f"{i}. {name} — {int(val)} см")
        else:  # klitor: val is mm -> show cm with 1 decimal
            try:
                cm = float(val) / 10.0
                lines.append(f"{i}. {name} — {cm:.1f} см")
            except Exception:
                lines.append(f"{i}. {name} — {val} мм")
    return "\n".join(lines)

# ------- основная функция (отправляет 3 сообщения) -------
def handle(bot, message):
    chat_id = message.chat.id
    # send three separate messages
    for game in ("sisi", "hui", "klitor"):
        text = _format_top_for_game(bot, chat_id, game)
        try:
            bot.send_message(chat_id, text)
        except Exception:
            try:
                bot.reply_to(message, text)
            except Exception:
                pass

# ------- /my handler -------
def handle_my(bot, message):
    chat_id = str(message.chat.id)
    uid = str(message.from_user.id)
    parts = []

    # read each file and get values
    # sisi
    sdata = _load_json(FILES["sisi"])
    if chat_id in sdata and uid in sdata[chat_id]:
        info = sdata[chat_id][uid]
        name = _safe_name_from_info(info) or _name_via_api(bot, message.chat.id, uid)
        size = _extract_sisi(info)
        parts.append(f"🎀 Сиськи: {int(size)} размер")
    else:
        name = None
        parts.append("🎀 Сиськи: ещё не играл")

    # hui
    hdata = _load_json(FILES["hui"])
    if chat_id in hdata and uid in hdata[chat_id]:
        info = hdata[chat_id][uid]
        if not name:
            name = _safe_name_from_info(info) or _name_via_api(bot, message.chat.id, uid)
        size = _extract_hui(info)
        parts.append(f"🍌 Хуй: {int(size)} см")
    else:
        parts.append("🍌 Хуй: ещё не играл")

    # klitor
    kdata = _load_json(FILES["klitor"])
    if chat_id in kdata and uid in kdata[chat_id]:
        info = kdata[chat_id][uid]
        if not name:
            name = _safe_name_from_info(info) or _name_via_api(bot, message.chat.id, uid)
        mm = _extract_klitor_mm(info)
        parts.append(f"💎 Клитор: {mm/10.0:.1f} см")
    else:
        parts.append("💎 Клитор: ещё не играл")

    # fallback for display name
    if not name:
        try:
            member = bot.get_chat_member(int(message.chat.id), int(uid))
            u = member.user
            name = getattr(u, "first_name", None) or ("@" + getattr(u, "username", "")) or f"User{uid}"
        except Exception:
            name = f"User{uid}"

    out = f"👤 {name}\n\n" + "\n".join(parts)
    try:
        bot.send_message(message.chat.id, out)
    except Exception:
        bot.reply_to(message, out)