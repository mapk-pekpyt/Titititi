import os
import importlib

def load_plugins(bot):
    plugin_dir = os.path.dirname(__file__)
    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and file != "__init__.py":
            modulename = file[:-3]
            module = importlib.import_module(f"plugins.{modulename}")
            if hasattr(module, "register"):
                module.register(bot)