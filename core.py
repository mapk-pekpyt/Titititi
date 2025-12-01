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
    # Таблицы для будущих плагинов
    db_execute("""
    CREATE TABLE IF NOT EXISTS boobs (
        chat_id TEXT,
        user_id TEXT,
        size INTEGER,
        last_date TEXT,
        PRIMARY KEY(chat_id, user_id)
    )
    """)
    db_execute("""
    CREATE TABLE IF NOT EXISTS klitor (
        chat_id TEXT,
        user_id TEXT,
        size_mm INTEGER,
        last_date TEXT,
        PRIMARY KEY(chat_id, user_id)
    )
    """)
    db_execute("""
    CREATE TABLE IF NOT EXISTS hui (
        chat_id TEXT,
        user_id TEXT,
        size_cm INTEGER,
        last_date TEXT,
        PRIMARY KEY(chat_id, user_id)
    )
    """)

def change_size(table, chat_id, user_id, delta_range=(-10,10)):
    today = datetime.date.today().isoformat()
    chat, user = str(chat_id), str(user_id)
    row = db_execute(f"SELECT * FROM {table} WHERE chat_id=? AND user_id=?", (chat, user), fetch=True)
    if row:
        last = row[0]["last_date"]
        size_key = "size" if table=="boobs" else ("size_mm" if table=="klitor" else "size_cm")
        size = row[0][size_key]
    else:
        last = None
        size = 0
    if last == today:
        return 0, size
    delta = random.randint(delta_range[0], delta_range[1])
    if size + delta < 0:
        delta = -size
    new_size = size + delta
    size_key = "size" if table=="boobs" else ("size_mm" if table=="klitor" else "size_cm")
    db_execute(f"INSERT OR REPLACE INTO {table}(chat_id,user_id,{size_key},last_date) VALUES (?,?,?,?)",
               (chat, user, new_size, today))
    return delta, new_size