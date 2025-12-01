import sqlite3
import datetime
import random

DB = "boobs.db"

# === Работа с базой ===
def db_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def db_execute(query, params=(), fetch=False):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    data = cur.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data

# === Утилиты ===
def today_date():
    return datetime.date.today().isoformat()

def random_delta(min_val=-10, max_val=10):
    return random.randint(min_val, max_val)