from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config_data.config import load_config
from lexicon.lexicon_ru import LEXICON_RU

router = Router(name=__name__)
config = load_config()


@router.message(Command(commands=["start", "help"]))
async def start_bot(message: Message) -> None:

    await message.answer(text=LEXICON_RU["/start"])
