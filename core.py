import sqlite3
import datetime
import random

DB = "bot.db"  # Имя базы, можно менять

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

def init_db():
    queries = [
        "CREATE TABLE IF NOT EXISTS boobs(chat_id TEXT, user_id TEXT, size INTEGER, last_date TEXT, PRIMARY KEY(chat_id, user_id))",
        "CREATE TABLE IF NOT EXISTS hui(chat_id TEXT, user_id TEXT, size INTEGER, last_date TEXT, PRIMARY KEY(chat_id, user_id))",
        "CREATE TABLE IF NOT EXISTS klitor(chat_id TEXT, user_id TEXT, size INTEGER, last_date TEXT, PRIMARY KEY(chat_id, user_id))"
    ]
    for q in queries:
        db_execute(q)

# === Утилиты ===
def today_date():
    return datetime.date.today().isoformat()

def random_delta(min_val=-10, max_val=10):
    return random.randint(min_val, max_val)