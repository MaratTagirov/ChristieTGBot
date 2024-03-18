import random
from dataclasses import dataclass

from aiogram import Bot, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from lexicon.lexicon_ru import LEXICON_RU
from routers.notes_routers.notes import config

bot = Bot(config.tg_bot.token)

router = Router(name=__name__)

storage = MemoryStorage()


async def get_word() -> dict[str, str | list]:
    words: list[str] = ["яблоко", "малина", "ананас", "груша", "виноград", "смородина", "арбуз"]
    _word: str = random.choice(words)
    word_letters: dict[str, list[int]] = {key: [] for key in sorted(list(set(_word)))}
    word_placeholder: list[str] = list("_" * len(_word))
    for key in word_letters:
        for i, l in enumerate(_word):
            if l == key:
                word_letters[key] += [i]

    return {"word": _word, "word_letters": word_letters, "word_placeholder": list(word_placeholder)}


@dataclass
class Game(StatesGroup):
    word: str
    word_letters: str
    word_placeholder: list[str]
    msg_id: int = 0
    attempts: int = 5
    user_input: "State" = State()


@router.message(Command(commands=["playhanged"]))
async def play_hanged_man(message: Message, state: FSMContext) -> None:
    _word: dict[str, str | list] = await get_word()
    Game.word = _word["word"]
    Game.word_letters = _word["word_letters"]
    Game.word_placeholder = _word["word_placeholder"]
    BOT_MESSAGE_DIFFERENCE: int = 2
    if Game.msg_id == 0:
        Game.msg_id = message.message_id + BOT_MESSAGE_DIFFERENCE
    await message.answer(f"{LEXICON_RU["hanged_start_msg"]}")
    await message.answer(f"{''.join(Game.word_placeholder)}")
    await state.set_state(Game.user_input)


@router.message(Command(commands=["exithanged"]), ~StateFilter(default_state))
async def cancel_game(message: Message, state: FSMContext) -> None:
    await message.answer(LEXICON_RU["hanged_exit_game_msg"])
    await state.clear()


@router.message(~StateFilter(default_state))
async def catch_answer(message: Message, state: FSMContext) -> None:
    letter: str = message.text

    if letter in Game.word:
        for i in Game.word_letters[letter]:
            Game.word_placeholder[i] = letter
        word = ''.join(Game.word_placeholder)
        await bot.edit_message_text(chat_id=message.chat.id, message_id=Game.msg_id, text=word)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    else:
        Game.attempts -= 1
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    win_condition = "".join(Game.word_placeholder) == Game.word

    if win_condition:
        await message.answer(LEXICON_RU["hanged_win_msg"])
        Game.msg_id = 0
        await state.clear()
        return

    if Game.attempts <= 0:
        await message.answer(LEXICON_RU["hanged_lose_msg"])
        Game.msg_id = 0
        await state.clear()
        return
    await state.set_state(Game.user_input)
