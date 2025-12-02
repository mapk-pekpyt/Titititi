# core.py
import os
import sqlite3
import datetime
import random

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "bot.db")

def db_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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

def today_date():
    return datetime.date.today().isoformat()

def random_delta(min_val=-10, max_val=10):
    return random.randint(min_val, max_val)

def init_db():
    # Игровые таблицы
    db_execute("""CREATE TABLE IF NOT EXISTS boobs (
        chat_id TEXT,
        user_id TEXT,
        size INTEGER DEFAULT 0,
        last_date TEXT,
        PRIMARY KEY(chat_id, user_id)
    )""")
    db_execute("""CREATE TABLE IF NOT EXISTS hui (
        chat_id TEXT,
        user_id TEXT,
        size INTEGER DEFAULT 0,
        last_date TEXT,
        PRIMARY KEY(chat_id, user_id)
    )""")
    db_execute("""CREATE TABLE IF NOT EXISTS klitor (
        chat_id TEXT,
        user_id TEXT,
        size INTEGER DEFAULT 0, -- mm
        last_date TEXT,
        PRIMARY KEY(chat_id, user_id)
    )""")

    # Баланс бота по чату (здесь храним звёзды, зачисленные на аккаунт бота в рамках чата/репозитория)
    db_execute("""CREATE TABLE IF NOT EXISTS bot_balance (
        chat_id TEXT PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )""")

    # Цена (храним в отдельной таблице)
    db_execute("""CREATE TABLE IF NOT EXISTS mute_price (
        id INTEGER PRIMARY KEY,
        price INTEGER
    )""")
    # если нет цены — установим 2
    row = db_execute("SELECT price FROM mute_price WHERE id=1", fetch=True)
    if not row:
        db_execute("INSERT INTO mute_price(id, price) VALUES (1, 2)")

    # Активные мьюты
    db_execute("""CREATE TABLE IF NOT EXISTS active_mutes (
        chat_id TEXT,
        user_identifier TEXT,
        end_time TEXT,
        PRIMARY KEY(chat_id, user_identifier)
    )""")

# helper for balance/price
def get_bot_balance(chat_id):
    row = db_execute("SELECT balance FROM bot_balance WHERE chat_id=?", (str(chat_id),), fetch=True)
    return int(row[0]['balance']) if row else 0

def set_bot_balance(chat_id, val):
    db_execute("INSERT OR REPLACE INTO bot_balance(chat_id,balance) VALUES (?,?)", (str(chat_id), int(val)))

def get_price():
    row = db_execute("SELECT price FROM mute_price WHERE id=1", fetch=True)
    return int(row[0]['price']) if row else 2

def set_price(new_price:int):
    db_execute("UPDATE mute_price SET price=? WHERE id=1", (int(new_price),))