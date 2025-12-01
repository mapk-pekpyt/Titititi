import os
import sqlite3
import datetime
import random

DB = "bot.db"

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
    # Таблицы можно добавлять постепенно
    db_execute("""CREATE TABLE IF NOT EXISTS users (
        chat_id TEXT,
        user_id TEXT,
        PRIMARY KEY(chat_id,user_id)
    )""")

def random_delta(min_val=-10, max_val=10):
    return random.randint(min_val, max_val)

def today_date():
    return datetime.date.today().isoformat()