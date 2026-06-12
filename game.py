import random
from models import Stack, Queue, SortedCoordList, ShipBST

SIZE = 10
SHIPS = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

EMPTY = '.'
SHIP = 'S'
HIT = 'X'
MISS = 'O'

def make_board():
    """Создаёт пустое игровое поле.
    принимает: нет
    возвращает: list[list[str]] - двумерный список размера SIZE x SIZE
    """
    return [[EMPTY] * SIZE for _ in range(SIZE)]  #создаём список из 10 строк, каждая по 10 пустых клеток

def can_place(board, cells):
    """Проверяет, можно ли поставить корабль в клетки с учётом зазора.
    принимает: board - list[list[str]] - поле, cells - list[tuple[int, int]] - клетки корабля
    возвращает: bool - True если корабль можно поставить
    """
    for r, c in cells:  #перебираем каждую клетку будущего корабля
        for dr in range(-1, 2):  #смещаемся по строке и столбцу
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc  #координаты соседней клетки
                if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == SHIP:  #если сосед в пределах поля и уже занят
                    return False
    return True

def place_ships(board):
    """Случайно расставляет все корабли на поле.
    принимает: board - list[list[str]] - поле для расстановки
    возвращает: None - изменяет поле на месте
    """
    for length in SHIPS:  #перебираем длины кораблей по очереди
        placed = False

        while not placed:  #пока не найдём подходящее место, случайно выбираем ориентацию корабля
            horizontal = random.choice([True, False])

            if horizontal:  #для горизонтального корабля выбираем любую строку, а для столбца делаем запас
                row = random.randint(0, SIZE - 1)
                col = random.randint(0, SIZE - length)
            else:  #для вертикальныого корабля наоборот
                row = random.randint(0, SIZE - length)
                col = random.randint(0, SIZE - 1)

            cells = [
                (row, col + i) if horizontal else (row + i, col)  #для горизонтали смещаем столбец, для вертикали смещаем строку
                for i in range(length)
            ]

            if can_place(board, cells):  #проверяем, не нарушается ли зазор и не перекрывается ли другой корабль
                for r, c in cells:
                    board[r][c] = SHIP
                placed = True  #в случае успеха выходим из while

def all_ships_sunk(board):
    """Проверяет, потоплены ли все корабли на поле.
    принимает: board - list[list[str]] - игровое поле
    возвращает: bool - True если живых клеток кораблей не осталось
    """
    return all(cell != SHIP for row in board for cell in row)  #если ни одной клетки SHIP не осталось, то возвращает true

def find_ship_cells(board, row, col):
    """Находит все клетки одного корабля по подбитой клетке.
    принимает: board - list[list[str]] - поле, row - int - строка, col - int - столбец
    возвращает: list[tuple[int, int]] - список клеток найденного корабля
    """
    stack = [(row, col)]  #стек для поиска корабля, начиная с подбитой клетки
    visited = set()
    cells = []

    while stack:  #пока есть клетки для проверки, берём следующую клетку из стека
        r, c = stack.pop()

        if (r, c) in visited:  #пропускаем, если уже проверяли эту клетку
            continue

        visited.add((r, c))

        if board[r][c] not in (HIT, SHIP):  #пропускаем, если клетка не является частью корабля
            continue

        cells.append((r, c))  #если клетка часть корабля, добавляем в результат

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  #смотрим координаты соседней клетки по четырём направлениям
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE and (nr, nc) not in visited:  #если сосед в пределах поля и не проверен
                if board[nr][nc] in (HIT, SHIP):  #и если сосед тоже часть корабля, то добавляем его в стек для проверки
                    stack.append((nr, nc))

    return cells  #в конце возвращаем все найденные клетки корабля

def get_zone_around(ship_cells):
    """Возвращает клетки вокруг потопленного корабля.
    принимает: ship_cells - list[tuple[int, int]] - клетки корабля
    возвращает: set[tuple[int, int]] - множество клеток вокруг корабля
    """
    ship_set = set(ship_cells)  #задаём множество клеток корабля
    zone = set()

    for r, c in ship_cells:  #перебираем каждую клетку и смещаемся по строке и по столбцу
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc  #координаты потенциальной клетки зазора
                if 0 <= nr < SIZE and 0 <= nc < SIZE and (nr, nc) not in ship_set:  #если клетка в пределах поля и не сам корабль, то добавляем клетку в зазор
                    zone.add((nr, nc))

    return zone

def _process_hit(board, row, col):
    """Определяет клетки корабля и факт его потопления после попадания.
    принимает: board - list[list[str]] - поле, row - int - строка, col - int - столбец
    возвращает: tuple[list[tuple[int, int]], bool] - клетки корабля и флаг потопления
    """
    ship_cells = find_ship_cells(board, row, col)  #находим все клетки корабля, в который попали, и если среди клеток корабля не осталось живых
    sunk = all(board[r][c] != SHIP for r, c in ship_cells)
    return ship_cells, sunk  #возвращаем клетки и флаг

def _get_hunt_targets(board, hit_cells):
    """Вычисляет приоритетные цели для добивания корабля.
    принимает: board - list[list[str]] - поле игрока, hit_cells - list[tuple[int, int]] - подбитые клетки
    возвращает: list[tuple[int, int]] - список целей в порядке приоритета
    """
    if len(hit_cells) >= 2:  #если известны минимум две подбитые клетки, то можно определить направление корабля
        rows = [r for r, _ in hit_cells]  #список строк подбитых клеток
        cols = [c for _, c in hit_cells]  #список столбцов подбитых клеток

        if len(set(rows)) == 1:  #если все подбитые клетки в одной строке, то корабль горизонтальный
            row = rows[0]  #задаём строку и крайние подбитые столбцы
            min_col = min(cols)
            max_col = max(cols)
            targets = []

            if max_col + 1 < SIZE and board[row][max_col + 1] not in (HIT, MISS):  #если клетка справа существует и не обстреляна
                targets.append((row, max_col + 1))
            if min_col - 1 >= 0 and board[row][min_col - 1] not in (HIT, MISS):  #если клетка слева существует и не обстреляна
                targets.append((row, min_col - 1))

            return targets  #возвращаем цели по краям

        if len(set(cols)) == 1:  #если все подбитые клетки в одном столбце, то корабль вертикальный
            col = cols[0]  #задаём столбец и крайние подбитые строки
            min_row = min(rows)
            max_row = max(rows)
            targets = []

            if max_row + 1 < SIZE and board[max_row + 1][col] not in (HIT, MISS):  #если клетка снизу существует и не обстреляна
                targets.append((max_row + 1, col))
            if min_row - 1 >= 0 and board[min_row - 1][col] not in (HIT, MISS):  #если клетка сверху существует и не обстреляна
                targets.append((min_row - 1, col))

            return targets  #возвращаем цели по краям

    r0, c0 = hit_cells[0]  #если только одна подбитая клетка, то направление неизвестно
    targets = []

    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  #берём четыре направления и координаты соседней клетки
        nr, nc = r0 + dr, c0 + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] not in (HIT, MISS):  #если сосед в пределах поля и не обстрелян, то добавляем как потенциальную цель
            targets.append((nr, nc))

    return targets  #возвращаем всех четырёх соседей как цели

# Никитка
class PlacementController:
    """Логика ручной расстановки кораблей без привязки к интерфейсу."""

    def __init__(self):
        """Создаёт контроллер ручной расстановки."""
        self.board = make_board()  #пустое поле, на котором будем расставлять корабли
        self.ship_index = 0
        self.horizontal = True
        self.ships = list(SHIPS)  #копируем список длин кораблей, чтобы не менять глобальный SHIPS

    def toggle_orientation(self):
        """Меняет ориентацию текущего корабля."""
        self.horizontal = not self.horizontal  #переключаем значения true/false(горизонтально/вертикально)

    def get_next_ship_length(self):
        """Возвращает длину следующего корабля."""
        if self.ship_index >= len(self.ships):  #если все корабли уже расставлены, возвращаем None
            return None
        return self.ships[self.ship_index]  #иначе возвращаем длину следующего ещё не поставленного корабля

    def is_finished(self):
        """Проверяет, завершена ли ручная расстановка."""
        return self.ship_index >= len(self.ships)  #возвращает true если индекс вышел за пределы списка кораблей

    def get_ship_cells(self, row, col):
        """Возвращает клетки текущего корабля по стартовой позиции.
        принимает: row - int - строка, col - int - столбец
        возвращает: list[tuple[int, int]] - список клеток или пустой список
        """
        if self.is_finished():  #проверка, если расстановка уже завершена
            return []

        length = self.ships[self.ship_index]
        cells = []  #список клеток, которые займёт корабль

        for i in range(length):  #перебираем каждую часть корабля
            r = row if self.horizontal else row + i  #при горизонтали не меняем строку, а при вертикали смещаемся вниз
            c = col + i if self.horizontal else col  #при горизонтали смещаемся вправо, при вертикали не меняем

            if not (0 <= r < SIZE and 0 <= c < SIZE):  #если клетка выходит за границы поля
                return []

            cells.append((r, c))  #добавляем допустимую клетку в список

        return cells  #возвращаем все клетки корабля

    def place_ship(self, row, col):
        """Пытается поставить очередной корабль.
        принимает: row - int - строка, col - int - столбец
        возвращает: list[tuple[int, int]] - клетки поставленного корабля или пустой список
        """
        cells = self.get_ship_cells(row, col)  #вычисляем клетки корабля по позиции и ориентации

        if not cells or not can_place(self.board, cells):
            return []

        for r, c in cells:  #перебираем все клетки и отмечаем занятые
            self.board[r][c] = SHIP

        self.ship_index += 1
        return cells  #возвращаем клетки успешно поставленного корабля

# Миша
class Game:
    """Основная логика игры и работы компьютера."""

    def __init__(self):
        """Создаёт объект игры и инициализирует все атрибуты."""
        self.player_board = None
        self.computer_board = None
        self.current_turn = 'player'
        self.history = Stack()
        self.computer_targets = Queue()
        self._hunt_hits = []
        self.computer_coords = SortedCoordList(SIZE)
        self.computer_bst = ShipBST()
        self.shots = 0
        self.hits = 0
        self.player_shots = 0
        self.enemy_sunk_ships = []
        self.player_sunk_ships = []

    def setup(self, player_board=None):
        """Инициализирует игру. Если player_board не передан — расставляет корабли случайно.
        принимает: player_board - list[list[str]] | None - готовое поле игрока
        возвращает: None
        """
        if player_board is not None:
            self.player_board = [row[:] for row in player_board]
        else:
            self.player_board = make_board()
            place_ships(self.player_board)

        self.computer_board = make_board()
        place_ships(self.computer_board)

        self.current_turn = 'player'
        self.history = Stack()
        self.computer_targets = Queue()
        self._hunt_hits = []
        self.computer_coords = SortedCoordList(SIZE)
        self.computer_bst = ShipBST()
        self.shots = 0
        self.hits = 0
        self.player_shots = 0
        self.enemy_sunk_ships = []
        self.player_sunk_ships = []

        for r in range(SIZE):
            for c in range(SIZE):
                if self.computer_board[r][c] == SHIP:
                    self.computer_coords.add(r, c)
                    self.computer_bst.insert(r, c)

    def get_remaining_enemy_ships(self):
        """Возвращает список оставшихся кораблей противника.
        принимает: нет
        возвращает: list[int] - длины живых кораблей по убыванию
        """
        remaining = list(SHIPS)

        for length in self.enemy_sunk_ships:
            if length in remaining:
                remaining.remove(length)

        return sorted(remaining, reverse=True)

    def player_shoot(self, row, col):
        """Выполняет выстрел игрока по полю компьютера.
        принимает: row - int - строка, col - int - столбец
        возвращает: dict - результат выстрела и служебные данные
        """
        cell = self.computer_board[row][col]
        self.shots += 1
        self.player_shots += 1

        result = {
            'result': 'miss',
            'ship_cells': [],
            'zone': set(),
            'game_over': False,
        }

        if cell == SHIP:
            self.computer_board[row][col] = HIT
            self.hits += 1
            self.history.push(('player', row, col, SHIP, None))
            self.computer_coords.remove(row, col)
            self.computer_bst.remove(row, col)

            ship_cells, sunk = _process_hit(self.computer_board, row, col)
            result['ship_cells'] = ship_cells

            if sunk:
                length = len(ship_cells)
                zone = get_zone_around(ship_cells)
                self.enemy_sunk_ships.append(length)
                self.history.push(('player_sunk', row, col, None, length))
                result['result'] = 'sunk'
                result['zone'] = zone
            else:
                result['result'] = 'hit'

            result['game_over'] = all_ships_sunk(self.computer_board)
            return result

        self.computer_board[row][col] = MISS
        self.history.push(('player', row, col, EMPTY, None))
        self._switch_turn()
        return result

    def undo_player_shot(self):
        """Отменяет последний ход игрока.
        принимает: нет
        возвращает: tuple[int, int, str] | None - координаты и состояние клетки до отмены
        """
        temp = []
        result = None
        rollback_sunk_length = None

        while not self.history.is_empty():
            entry = self.history.pop()
            tag, row, col, old_val, extra = entry

            if tag == 'player_sunk':
                rollback_sunk_length = extra
                continue

            if tag == 'player':
                current = self.computer_board[row][col]
                self.computer_board[row][col] = old_val

                if old_val == SHIP:
                    self.computer_coords.add(row, col)
                    self.computer_bst.insert(row, col)
                    self.hits -= 1

                if rollback_sunk_length is not None and rollback_sunk_length in self.enemy_sunk_ships:
                    self.enemy_sunk_ships.remove(rollback_sunk_length)

                self.shots -= 1
                self.player_shots -= 1
                result = (row, col, current)
                break

            temp.append(entry)

        for entry in reversed(temp):
            self.history.push(entry)

        return result

    def get_enemy_visual_state(self):
        """Готовит визуальное состояние поля компьютера для интерфейса.
        принимает: нет
        возвращает: dict - клетки попаданий, промахов и зоны вокруг потопленных кораблей
        """
        hits = set()
        misses = set()
        zones = set()

        for r in range(SIZE):
            for c in range(SIZE):
                cell = self.computer_board[r][c]
                if cell == HIT:
                    hits.add((r, c))
                elif cell == MISS:
                    misses.add((r, c))

        visited = set()

        for r, c in hits:
            if (r, c) in visited:
                continue

            ship_cells, sunk = _process_hit(self.computer_board, r, c)

            for cell in ship_cells:
                visited.add(cell)

            if sunk:
                zones.update(get_zone_around(ship_cells))

        return {
            'hits': hits,
            'misses': misses,
            'zones': zones,
        }

    def _computer_random_shot(self):
        """Выбирает случайную необстрелянную клетку поля игрока.
        принимает: нет
        возвращает: tuple[int, int] - координаты клетки
        """
        while True:
            r = random.randint(0, SIZE - 1)
            c = random.randint(0, SIZE - 1)

            if self.player_board[r][c] not in (HIT, MISS):
                return r, c

    def _refill_hunt_queue(self):
        """Пересчитывает очередь добивания по текущим подбитым клеткам.
        принимает: нет
        возвращает: None
        """
        self.computer_targets.clear()

        if not self._hunt_hits:
            return

        for target in _get_hunt_targets(self.player_board, self._hunt_hits):
            self.computer_targets.enqueue(target)

    def computer_shoot(self):
        """Выполняет ход компьютера с умным добиванием.
        принимает: нет
        возвращает: dict - координаты, результат и служебные данные
        """
        row, col = None, None

        while not self.computer_targets.is_empty():
            candidate = self.computer_targets.dequeue()
            r, c = candidate

            if self.player_board[r][c] not in (HIT, MISS):
                row, col = r, c
                break

        if row is None:
            row, col = self._computer_random_shot()

        cell = self.player_board[row][col]
        self.shots += 1

        result = {
            'row': row,
            'col': col,
            'result': 'miss',
            'ship_cells': [],
            'zone': set(),
            'game_over': False,
        }

        if cell == SHIP:
            self.player_board[row][col] = HIT
            self.history.push(('computer', row, col, SHIP, None))

            ship_cells, sunk = _process_hit(self.player_board, row, col)
            result['ship_cells'] = ship_cells

            if sunk:
                zone = get_zone_around(ship_cells)
                self.player_sunk_ships.append(len(ship_cells))
                self._hunt_hits = []
                self.computer_targets.clear()
                result['result'] = 'sunk'
                result['zone'] = zone
            else:
                self._hunt_hits = [
                    (r, c) for r, c in ship_cells
                    if self.player_board[r][c] == HIT
                ]
                self._refill_hunt_queue()
                result['result'] = 'hit'

            result['game_over'] = all_ships_sunk(self.player_board)
            return result

        self.player_board[row][col] = MISS
        self.history.push(('computer', row, col, EMPTY, None))

        if self._hunt_hits:
            self._hunt_hits = [
                (r, c) for r, c in self._hunt_hits
                if self.player_board[r][c] == HIT
            ]
            self._refill_hunt_queue()

        self._switch_turn()
        return result

    def _switch_turn(self):
        """Передаёт ход другой стороне.
        принимает: нет
        возвращает: None
        """
        if self.current_turn == 'player':
            self.current_turn = 'computer'
        else:
            self.current_turn = 'player'