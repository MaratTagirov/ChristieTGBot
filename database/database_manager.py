import sqlite3 as sq
from config_data.config import load_config

config = load_config()


class Database:

    @staticmethod
    def connect(sql_query):
        with sq.connect(config.database.database_name) as con:
            cur = con.cursor()
            cur.execute(sql_query)

            cur.close()

    @staticmethod
    @connect
    def create_db():
        query = '''CREATE TABLE IF NOT EXISTS users(
PRIMARY KEY user_id int)'''

    @staticmethod
    @connect
    def add_user():

        query = '''CREATE TABLE IF NOT EXISTS ? {}
FOREIGN KEY'''

    @staticmethod
    def get_user_stats():
        query = '''FROM users SELECT WHERE '''

        return query

    @staticmethod
    def get_top_10():
        query = '''FROM users SELECT WHERE '''

        return query


db = Database()

