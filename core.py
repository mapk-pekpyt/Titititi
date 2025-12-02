import sqlite3
import random
from datetime import datetime

DB_PATH = "data/bot.db"

def db_execute(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    if fetch:
        result = cur.fetchall()
        conn.close()
        return result
    conn.commit()
    conn.close()
    return None

def today_date():
    return datetime.now().strftime("%Y-%m-%d")

def random_delta(min_val=-10, max_val=10):
    return random.randint(min_val, max_val)