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
class Config:
    tg_bot: TgBot
    database: DataBase


def load_config() -> Config:
    return Config(
        tg_bot=TgBot(
            token=os.getenv("BOT_TOKEN"),
            bot_username=os.getenv("BOT_USERNAME")
            ),
        database=DataBase(
            database_name="database.db"
            ),
    )
