import time
import requests
import traceback
from core import load_plugins, load_users, save_users

TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_СВОЙ_ТОКЕН"
API = f"https://api.telegram.org/bot{TOKEN}"

ADMIN_USERNAME = "Sugar_Daddy_rip"

plugins = load_plugins()
users = load_users()


def send(chat_id, text):
    requests.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })


def handle_command(cmd, message):
    username = message["from"].get("username", "")
    chat_id = message["chat"]["id"]
    user_id = str(message["from"]["id"])

    if cmd.startswith("/price"):
        # доступ только админу
        if username != ADMIN_USERNAME:
            send(chat_id, "⛔ У тебя нет доступа")
            return

        parts = cmd.split()
        if len(parts) != 2:
            send(chat_id, "Использование: /price 10")
            return

        new_price = int(parts[1])

        users.setdefault("config", {})
        users["config"]["mute_price"] = new_price
        save_users(users)

        send(chat_id, f"💰 Цена за 1 минуту мута теперь: {new_price}")
        return

    # Отправляем команду плагинам
    for plugin in plugins.values():
        try:
            if plugin.handle(cmd, message, users):
                save_users(users)
                return
        except Exception:
            send(chat_id, "❌ Ошибка в плагине")
            traceback.print_exc()

    send(chat_id, "Неизвестная команда")


def longpoll():
    offset = 0
    print("Бот запущен")

    while True:
        try:
            r = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 50})
            data = r.json()

            if not data["ok"]:
                time.sleep(1)
                continue

            for upd in data["result"]:
                offset = upd["update_id"] + 1

                if "message" in upd:
                    text = upd["message"].get("text", "")
                    if text.startswith("/"):
                        handle_command(text.split()[0], upd["message"])

        except Exception as e:
            print("Ошибка:", e)
            time.sleep(3)


if __name__ == "__main__":
    longpoll()