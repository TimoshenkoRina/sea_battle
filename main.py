from game import Game


def print_welcome():
    """Выводит приветственное сообщение и правила игры."""
    print('=' * 40)
    print('       МОРСКОЙ БОЙ')
    print('=' * 40)
    print('Правила:')
    print('  - Поле 10x10, корабли расставлены случайно.')
    print('  - Вводите координаты: строка и столбец (1-10).')
    print('  - X — попадание, O — промах.')
    print('  - Побеждает тот, кто первым потопит все корабли.')
    print('=' * 40)


def main():
    """Точка входа: запускает игровой цикл, предлагает сыграть ещё раз."""
    print_welcome()

    while True:
        game = Game()
        game.setup()
        game.run()

        again = input('\nСыграть ещё раз? (да/нет): ').strip().lower()
        stop = again not in ('да', 'д', 'yes', 'y')
        if stop:
            break

    print('Спасибо за игру!')


if __name__ == '__main__':
    main()
