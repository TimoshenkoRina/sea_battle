import random
from models import Stack, Queue

SIZE = 10
SHIPS = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]  # длины кораблей

EMPTY = '.'
SHIP = 'S'
HIT = 'X'
MISS = 'O'


def _make_board():
    """Создаёт пустое игровое поле SIZE x SIZE.
    возвращает: list[list[str]] - двумерный список символов
    """
    return [[EMPTY] * SIZE for _ in range(SIZE)]


def _place_ships(board):
    """Расставляет корабли на поле случайным образом.
    принимает: board - list[list[str]] - пустое поле
    возвращает: None (изменяет board на месте)
    """
    for length in SHIPS:
        placed = False
        while not placed:
            horizontal = random.choice([True, False])
            if horizontal:
                row = random.randint(0, SIZE - 1)
                col = random.randint(0, SIZE - length)
            else:
                row = random.randint(0, SIZE - length)
                col = random.randint(0, SIZE - 1)

            # проверяем, что все клетки и соседи свободны
            cells = [
                (row, col + i) if horizontal else (row + i, col)
                for i in range(length)
            ]
            if _can_place(board, cells):
                for r, c in cells:
                    board[r][c] = SHIP
                placed = True


def _can_place(board, cells):
    """Проверяет, можно ли поставить корабль в заданные клетки.
    принимает: board - list[list[str]], cells - list[(int, int)]
    возвращает: bool - True если место свободно с учётом зазора
    """
    for r, c in cells:
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE:
                    if board[nr][nc] == SHIP:
                        return False
    return True


def _print_board(board, hide_ships=False):
    """Выводит поле в консоль.
    принимает: board - list[list[str]],
               hide_ships - bool, скрыть ли символы кораблей (поле противника)
    возвращает: None
    """
    print('  ' + ' '.join(str(i + 1) for i in range(SIZE)))
    for i, row in enumerate(board):
        row_str = []
        for cell in row:
            if hide_ships and cell == SHIP:
                row_str.append(EMPTY)
            else:
                row_str.append(cell)
        print(f'{i + 1:2} ' + ' '.join(row_str))


def _all_ships_sunk(board):
    """Проверяет, все ли корабли потоплены.
    принимает: board - list[list[str]]
    возвращает: bool - True если ни одного SHIP не осталось
    """
    return all(cell != SHIP for row in board for cell in row)


class Game:
    """Управляет всей логикой партии: поля, ходы, проверка победы."""

    def __init__(self):
        """Инициализирует поля и вспомогательные структуры."""
        self.player_board = None
        self.computer_board = None
        self.current_turn = 'player'  # 'player' или 'computer'
        self.history = Stack()         # история ходов
        self.computer_targets = Queue()  # приоритетные цели компьютера
        self.shots = 0
        self.hits = 0

    def setup(self):
        """Создаёт доску и случайно расставляет корабли для обоих участников.
        возвращает: None
        """
        self.player_board = _make_board()
        self.computer_board = _make_board()
        _place_ships(self.player_board)
        _place_ships(self.computer_board)
        self.current_turn = 'player'
        self.history = Stack()
        self.computer_targets = Queue()
        self.shots = 0
        self.hits = 0

    def player_turn(self):
        """Полный ход игрока: показывает поле, принимает координаты и делает выстрел.
        возвращает: None
        """
        print('\nВаше поле:')
        _print_board(self.player_board)
        print('\nПоле противника:')
        _print_board(self.computer_board, hide_ships=True)

        while True:
            try:
                raw = input('Ваш выстрел (строка столбец, например: 3 5): ')
                row, col = map(int, raw.split())
                row -= 1
                col -= 1
                if not (0 <= row < SIZE and 0 <= col < SIZE):
                    print('Координаты вне поля, попробуйте снова.')
                    continue
                cell = self.computer_board[row][col]
                if cell in (HIT, MISS):
                    print('Вы уже стреляли сюда, выберите другую клетку.')
                    continue
                break
            except ValueError:
                print('Введите два числа через пробел.')

        self.shots += 1
        if cell == SHIP:
            self.computer_board[row][col] = HIT
            self.hits += 1
            print('Попадание!')
            self.history.push(('player', row, col, HIT))
        else:
            self.computer_board[row][col] = MISS
            print('Мимо.')
            self.history.push(('player', row, col, MISS))
            self._switch_turn()

    def computer_turn(self):
        """Полный ход компьютера: выбирает клетку (умно или случайно) и стреляет.
        возвращает: None
        """
        # берём приоритетную цель или случайную
        if not self.computer_targets.is_empty():
            row, col = self.computer_targets.dequeue()
            # пропускаем уже обстрелянные
            while self.player_board[row][col] in (HIT, MISS):
                if self.computer_targets.is_empty():
                    row, col = self._random_shot()
                    break
                row, col = self.computer_targets.dequeue()
        else:
            row, col = self._random_shot()

        cell = self.player_board[row][col]
        self.shots += 1
        print(f'Компьютер стреляет в {row + 1} {col + 1}.')

        if cell == SHIP:
            self.player_board[row][col] = HIT
            print('Компьютер попал!')
            self.history.push(('computer', row, col, HIT))
            # добавляем соседей в очередь приоритетов
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE:
                    if self.player_board[nr][nc] not in (HIT, MISS):
                        self.computer_targets.enqueue((nr, nc))
        else:
            self.player_board[row][col] = MISS
            print('Компьютер промахнулся.')
            self.history.push(('computer', row, col, MISS))
            self._switch_turn()

    def _random_shot(self):
        """Выбирает случайную ещё не обстрелянную клетку.
        возвращает: (int, int) - кортеж (row, col)
        """
        while True:
            r = random.randint(0, SIZE - 1)
            c = random.randint(0, SIZE - 1)
            if self.player_board[r][c] not in (HIT, MISS):
                return r, c

    def run(self):
        """Основной игровой цикл: чередует ходы до победы одной из сторон.
        возвращает: None
        """
        while not self._is_finished():
            if self.current_turn == 'player':
                self.player_turn()
            else:
                self.computer_turn()

        self.print_stats()
        if _all_ships_sunk(self.computer_board):
            print('Вы победили!')
        else:
            print('Компьютер победил. Попробуйте ещё раз!')

    def print_stats(self):
        """Собирает и выводит статистику партии.
        возвращает: None
        """
        accuracy = (self.hits / self.shots * 100) if self.shots > 0 else 0
        print(f'\n--- Статистика ---')
        print(f'Всего выстрелов: {self.shots}')
        print(f'Попаданий: {self.hits}')
        print(f'Точность: {accuracy:.1f}%')

    def _is_finished(self):
        """Проверяет, закончилась ли игра (все корабли одной стороны потоплены).
        возвращает: bool - True если игра окончена
        """
        return (
            _all_ships_sunk(self.computer_board)
            or _all_ships_sunk(self.player_board)
        )

    def _switch_turn(self):
        """Передаёт ход другому участнику.
        возвращает: None
        """
        if self.current_turn == 'player':
            self.current_turn = 'computer'
        else:
            self.current_turn = 'player'
