import re

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config_data.config import load_config
from lexicon.lexicon_ru import LEXICON_RU

config = load_config()
storage = MemoryStorage()
router = Router()


class Board:
    def __init__(self, size):
        self.board = self.generate_board(size)
        self.size = size

    def __len__(self):
        return len(self.board)

    def __iter__(self):
        return iter(self.board)

    def __getitem__(self, item):
        return self.board[item]

    def __setitem__(self, key, value):
        self.board[key] = value

    def __contains__(self, item):
        return item in self.board

    @staticmethod
    def generate_board(_size=3):
        _board = [['_'] * _size for _ in range(_size)]
        return _board


class XOGame(StatesGroup):
    def __init__(self, board, win_row_size, state, turn, active=True):
        self.xo_board = board
        self.win_row_size = win_row_size
        self.turn = turn
        self.active = active
        self.players = {'X': '_', 'O': '_'}

        self.state = state

    def restart_game(self):
        self.xo_board = Board(self.xo_board.size)
        self.turn = 'X'
        self.active = True
        self.players = {'X': '_', 'O': '_'}

    def switch_turn(self):
        if self.turn == 'X':
            self.turn = 'O'
        else:
            self.turn = 'X'

    def scan_row(self, _row):
        win = False

        for i in range(len(_row)):
            _slice = _row[i: self.win_row_size + i]
            if _slice.count(self.turn) == self.win_row_size:
                win = True
                return win

        return win

    def check_epmty_cell(self, row, column, placeholder):
        is_cell_empty = self.xo_board[row][column] == placeholder

        return is_cell_empty

    def check_winner(self):
        board_size = len(self.xo_board)
        number_of_diagonals = board_size * 2 - 1

        win = False

        # Проверка горизонталей и вертикалей
        for i, row in enumerate(self.xo_board):
            vertical_row = []

            horizontal_check = self.scan_row(_row=row)

            if horizontal_check:
                win = True

            for j in range(board_size):
                vertical_row.append(self.xo_board[j][i])

            vertical_check = self.scan_row(_row=vertical_row)

            if vertical_check:
                win = True

        diagonals_1 = [[] for _ in range(number_of_diagonals)]
        diagonals_2 = [[] for _ in range(number_of_diagonals)]

        for i in range(-(board_size - 1), board_size):
            for j in range(board_size):
                row, col = j, i + j
                if 0 <= row < board_size and 0 <= col < len(self.xo_board[0]):
                    diagonals_1[i + board_size - 1].append(self.xo_board[row][col])
                    diagonals_2[i + board_size - 1].append(self.xo_board[row][board_size - col - 1])

        for i in range(number_of_diagonals):
            main_diagonal_check = self.scan_row(_row=diagonals_1[i])
            secondary_diagonal_check = self.scan_row(_row=diagonals_2[i])
            if main_diagonal_check or secondary_diagonal_check:
                win = True

        return win


class XOKeyboard:
    def __init__(self, placeholder, size):
        self.placeholder = placeholder
        self.size = size
        self.keyboard = self.construct_keyboard(self.size)

    def __iter__(self):
        return iter(self.keyboard)

    def __getitem__(self, item):
        return self.keyboard[item]

    def __setitem__(self, key, value):
        self.keyboard[key] = value

    def construct_keyboard(self, size):
        _keyboard = []
        for i in range(size):
            for j in range(size):
                _keyboard.extend([InlineKeyboardButton(text=self.placeholder, callback_data=f"{i}{j}")])
        return _keyboard


game = XOGame(board=Board(5), win_row_size=4, state=State(), turn="X")

xo_keyboard = XOKeyboard(placeholder='_', size=5)


@router.message(Command(commands="playxo"))
async def play_xo(message: Message):
    kb_builder = InlineKeyboardBuilder()
    xo_keyboard.keyboard = xo_keyboard.construct_keyboard(xo_keyboard.size)
    kb_builder.row(*xo_keyboard, width=len(game.xo_board))

    BOT_USERNAME: str = config.tg_bot.bot_username

    checks_1: str = "/playxo (@[A-z]([A-z0-9_]{4,31}))"
    checks_2: str = "/playxo" + BOT_USERNAME + " (@[A-z]([A-z0-9_]{4,31}))"

    is_valid_command_1: bool = bool(re.fullmatch(checks_1, message.text))
    is_valid_command_2: bool = bool(re.fullmatch(checks_2, message.text))

    message_content: list[str] = message.text.split()
    recipient: str = message_content[-1][1:]

    if is_valid_command_1 or is_valid_command_2:
        game.restart_game()
        game.players['X'] = message.from_user.username
        game.players['O'] = recipient

        await message.answer(LEXICON_RU["xo"]["xo_start_msg"])
        await message.answer(text=f"{LEXICON_RU["xo"][game.turn]["win_higlight_symbol"]}  @{game.players[game.turn]}",
                             reply_markup=kb_builder.as_markup())
    else:
        await message.answer(f'Для начала игры введите команду /playxo @[ник вашего соперника]')


@router.callback_query(F.data.in_["3", "5", "10"])
async def choose_field_size(callback: CallbackQuery):
    ...


@router.callback_query(F.data.in_([f"{i}{j}" for i in range(game.xo_board.size) for j in range(game.xo_board.size)]))
async def process_move(callback: CallbackQuery):
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(*xo_keyboard, width=len(game.xo_board))

    win = game.check_winner()

    coords = callback.data
    keyboard_button_number = int(coords, base=game.xo_board.size)
    row = int(coords[0])
    column = int(coords[1])

    if not win:
        kb_builder = InlineKeyboardBuilder()

        cell_is_empty = game.check_epmty_cell(row, column, xo_keyboard.placeholder)

        if cell_is_empty:
            game.xo_board[row][column] = game.turn
            xo_keyboard[keyboard_button_number] = InlineKeyboardButton(text=game.turn, callback_data=coords)

        kb_builder.row(*xo_keyboard, width=game.xo_board.size)

        win = game.check_winner()

        if not win and cell_is_empty:
            game.switch_turn()
            await callback.message.edit_text(
                text=f"{LEXICON_RU["xo"][game.turn]["win_higlight_symbol"]}  @{game.players[game.turn]}",
                reply_markup=kb_builder.as_markup())
        elif not win and not cell_is_empty:
            await callback.answer(text="Эта клетка занята!")
        else:
            await callback.answer()

    if win:
        # TODO: Добавить подсветку выигрышной комбинации

        await callback.answer("Игра окончена!")
        await callback.message.edit_text(
            text=f'''{LEXICON_RU["xo"]["win_msg"]} {LEXICON_RU["xo"][game.turn]["win_higlight_symbol"]} @{game.players[game.turn]}''',
            reply_markup=kb_builder.as_markup())
        xo_keyboard.keyboard = xo_keyboard.construct_keyboard(xo_keyboard.size)

        game.restart_game()

    await callback.answer()
