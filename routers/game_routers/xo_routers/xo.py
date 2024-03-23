from dataclasses import dataclass

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

storage = MemoryStorage()
router = Router()


def generate_board(_size=3):
    _board = [['_'] * _size for _ in range(_size)]

    return _board


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


size = 5
board = generate_board(5)
turn = "X"

buttons: list[InlineKeyboardButton] = []

for i in range(size):
    for j in range(size):
        buttons.extend([InlineKeyboardButton(text=f"_", callback_data=f"{i}{j}")])

kb_builder = InlineKeyboardBuilder()
kb = kb_builder.row(*buttons, width=size)


@router.message(Command(commands="playxo"))
async def play_xo(message: Message):
    await message.answer("Вы начали игру в крестики-нолики", reply_markup=kb_builder.as_markup())


@router.callback_query(F.data.in_([f"{i}{j}" for i in range(size) for j in range(size)]))
async def process_move(callback: CallbackQuery):
    global kb_builder, buttons, turn, board, size

    win_x = check_winner(board=board, scan_window_size=4, turn="X")
    win_o = check_winner(board=board, scan_window_size=4, turn="O")

    if win_x:
        await callback.message.answer("Победил крестик!")
        buttons = generate_board(5)
    if win_o:
        await callback.message.answer("Победил нолик!")
        buttons = generate_board(5)

    if turn == 'X':
        buttons[int(callback.data, base=size)] = InlineKeyboardButton(text="X", callback_data=callback.data)
        board[int(callback.data[0])][int(callback.data[1])] = 'X'
        turn = 'O'
    else:
        buttons[int(callback.data, base=size)] = InlineKeyboardButton(text="O", callback_data=callback.data)
        board[int(callback.data[0])][int(callback.data[1])] = 'O'
        turn = 'X'

    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(*buttons, width=size)
    print(*board, sep='\n')

    await callback.message.edit_text(text=f"Вы отметили поле {callback.data}", reply_markup=kb_builder.as_markup())
