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


def db_init(chat_id):
    with db_ops() as cur:
        cur.execute(f'''
        CREATE TABLE IF NOT EXISTS chat{str(chat_id)[1:]} (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        real_name TEXT NOT NULL, 
        nickname TEXT,
        is_admin BOOLEAN NOT NULL,
        UNIQUE(username, user_id)
        )
        ''')
