import sqlite3
import datetime
import random

DB = "data/bot.db"

def db_execute(query, params=(), fetch=False):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        result = c.fetchall()
    else:
        result = None
    conn.commit()
    conn.close()
    return result

def init_db():
    db_execute("""CREATE TABLE IF NOT EXISTS game_data (
        chat_id TEXT,
        user_id TEXT,
        game TEXT,
        value REAL,
        last_play TEXT,
        PRIMARY KEY(chat_id, user_id, game)
    )""")
    db_execute("""CREATE TABLE IF NOT EXISTS mut_settings (
        chat_id TEXT PRIMARY KEY,
        price_per_min INTEGER DEFAULT 2
    )""")
    db_execute("""CREATE TABLE IF NOT EXISTS stars_balance (
        user_id TEXT PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )""")

def today_date():
    return datetime.date.today().isoformat()

def random_delta(min_val, max_val):
    return random.randint(min_val, max_val)