import re

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config_data.config import load_config
from database.database_manager import Database
from lexicon.lexicon_ru import LEXICON_RU

config = load_config()
router = Router()
db = Database()
db.create_db()


class Board:
    def __init__(self, size):
        self.board = self.generate_board(size)
        self.size = size

    def __len__(self):
        return self.size

    def __iter__(self):
        yield from self.board

    def __getitem__(self, item):
        return self.board[item]

    def __setitem__(self, key, value):
        self.board[key] = value

    def __contains__(self, item):
        return item in self.board

    @staticmethod
    def generate_board(_size=3):
        _board: list[list[str]] = [['_'] * _size for _ in range(_size)]
        return _board


class XOGame:
    def __init__(self, board, win_row_size=3, turn='X', turns_number=9):
        self.xo_board = board
        self.win_row_size = win_row_size
        self.turn = turn
        self.turns_number = turns_number
        self.players = {'X': {"username": '_', "id": 0}, 'O': {"username": '_', "id": 0}}

    def set_game(self, size, win_row_size, turns_number):
        self.xo_board = Board(size)
        self.win_row_size = win_row_size
        self.turn = 'X'
        self.turns_number = turns_number

    def switch_turn(self):
        turns: dict[str, str] = {'X': 'O', 'O': 'X'}
        self.turn = turns.get(self.turn)

    def scan_row(self, _row):
        win: bool = False

        for i in range(len(_row)):
            _slice = _row[i: self.win_row_size + i]
            if _slice.count(self.turn) == self.win_row_size:
                win = True
                return win

        return win

    def check_epmty_cell(self, row, column, placeholder):
        is_cell_empty: bool = self.xo_board[row][column] == placeholder

        return is_cell_empty

    def check_winner(self):
        board_size: int = len(self.xo_board)
        number_of_diagonals: int = board_size * 2 - 1

        win: bool = False
        win_row: list[str] = []
        flag: bool = True

        diagonals_1 = [[] for _ in range(number_of_diagonals)]
        d_indexes_1 = [[] for _ in range(number_of_diagonals)]
        diagonals_2 = [[] for _ in range(number_of_diagonals)]
        d_indexes_2 = [[] for _ in range(number_of_diagonals)]

        for i, row in enumerate(self.xo_board):
            if not flag:
                break

            column = []
            vert_indexes = []

            win = self.scan_row(_row=row)

            if win:
                win_row = [f"{i}{j}" for j in range(board_size)]
                flag = False
                continue

            for j in range(board_size):
                column.append(self.xo_board[j][i])
                vert_indexes.append(f"{j}{i}")

            win = self.scan_row(_row=column)

            if win:
                win_row = vert_indexes
                break

        for i in range(-(board_size - 1), board_size):
            for j in range(board_size):
                row, col = j, i + j
                if 0 <= row < board_size and 0 <= col < len(self.xo_board[0]):
                    diagonals_1[i + board_size - 1].append(self.xo_board[row][col])
                    d_indexes_1[i + board_size - 1].append(f"{row}{col}")

                    diagonals_2[i + board_size - 1].append(self.xo_board[row][board_size - col - 1])
                    d_indexes_2[i + board_size - 1].append(f"{row}{board_size - col - 1}")

        for i in range(number_of_diagonals):
            main_diagonal_check = self.scan_row(_row=diagonals_1[i])
            secondary_diagonal_check = self.scan_row(_row=diagonals_2[i])

            if main_diagonal_check:
                indexes_q = d_indexes_1[i]
                win = True
                win_row = indexes_q
                break
            if secondary_diagonal_check:
                indexes_w = d_indexes_2[i]
                win = True
                win_row = indexes_w
                break

        return win, win_row


class XOKeyboard:
    def __init__(self, size, placeholder):
        self.placeholder = placeholder
        self.size = size
        self.keyboard = self.construct_keyboard(self.size)

    def __iter__(self):
        yield from self.keyboard

    def __getitem__(self, item):
        return self.keyboard[item]

    def __setitem__(self, key, value):
        self.keyboard[key] = value

    def __delitem__(self, key):
        del self.keyboard[key]

    def construct_keyboard(self, size):
        _keyboard = []
        for i in range(size):
            for j in range(size):
                _keyboard.extend([InlineKeyboardButton(text=self.placeholder, callback_data=f"{i}{j}")])
        self.keyboard = _keyboard
        return self.keyboard

    def update_keys(self, symbol, *args):
        buttons = list(*args)

        for key in buttons:
            self.keyboard[key].text = symbol


game = XOGame(board=Board(5), win_row_size=4)
xo_keyboard = XOKeyboard(size=5, placeholder='_')


@router.message(Command(commands="playxo"))
async def play_xo(message: Message):
    keyboard = [InlineKeyboardButton(text="3x3", callback_data="3"),
                InlineKeyboardButton(text="5x5", callback_data="5")]

    kb_1 = InlineKeyboardBuilder()

    kb_1.row(*keyboard, width=3)

    BOT_USERNAME: str = config.tg_bot.bot_username

    checks_1: str = "/playxo (@[A-z]([A-z0-9_]{4,31}))"
    checks_2: str = "/playxo" + BOT_USERNAME + " (@[A-z]([A-z0-9_]{4,31}))"

    is_valid_command_1: bool = bool(re.fullmatch(checks_1, message.text))
    is_valid_command_2: bool = bool(re.fullmatch(checks_2, message.text))

    message_content: list[str] = message.text.split()
    recipient: str = message_content[-1][1:]

    if is_valid_command_1 or is_valid_command_2:
        game.players['X']["username"] = message.from_user.username
        game.players['O']["username"] = recipient

        await message.answer(text=LEXICON_RU["xo_start_msg"])
        await message.answer(text="Выберите размер поля:", reply_markup=kb_1.as_markup())

    else:
        await message.answer(text=LEXICON_RU["game_start_hint"])


@router.message(Command(commands="stats"))
async def get_stats(message: Message):
    user_id: int = message.from_user.id
    res = [*db.get_user_stats(user_id)[0]]
    answer = f"Статистика игрока: {message.from_user.username}\nПобеды: {res[0]}\nПоражения: {res[1]}"
    await message.answer(answer)


@router.callback_query(F.data.in_(["3", "5"]))
async def set_the_xo_game(callback: CallbackQuery):
    field_size = int(callback.data)
    win_row_sizes: dict[int, int] = {3: 3, 5: 4}

    await callback.message.edit_text(
        f'''Вы выбрали крестики-нолики {field_size}x{field_size}.
 Для победы создайте ряд из {win_row_sizes[field_size]} символов''')

    game.set_game(field_size, win_row_sizes[field_size], field_size ** 2)

    xo_keyboard.construct_keyboard(field_size)

    kb_builder = InlineKeyboardBuilder()

    kb_builder.row(*xo_keyboard, width=game.xo_board.size)

    await callback.message.answer(
        text=f"{LEXICON_RU[game.turn]["win_highlight_symbol"]}  @{game.players[game.turn]["username"]}",
        reply_markup=kb_builder.as_markup())


@router.callback_query(F.data.in_([f"{i}{j}" for i in range(game.xo_board.size) for j in range(game.xo_board.size)]))
async def process_move(callback: CallbackQuery):
    win_list: list[bool, list[str]] = game.check_winner()
    win: bool = win_list[0]

    coords: str = callback.data
    keyboard_button_number: int = int(coords, base=game.xo_board.size)
    row: int = int(coords[0])
    column: int = int(coords[1])
    current_player: str = game.players[game.turn]["username"]
    user_is_valid: bool = current_player == callback.from_user.username

    user_id: int = callback.from_user.id
    db.add_user(user_id)

    if not win:
        if user_is_valid:
            kb_builder = InlineKeyboardBuilder()

            cell_is_empty: bool = game.check_epmty_cell(row=row, column=column, placeholder=xo_keyboard.placeholder)

            if cell_is_empty:
                game.xo_board[row][column] = game.turn
                xo_keyboard[keyboard_button_number] = InlineKeyboardButton(text=game.turn, callback_data=coords)

            kb_builder.row(*xo_keyboard, width=game.xo_board.size)

            win: bool = game.check_winner()[0]

            if not win and cell_is_empty:
                game.players[game.turn]["id"] = callback.from_user.id
                game.turns_number -= 1
                draw: bool = game.turns_number <= 0

                if draw:
                    await callback.message.edit_text(
                        text=LEXICON_RU["draw"],
                        reply_markup=kb_builder.as_markup())
                else:
                    try:
                        game.switch_turn()
                        await callback.message.edit_text(
                            text=f"{LEXICON_RU[game.turn]["win_highlight_symbol"]}  @{game.players[game.turn]["username"]}",
                            reply_markup=kb_builder.as_markup())
                    except TelegramRetryAfter:
                        ...

            elif not win and not cell_is_empty:
                await callback.answer(text=LEXICON_RU["occupied_cell_hint"])

                await callback.answer()
        else:
            await callback.answer(text=LEXICON_RU["forbidden_move_hint"])

    if win:
        winner: list[...] = [1, 0, 0, game.players[game.turn]["id"]]
        loser: list[...] = [0, 1, 0, game.players['O' if game.turn == 'X' else 'X']["id"]]
        db.update_user_stats(*winner)
        db.update_user_stats(*loser)

        win_list: list[bool, list[str]] = game.check_winner()

        keys_to_replace: list[int] = [key for key, button in enumerate(xo_keyboard.keyboard)
                                      if button.text == game.turn and button.callback_data in win_list[1]]

        xo_keyboard.update_keys(LEXICON_RU[game.turn]["win_highlight_symbol"], keys_to_replace)

        kb_builder = InlineKeyboardBuilder()

        kb_builder.row(*xo_keyboard, width=game.xo_board.size)

        await callback.answer()

        try:
            await callback.message.edit_text(
                text=f'''{LEXICON_RU["win_msg"]} {LEXICON_RU[game.turn]["win_highlight_symbol"]} @{game.players[game.turn]["username"]}''',
                reply_markup=kb_builder.as_markup())
        except TelegramBadRequest:
            ...
