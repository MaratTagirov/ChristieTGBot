from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lexicon.lexicon_ru import LEXICON_RU

storage = MemoryStorage()
router = Router()


def scan_row(_row, symbol, scan_window_size=3):
    win = False

    for i in range(len(_row)):
        _slice = _row[i: scan_window_size + i]
        if _slice.count(symbol) == scan_window_size:
            win = True
            return win

    return win


def check_winner(board, scan_window_size, turn):
    board_size = len(board)
    number_of_diagonals = board_size * 2 - 1

    win = False

    # Проверка горизонталей и вертикалей
    for i, row in enumerate(board):
        vertical_row = []

        horizontal_check = scan_row(_row=row, symbol=turn, scan_window_size=scan_window_size)

        if horizontal_check:
            win = True

        for j in range(len(row)):
            vertical_row.append(board[j][i])

        vertical_check = scan_row(_row=vertical_row, symbol=turn, scan_window_size=scan_window_size)

        if vertical_check:
            win = True

    diagonals_1 = [[] for _ in range(number_of_diagonals)]
    diagonals_2 = [[] for _ in range(number_of_diagonals)]

    for i in range(-(board_size - 1), board_size):
        for j in range(board_size):
            row, col = j, i + j
            if 0 <= row < len(board) and 0 <= col < len(board[0]):
                diagonals_1[i + board_size - 1].append(board[row][col])
                diagonals_2[i + board_size - 1].append(board[row][board_size - col - 1])

    for i in range(number_of_diagonals):
        main_diagonal_check = scan_row(_row=diagonals_1[i], symbol=turn, scan_window_size=scan_window_size)
        secondary_diagonal_check = scan_row(_row=diagonals_2[i], symbol=turn, scan_window_size=scan_window_size)
        if main_diagonal_check or secondary_diagonal_check:
            win = True

    return win


class Board:
    def __init__(self, size):
        self.board = self.generate_board(size)

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

buttons = XOKeyboard(placeholder='_', size=5)

kb_builder = InlineKeyboardBuilder()
kb = kb_builder.row(*buttons, width=len(game.xo_board))


@router.message(Command(commands="playxo"))
async def play_xo(message: Message):
    global kb_builder, buttons
    await message.answer(LEXICON_RU["xo"]["xo_start_msg"], reply_markup=kb_builder.as_markup())
    kb_builder = InlineKeyboardBuilder()
    buttons = XOKeyboard('_', 5)
    kb = kb_builder.row(*buttons, width=len(game.xo_board))
    game.active = True

@router.callback_query(F.data.in_([f"{i}{j}" for i in range(len(game.xo_board)) for j in range(len(game.xo_board))]))
async def process_move(callback: CallbackQuery):
    global kb_builder, buttons

    win_x = check_winner(board=game.xo_board, scan_window_size=game.win_row_size, turn="X")
    win_o = check_winner(board=game.xo_board, scan_window_size=game.win_row_size, turn="O")

    if game.turn == 'X':
        buttons[int(callback.data, base=len(game.xo_board))] = InlineKeyboardButton(text="X",
                                                                                    callback_data=callback.data)
        game.xo_board[int(callback.data[0])][int(callback.data[1])] = game.turn
    else:
        buttons[int(callback.data, base=len(game.xo_board))] = InlineKeyboardButton(text="O",
                                                                                    callback_data=callback.data)
        game.xo_board[int(callback.data[0])][int(callback.data[1])] = game.turn
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(*buttons, width=len(game.xo_board))

    game.switch_turn()

    if not (win_x or win_o) and game.active:
        await callback.message.edit_text(text=f"Ход {game.turn}", reply_markup=kb_builder.as_markup())

    if win_x or win_o:
        await callback.answer("Игра окончена!")
        await callback.message.edit_text(text=f"{LEXICON_RU["xo"][game.turn]}",
                                         reply_markup=kb_builder.as_markup())
        game.active = False
        kb_builder = InlineKeyboardBuilder()
        buttons = XOKeyboard('_', 5)

        game.xo_board = Board(5)
