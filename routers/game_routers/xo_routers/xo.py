from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lexicon.lexicon_ru import LEXICON_RU

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

        self.state = state

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

    game.active = True

    await message.answer(LEXICON_RU["xo"]["xo_start_msg"], reply_markup=kb_builder.as_markup())


@router.callback_query(F.data.in_([f"{i}{j}" for i in range(game.xo_board.size) for j in range(game.xo_board.size)]))
async def process_move(callback: CallbackQuery):
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(*xo_keyboard, width=len(game.xo_board))

    win = game.check_winner()

    coords = callback.data
    keyboard_button_number = int(coords, base=game.xo_board.size)
    row = int(coords[0])
    column = int(coords[1])

    if not win and game.active:
        kb_builder = InlineKeyboardBuilder()
        xo_keyboard[keyboard_button_number] = InlineKeyboardButton(text=game.turn, callback_data=coords)

        game.xo_board[row][column] = game.turn

        kb_builder.row(*xo_keyboard, width=game.xo_board.size)

        win = game.check_winner()

        game.switch_turn()

        if not win:
            await callback.message.edit_text(text=f"Ход {game.turn}", reply_markup=kb_builder.as_markup())

    if win:
        game.switch_turn()

        await callback.answer("Игра окончена!")
        await callback.message.edit_text(text=f"{LEXICON_RU["xo"][game.turn]}",
                                         reply_markup=kb_builder.as_markup())
        game.active = False
        xo_keyboard.keyboard = xo_keyboard.construct_keyboard(xo_keyboard.size)

        game.xo_board = Board(5)

    await callback.answer()


