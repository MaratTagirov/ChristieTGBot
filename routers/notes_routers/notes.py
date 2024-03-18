import re
import sqlite3

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config_data.config import load_config
from lexicon.lexicon_ru import LEXICON_RU

config = load_config()
router = Router(name=__name__)


@router.message(Command(commands=["addnote"]))
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


@router.message(Command(commands=["delnote"]))
async def del_note(message: Message) -> None:
    con = sqlite3.connect(database=config.database.database_name)
    cur = con.cursor()

    message_content: list[str] = message.text.split()
    note_header = message_content[1]
    cur.execute(f'''DELETE FROM notes WHERE note_header = "{note_header}" ''')

    con.commit()
    cur.close()
    con.close()


@router.message(F.text.startswith('#'))
async def get_note(message: Message) -> None:
    con = sqlite3.connect(database=config.database.database_name)
    cur = con.cursor()
    query = cur.execute(f"SELECT note_header, note_content FROM notes WHERE note_header = '{message.text}' ")
    result: list = list(query.fetchall())

    if bool(result):
        await message.reply(f"{result[0][0]} {result[0][1]}")

    cur.close()
    con.close()
