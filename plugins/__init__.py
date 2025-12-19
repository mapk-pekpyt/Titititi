# plugins/__init__.py

# ===========================
# Импорт всех плагинов
# ===========================
from . import sisi
from . import hui
from . import klitor
from . import mut
from . import top_plugin
from . import kto
from . import bust_price
from . import cannabis_game
from . import minus
from . import say
from . import beer
from . import cartel_war_game

# ===========================
# Словарь плагинов для main.py
# ===========================
PLUGINS = {
    "sisi": sisi,
    "hui": hui,
    "klitor": klitor,
    "mut": mut,
    "top_plugin": top_plugin,
    "kto": kto,
    "bust_price": bust_price,
    "cannabis_game": cannabis_game,
    "minus": minus,
    "say": say,
    "beer": beer,
    "cartel_war_game": cartel_war_game,
}