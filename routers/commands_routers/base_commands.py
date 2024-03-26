import json
import random
import re
from typing import Any

import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from requests import Response

from config_data.config import load_config
from lexicon.lexicon_ru import LEXICON_RU

router = Router(name=__name__)
config = load_config()


@router.message(Command(commands=["start", "help"]))
async def start_bot(message: Message) -> None:
    await message.answer(LEXICON_RU['/start'])


@router.message(Command(commands=["anec"]))
async def send_joke(message: Message) -> None:
    JOKES_API: str = config.apis.jokes_api
    r: "Response" = requests.get(JOKES_API)

    if r.status_code != 200:
        await message.answer(text=LEXICON_RU["send_joke_bad_request"])
        return
    joke: str = r.content.decode('cp1251')[12:-2]
    await message.answer(joke)


@router.message(Command(commands=["cat"]))
async def send_cat(message: Message) -> None:
    CATS_API: str = config.apis.cats_api
    cat_response: "Response" = requests.get(CATS_API)
    if cat_response.status_code != 200:
        await message.answer(text=LEXICON_RU["send_cat_bad_request"])
        return
    cat_link: str = cat_response.json()[0]['url']
    await message.answer_photo(photo=cat_link)


@router.message(Command(commands=["tea"]))
async def drink_tea(message: Message) -> None:
    tea_volume: float = round(random.uniform(0.2, 12.3), 2)
    await message.answer(text=f"🍵 @{message.from_user.username} выпил(а) {tea_volume} литра(ов) чая 🍵 ")


@router.message(Command(commands=["hug", "kiss", "slap"]))
async def make_interaction_with_user(message: Message) -> None:
    BOT_USERNAME: str = config.tg_bot.bot_username
    TENOR_API: str = config.apis.tenor
    lmt: int = 20

    checks_1: str = "((/hug)|(/kiss)|(/slap)) (@[A-z]([A-z0-9_]{4,31}))"
    checks_2: str = "((/hug)|(/kiss)|(/slap))" + BOT_USERNAME + " (@[A-z]([A-z0-9_]{4,31}))"
    is_valid_command_1: bool = bool(re.fullmatch(checks_1, message.text))
    is_valid_command_2: bool = bool(re.fullmatch(checks_2, message.text))

    message_content: list[str] = message.text.split()
    recipient: str = message_content[-1]

    try:
        if is_valid_command_1:
            command: str = message_content[0]
            search_term: str = command[1:]
        elif is_valid_command_2:
            command: str = message_content[0].split('@')[0]
            search_term: str = message_content[0].split('@')[0][1:]
        else:
            return

        r: "Response" = requests.get(
            f"https://tenor.googleapis.com/v2/search?q={search_term + "anime"}&key={TENOR_API}&limit={lmt}")

        if r.status_code != 200:
            await message.answer(text=LEXICON_RU["tenor_bad_request_msg"])
            return

        tenor_urls: tuple[Any, ...] = tuple(gif['url'] for gif in json.loads(r.content)['results'])
        gif_url: str = random.choice(tenor_urls)

        await message.answer(text=f"@{message.from_user.username} {LEXICON_RU[command]} {recipient}")
        await message.answer_animation(animation=gif_url)

    except UnboundLocalError:
        return
