# core.py
import sqlite3
import datetime
import random
import os

# База будет в рабочем каталоге (BotHost использует /app)
DB = os.path.join(os.path.dirname(__file__), "bot.db")

def db_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
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
    # Таблицы для игр
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
        size INTEGER DEFAULT 0, -- хранится в мм
        last_date TEXT,
        PRIMARY KEY(chat_id, user_id)
    )""")

    # Общая таблица для удобства топов/игр (не обязательна, но оставлю)
    db_execute("""CREATE TABLE IF NOT EXISTS game_stats (
        chat_id TEXT,
        user_id TEXT,
        game TEXT,
        value REAL DEFAULT 0,
        last_play TEXT,
        PRIMARY KEY(chat_id, user_id, game)
    )""")

    # Баланс бота по чату (тут будут отражаться звезды, которые уже зачислены на счёт бота)
    db_execute("""CREATE TABLE IF NOT EXISTS bot_balance (
        chat_id TEXT PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )""")

    # Таблица активных мутов (храним по username или user_id)
    db_execute("""CREATE TABLE IF NOT EXISTS active_mutes (
        chat_id TEXT,
        user_identifier TEXT,
        end_time TEXT,
        PRIMARY KEY(chat_id, user_identifier)
    )""")