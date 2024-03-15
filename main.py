import json
import random
import re
import sqlite3
from dataclasses import dataclass
from typing import Any

import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from requests import Response

from config_data.config import load_config
from lexicon.lexicon_ru import LEXICON_RU


config = load_config()


async def start_bot(message: Message) -> None:
    await message.answer(LEXICON_RU['/start'])


async def send_joke(message: Message) -> None:
    JOKES_API: str = config.apis.jokes_api
    r: "Response" = requests.get(JOKES_API)

    if r.status_code != 200:
        await message.answer(LEXICON_RU["send_joke_bad_request"])
        return
    joke: str = r.content.decode('cp1251')[12:-2]
    await message.answer(joke)


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
            await message.answer(LEXICON_RU["tenor_bad_request_msg"])
            return

        tenor_urls: tuple[Any, ...] = tuple(gif['url'] for gif in json.loads(r.content)['results'])
        gif_url: str = random.choice(tenor_urls)

        await message.answer(f"@{message.from_user.username} {LEXICON_RU[command]} {recipient}")
        await message.answer_animation(animation=gif_url)

    except UnboundLocalError:
        return


async def send_cat(message: Message) -> None:
    CATS_API: str = config.apis.cats_api
    cat_response: "Response" = requests.get(CATS_API)
    if cat_response.status_code != 200:
        await message.answer(LEXICON_RU["send_cat_bad_request"])
        return
    cat_link: str = cat_response.json()[0]['url']
    await message.answer_photo(photo=cat_link)


async def drink_tea(message: Message) -> None:
    tea_volume: float = round(random.uniform(0.2, 12.3), 2)
    await message.answer(f"🍵 @{message.from_user.username} выпил(а) {tea_volume} литра(ов) чая 🍵 ")


async def add_note(message: Message) -> None:
    con = sqlite3.connect(database=config.database.database_name)
    cur = con.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS notes
(group_chat_id int,
note_header varchar(50) PRIMARY KEY ,
note_content varchar(50)
)''')

    note: str = message.text
    note_checks: str = "(/addnote #)[А-яёЁA-z]([А-яёЁA-z0-9_ ]{,64}) [А-яЕёA-z]([А-яеЁA-z0-9_]{,256})"
    is_valid_string: bool = bool(re.fullmatch(note_checks, note))

    if is_valid_string:
        note: str = note.replace(' ', '+', 2)
        note_content: list[str] = note.split('+')
        note_header: str = note_content[1]
        note_text: str = note_content[2]
        current_group_id: int = message.chat.id

        try:
            cur.execute(
                f'''INSERT INTO notes (group_chat_id, note_header, note_content)
                VALUES ({current_group_id}, "{note_header}", "{note_text}")''')

            await message.answer(LEXICON_RU["succces_add_note_msg"])
            con.commit()
        except sqlite3.IntegrityError:
            await message.reply(LEXICON_RU["add_note_error_msg"])

        cur.close()
        con.close()

    else:
        await message.answer(LEXICON_RU["add_note_invalid_input"])


async def del_note(message: Message) -> None:
    con = sqlite3.connect(database=config.database.database_name)
    cur = con.cursor()

    message_content: list[str] = message.text.split()
    note_header = message_content[1]
    cur.execute(f'''DELETE FROM notes WHERE note_header = "{note_header}" ''')

    con.commit()
    cur.close()
    con.close()


async def get_note(message: Message) -> None:
    con = sqlite3.connect(database=config.database.database_name)
    cur = con.cursor()
    query = cur.execute(f"SELECT note_header, note_content FROM notes WHERE note_header = '{message.text}' ")
    result: list = list(query.fetchall())

    if bool(result):
        await message.reply(f"{result[0][0]} {result[0][1]}")

    cur.close()
    con.close()


async def get_word() -> dict[str, str | list]:
    words: list[str] = ["яблоко", "малина", "апельсин", "мандарин", "груша"]
    _word: str = random.choice(words)
    word_letters: dict[str, list[int]] = {key: [] for key in sorted(list(set(_word)))}
    word_placeholder: list[str] = list("_" * len(_word))
    for key in word_letters:
        for i, l in enumerate(_word):
            if l == key:
                word_letters[key] += [i]

    return {"word": _word, "word_letters": word_letters, "word_placeholder": list(word_placeholder)}


storage = MemoryStorage()


@dataclass
class Game(StatesGroup):
    word: str
    word_letters: str
    word_placeholder: list[str]
    attempts: int = 5
    user_input: "State" = State()


async def play_hanged_man(message: Message, state: FSMContext) -> None:
    await message.answer(LEXICON_RU["hanged_start_msg"])
    _word: dict[str, str | list] = await get_word()
    Game.word = _word["word"]
    Game.word_letters = _word["word_letters"]
    Game.word_placeholder = _word["word_placeholder"]

    await state.set_state(Game.user_input)


async def cancel_game(message: Message, state: FSMContext) -> None:
    await message.answer(LEXICON_RU["hanged_exit_game_msg"])
    await state.clear()


async def catch_answer(message: Message, state: FSMContext) -> None:
    letter: str = message.text

    if letter in Game.word:
        for i in Game.word_letters[letter]:
            Game.word_placeholder[i] = letter
            await message.answer(''.join(Game.word_placeholder))
    else:
        await message.answer(''.join(Game.word_placeholder))
        Game.attempts -= 1

    win_condition = "".join(Game.word_placeholder) == Game.word

    if win_condition:
        await message.answer(LEXICON_RU["hanged_win_msg"])
        await state.clear()
        return

    if Game.attempts <= 0:
        await message.answer(LEXICON_RU["hanged_lose_msg"])
        await state.clear()
        return
    await state.set_state(Game.user_input)


def main() -> None:
    BOT_TOKEN: str = config.tg_bot.token
    bot: "Bot" = Bot(token=BOT_TOKEN)
    dp: "Dispatcher" = Dispatcher(storage=storage)

    dp.message.register(start_bot, Command(commands=["help", "start"]))
    dp.message.register(send_joke, Command(commands=["anec"]))
    dp.message.register(make_interaction_with_user, Command(commands=["hug", "kiss", "slap"]))
    dp.message.register(send_cat, Command(commands=["cat"]))
    dp.message.register(drink_tea, Command(commands=["tea"]))
    dp.message.register(add_note, Command(commands=["addnote"]))
    dp.message.register(del_note, Command(commands=["delnote"]))
    dp.message.register(get_note, F.text.startswith('#'))

    dp.message.register(play_hanged_man, Command(commands=["playhanged"]))
    dp.message.register(cancel_game, Command(commands=["cancel"]), ~StateFilter(default_state))
    dp.message.register(catch_answer, ~StateFilter(default_state))

    dp.run_polling(bot)


if __name__ == "__main__":
    main()
