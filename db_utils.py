import sqlite3
from contextlib import contextmanager


@contextmanager
def db_ops():
    conn = sqlite3.connect('bot_database.db')
    try:
        cursor = conn.cursor()
        yield cursor
    except Exception as e:
        conn.rollback()
        raise e
    else:
        conn.commit()
    finally:
        conn.close()


def db_init():
    with db_ops() as cur:
        cur.execute('''
        CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        age INTEGER
        )
        ''')
