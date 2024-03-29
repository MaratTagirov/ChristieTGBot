import functools
import random
import sqlite3 as sq

from config_data.config import load_config

config = load_config()


class Database:

    @staticmethod
    def connect(func):
        @functools.wraps(func)
        def wrapper(*args):
            with sq.connect(config.database.database_name) as con:
                cur = con.cursor()
                func_call = func(*args)

                if len(func_call) == 2:
                    query = func_call[0]
                    params = func_call[1]
                    call = cur.execute(query, [params])
                else:
                    call = cur.execute(func_call)

                cur.close()
                con.commit()
            return call
        return wrapper

    @staticmethod
    @connect
    def create_db():
        query = '''CREATE TABLE IF NOT EXISTS users(
                    user_id INTEGER NOT NULL PRIMARY KEY,
                    win INT NOT NULL,
                    lose INT NOT NULL,
                    draw INT NOT NULL)'''

        return query

    @staticmethod
    @connect
    def add_user(_user_id):
        query = '''INSERT INTO users (user_id, win, lose, draw)
                   VALUES (?, 0, 0, 0)'''
        user_id = _user_id

        return query, user_id

    @staticmethod
    def get_user_stats(_username):
        username = _username
        query = '''FROM users SELECT WHERE username = ?'''

        return query, username

    @staticmethod
    def get_top_10():
        query = '''FROM users SELECT WHERE '''

        return query


db = Database()
db.create_db()
