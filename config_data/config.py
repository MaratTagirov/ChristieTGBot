import os
from dataclasses import dataclass

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


@dataclass
class TgBot:
    token: str
    bot_username: str


@dataclass
class DataBase:
    database_name: str


@dataclass
class APIs:
    tenor: str
    cats_api: str
    jokes_api: str


@dataclass
class Config:
    tg_bot: TgBot
    database: DataBase
    apis: APIs


def load_config(path: str | None = None) -> Config:
    """Loads config data: TOKENS, API KEYS from your env variable"""

    return Config(
        tg_bot=TgBot(
            token=os.getenv("BOT_TOKEN"),
            bot_username=os.getenv("BOT_USERNAME")
            ),
        database=DataBase(
            database_name="database.db"
            ),
        apis=APIs(
            tenor=os.getenv("TENOR"),
            cats_api=os.getenv("CATS_API"),
            jokes_api=os.getenv("JOKES_API"),
            ),
        )
