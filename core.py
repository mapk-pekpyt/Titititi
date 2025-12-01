import json
import os
import importlib

DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.json"

os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)


def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_plugins():
    plugins = {}
    for file in os.listdir("plugins"):
        if file.endswith(".py") and file not in ["__init__.py"]:
            module_name = file[:-3]
            module = importlib.import_module(f"plugins.{module_name}")
            if hasattr(module, "register"):
                plugins[module_name] = module
    return plugins