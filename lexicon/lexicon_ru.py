LEXICON_RU: dict[str, str] = {
    "/start":
        '''Привет! Меня зовут Кристи!
        Вот, что я могу:
        /help - получить полный список команд
        /tea - попить чай
        /anec - получить случайный анекдот
        /hug /kiss /slap - взаимодействие с пользователем
        /addnote #note_name /delnote - добавить, прочитать, удалить заметку (в разработке)
        /playgame hanged - сыграть в игру "Виселица" ''',

    "/hug":
        '''обнял(а)''',
    "/kiss":
        '''поцеловал(а)''',
    "/slap":
        '''шлепнул(а)''',
    "send_cat_bad_request":
        '''Котиков седня не будет''',
    "send_joke_bad_request":
        '''Анекдота сегодня не будет''',
    "tenor_bad_request_msg":
        '''У миня лапки!''',

    "succces_add_note_msg":
        '''Заметка была успешно добавлена!''',
    "add_note_invalid_input":
        '''Ошибка добавления записи''',
    "add_note_error_msg":
        '''Заметка с данным номером уже существует.
Удалите текущую либо создайте заметку с другим номером''',

    "hanged_start_msg":
        '''Вы начали игру виселица. Для того чтобы прекратить игру введите команду  /exithanged''',
    "hanged_exit_game_msg":
        '''Вы вышли из игры. Чтобы начать новую игру введите команду /playhanged''',
    "hanged_win_msg":
        '''Вы победили!''',
    "hanged_lose_msg":
        '''Вы проиграли(((''',

    "xo": {
        "xo_start_msg":
            '''Вы начали игру в крестики-нолики. Для выхода игры введите команду /exitxo''',
        "xo_exit_msg":
            '''Вы вышли из игры. Для начала новой игры введите команду  /playxo'''
    },
}
