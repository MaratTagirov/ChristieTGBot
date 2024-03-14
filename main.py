import json
import os
import random
import re
import sqlite3
from typing import Any

import dotenv
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from requests import Response

dotenv.load_dotenv(dotenv.find_dotenv())


async def start_bot(message: Message):
    BOT_NAME: str = os.getenv("BOT_NAME")
    await message.answer(fr'''
Привет! Меня зовут {BOT_NAME}!

Вот, что я могу:

/help - получить полный список команд
/cat - получить фото случайного котика
/tea - попить чай
/anec - получить случайный анекдот
/hug /kiss /slap - взаимодействие с пользователем
/addnote #note_name /delnote - добавить, прочитать, удалить заметку (в разработке)''')


async def send_joke(message: Message):
    JOKES_API: str = os.getenv("JOKES_API")
    r: "Response" = requests.get(JOKES_API)

    if r.status_code != 200:
        await message.answer("Анекдота сегодня не будет")
        return
    joke: str = r.content.decode('cp1251')[12:-2]
    await message.answer(joke)


async def make_interaction_with_user(message: Message):
    BOT_USERNAME: str = os.getenv("BOT_USERNAME")
    TENOR_API: str = os.getenv("TENOR")
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
            await message.answer("У миня лапки!")
            return

        tenor_urls: tuple[Any, ...] = tuple(gif['url'] for gif in json.loads(r.content)['results'])
        gif_url: str = random.choice(tenor_urls)
        command_text: dict[str, str] = {r"/hug": "обнял(а)", r"/kiss": "поцеловал(а)", r"/slap": "шлепнул(а)"}

        await message.answer(f"@{message.from_user.username} {command_text[command]} {recipient}")
        await message.answer_animation(animation=gif_url)

    except UnboundLocalError:
        return


async def send_cat(message: Message):
    CATS_API: str = os.getenv("CATS_API")
    cat_response: "Response" = requests.get(CATS_API)
    if cat_response.status_code != 200:
        await message.answer("Котиков седня не будет")
        return
    cat_link: str = cat_response.json()[0]['url']
    await message.answer_photo(photo=cat_link)


async def drink_tea(message: Message):
    tea_volume: float = round(random.uniform(0.2, 12.3), 2)
    await message.answer(f"🍵 @{message.from_user.username} выпил(а) {tea_volume} литра(ов) чая 🍵 ")


async def add_note(message: Message):
    con = sqlite3.connect(database="database.db")
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

            await message.answer("Заметка была успешно добавлена!")
            con.commit()
        except sqlite3.IntegrityError:
            await message.reply('''Заметка с данным номером уже существует.
Удалите текущую либо создайте заметку с другим номером''')

        cur.close()
        con.close()

    else:
        await message.answer("Оишбка!((((")


async def del_note(message: Message):
    con = sqlite3.connect(database="database.db")
    cur = con.cursor()

    message_content: list[str] = message.text.split()
    note_header = message_content[1]
    cur.execute(f'''DELETE FROM notes WHERE note_header = "{note_header}" ''')

    con.commit()
    cur.close()
    con.close()


async def get_note(message: Message):
    con = sqlite3.connect(database="database.db")
    cur = con.cursor()
    query = cur.execute(f"SELECT note_header, note_content FROM notes WHERE note_header = '{message.text}' ")
    result: list = list(query.fetchall())

    if bool(result):
        await message.reply(f"{result[0][0]} {result[0][1]}")

    cur.close()
    con.close()


def get_word() -> dict[str, str | list]:
    words: list[str] = ["президент", "инквизиция", "проституция", "расстрел",
                        "дифференцирование", "хайлайтер", "лоферы", "повербанк",
                        "куколд", "микроконтроллер", "доксинг", "константа"]
    _word: str = random.choice(words)
    word_letters = {key: [] for key in sorted(list(set(_word)))}
    word_placeholder: list[str] = list("_" * len(_word))
    for key in word_letters:
        for i, l in enumerate(_word):
            if l == key:
                word_letters[key] += [i]

    return {"word": _word, "word_letters": word_letters, "word_placeholder": list(word_placeholder)}


async def cancel_game(message: Message):
    global game
    if game["in_game"]:
        game["in_game"] = False
        await message.answer("Вы вышли из игры.")

word = get_word()


async def play_hanged_man(message: Message):
    global word
    global game
    if not game["in_game"]:
        game["in_game"] = True
        word = get_word()
        await message.answer(r"Вы начали игру виселица. Для того чтобы прекратить игру введите команду  /cancel")
    else:
        await message.answer(r"Игра уже начата. Завершите предыдущую игру, закончив раунд, либо введя комануд /cancel")

game = {"random_word": word["word"], "word_letters": word["word_letters"],
        "word_placeholder": word["word_placeholder"], "attempts": 5}
user = {"in_game": False, "total_games": 0, "wins": 0}

word = get_word()


async def catch_answer(message: Message):
    global game
    global user
    letter: str = message.text

    if ''.join(game["word_placeholder"]) == game["random_word"]:
        await message.answer("Вы победили!")
    if game["attempts"] <= 0:
        await message.answer("Вы проиграли(((")
    if letter in game["random_word"]:
        for i in game["word_letters"][letter]:
            game["word_placeholder"][i] = letter
            await message.answer(''.join(game["word_placeholder"]))
    else:
        await message.answer(''.join(["word_placeholder"]))
        game["attempts"] -= 1


def main():
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    bot: "Bot" = Bot(token=BOT_TOKEN)
    dp: "Dispatcher" = Dispatcher()

    dp.message.register(start_bot, Command(commands=["help", "start"]))

    dp.message.register(send_joke, Command(commands=["anec"]))

    dp.message.register(make_interaction_with_user, Command(commands=["hug", "kiss", "slap"]))

    dp.message.register(send_cat, Command(commands=["cat"]))

    dp.message.register(drink_tea, Command(commands=["tea"]))

    dp.message.register(add_note, Command(commands=["addnote"]))
    dp.message.register(del_note, Command(commands=["delnote"]))
    dp.message.register(get_note, F.text.startswith('#'))

    # dp.message.register(cancel_game, Command(commands=["cancel"]))
    # dp.message.register(play_hanged_man, Command(commands=["playhanged"]))
    # dp.message.register(catch_answer, F.is_alplha() & F.len() == 1)

    dp.run_polling(bot)


if __name__ == "__main__":
    main()
