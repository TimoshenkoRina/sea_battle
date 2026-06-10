import random
from models import Stack, Queue, SortedCoordList, ShipBST

SIZE = 10
SHIPS = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

EMPTY = '.'
SHIP = 'S'
HIT = 'X'
MISS = 'O'


def make_board():
    """Создаёт пустое игровое поле SIZE x SIZE.
    возвращает: list[list[str]] - двумерный список символов
    """
    return [[EMPTY] * SIZE for _ in range(SIZE)]


def place_ships(board):
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
            cells = [
                (row, col + i) if horizontal else (row + i, col)
                for i in range(length)
            ]
            if can_place(board, cells):
                for r, c in cells:
                    board[r][c] = SHIP
                placed = True


def can_place(board, cells):
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


def all_ships_sunk(board):
    """Проверяет, все ли корабли потоплены.
    принимает: board - list[list[str]]
    возвращает: bool - True если ни одного SHIP не осталось
    """
    return all(cell != SHIP for row in board for cell in row)


def find_ship_cells(board, row, col):
    """Находит все клетки корабля, которому принадлежит указанная клетка.
    принимает: board - list[list[str]], row - int, col - int
    возвращает: list[(int, int)] - список координат клеток корабля
    """
    cells = [(row, col)]
    for r, c in cells:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                if board[nr][nc] == HIT and (nr, nc) not in cells:
                    cells.append((nr, nc))
    return cells


def is_ship_sunk(board, ship_cells):
    """Проверяет, полностью ли потоплен корабль.
    принимает: board - list[list[str]], ship_cells - list[(int, int)]
    возвращает: bool - True если рядом нет уцелевших клеток корабля
    """
    for r, c in ship_cells:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == SHIP:
                return False
    return True


def get_zone_around(ship_cells):
    """Возвращает клетки-зазор вокруг корабля (не занятые самим кораблём).
    принимает: ship_cells - list[(int, int)]
    возвращает: set[(int, int)] - множество клеток-зазора
    """
    ship_set = set(ship_cells)
    zone = set()
    for r, c in ship_cells:
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE and (nr, nc) not in ship_set:
                    zone.add((nr, nc))
    return zone


def get_sorted_ships_stats(ships_list):
    """Возвращает отсортированный по длине список кораблей для статистики.
    принимает: ships_list - list[int] - список длин кораблей
    возвращает: list[int] - отсортированный по убыванию список длин
    """
    return sorted(ships_list, reverse=True)


class Game:
    """Управляет всей логикой партии: поля, ходы, структуры данных."""

    def __init__(self):
        """Инициализирует поля и вспомогательные структуры."""
        self.player_board = None
        self.computer_board = None
        self.current_turn = 'player'
        self.history = Stack()
        self.computer_targets = Queue()
        # SortedCoordList для бинарного поиска живых клеток компьютера
        self.computer_coords = SortedCoordList(SIZE)
        # BST для быстрого поиска неподбитых клеток по строке
        self.computer_bst = ShipBST()
        self.shots = 0
        self.hits = 0
        self.player_shots = 0

    def setup(self):
        """Создаёт доски и случайно расставляет корабли для обоих участников.
        возвращает: None
        """
        self.player_board = make_board()
        self.computer_board = make_board()
        place_ships(self.player_board)
        place_ships(self.computer_board)
        self.current_turn = 'player'
        self.history = Stack()
        self.computer_targets = Queue()
        self.computer_coords = SortedCoordList(SIZE)
        self.computer_bst = ShipBST()
        self.shots = 0
        self.hits = 0
        self.player_shots = 0
        # заполняем структуры координатами кораблей компьютера
        for r in range(SIZE):
            for c in range(SIZE):
                if self.computer_board[r][c] == SHIP:
                    self.computer_coords.add(r, c)
                    self.computer_bst.insert(r, c)

    def player_shoot(self, row, col):
        """Выполняет выстрел игрока по полю компьютера.
        принимает: row - int, col - int
        возвращает: str - 'hit', 'sunk' или 'miss'
        """
        cell = self.computer_board[row][col]
        self.shots += 1
        self.player_shots += 1

        if cell == SHIP:
            self.computer_board[row][col] = HIT
            self.hits += 1
            # сохраняем ход в стек для возможной отмены
            self.history.push(('player', row, col, SHIP))
            # обновляем вспомогательные структуры
            self.computer_coords.remove(row, col)
            self.computer_bst.remove(row, col)
            ship_cells = find_ship_cells(self.computer_board, row, col)
            if is_ship_sunk(self.computer_board, ship_cells):
                return 'sunk'
            return 'hit'
        else:
            self.computer_board[row][col] = MISS
            self.history.push(('player', row, col, EMPTY))
            self._switch_turn()
            return 'miss'

    def undo_player_shot(self):
        """Отменяет последний ход игрока, восстанавливая состояние поля.
        возвращает: tuple (row, col) если отмена выполнена, иначе None
        """
        # ищем последний ход именно игрока
        temp = []
        result = None
        while not self.history.is_empty():
            entry = self.history.pop()
            who, row, col, old_val = entry
            if who == 'player':
                current = self.computer_board[row][col]
                self.computer_board[row][col] = old_val
                if old_val == SHIP:
                    # возвращаем клетку в структуры поиска
                    self.computer_coords.add(row, col)
                    self.computer_bst.insert(row, col)
                    self.hits -= 1
                self.shots -= 1
                self.player_shots -= 1
                result = (row, col, current)
                break
            else:
                temp.append(entry)
        # возвращаем временные записи обратно в стек
        for entry in reversed(temp):
            self.history.push(entry)
        return result

    def computer_random_shot(self):
        """Выбирает случайную необстрелянную клетку поля игрока.
        возвращает: (int, int) - кортеж (row, col)
        """
        while True:
            r = random.randint(0, SIZE - 1)
            c = random.randint(0, SIZE - 1)
            if self.player_board[r][c] not in (HIT, MISS):
                return r, c

    def computer_enqueue_neighbors(self, row, col):
        """Добавляет необстрелянных соседей клетки в очередь приоритетов.
        принимает: row - int, col - int
        возвращает: None
        """
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                if self.player_board[nr][nc] not in (HIT, MISS):
                    self.computer_targets.enqueue((nr, nc))

    def computer_shoot(self):
        """Выполняет ход компьютера: умный выбор цели или случайный.
        возвращает: tuple (row, col, result) где result - 'hit', 'sunk' или 'miss'
        """
        # выбираем цель из очереди или случайно
        if not self.computer_targets.is_empty():
            row, col = self.computer_targets.dequeue()
            while self.player_board[row][col] in (HIT, MISS):
                if self.computer_targets.is_empty():
                    row, col = self.computer_random_shot()
                    break
                row, col = self.computer_targets.dequeue()
        else:
            row, col = self.computer_random_shot()

        cell = self.player_board[row][col]
        self.shots += 1

        if cell == SHIP:
            self.player_board[row][col] = HIT
            self.history.push(('computer', row, col, SHIP))
            ship_cells = find_ship_cells(self.player_board, row, col)
            if is_ship_sunk(self.player_board, ship_cells):
                return row, col, 'sunk'
            # добавляем соседей в очередь для добивания
            self.computer_enqueue_neighbors(row, col)
            return row, col, 'hit'
        else:
            self.player_board[row][col] = MISS
            self.history.push(('computer', row, col, EMPTY))
            self._switch_turn()
            return row, col, 'miss'

    def get_accuracy(self):
        """Вычисляет точность игрока в процентах.
        возвращает: float - процент попаданий или 0.0 если выстрелов не было
        """
        if self.player_shots == 0:
            return 0.0
        return self.hits / self.player_shots * 100

    def _switch_turn(self):
        """Передаёт ход другому участнику.
        возвращает: None
        """
        if self.current_turn == 'player':
            self.current_turn = 'computer'
        else:
            self.current_turn = 'player'

    def is_finished(self):
        """Проверяет, закончилась ли игра.
        возвращает: bool - True если все корабли одной стороны потоплены
        """
        return all_ships_sunk(self.computer_board) or all_ships_sunk(self.player_board)
