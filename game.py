import random
from collections import Counter

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
    return [[EMPTY] * SIZE for _ in range(SIZE)]


def can_place(board, cells):
    """Проверяет, можно ли поставить корабль в клетки с учётом зазора.
    принимает: board - list[list[str]] - поле, cells - list[tuple[int, int]] - клетки корабля
    возвращает: bool - True если корабль можно поставить
    """
    for r, c in cells:
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == SHIP:
                    return False
    return True


def place_ships(board):
    """Случайно расставляет все корабли на поле.
    принимает: board - list[list[str]] - поле для расстановки
    возвращает: None - изменяет поле на месте
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


def all_ships_sunk(board):
    """Проверяет, потоплены ли все корабли на поле.
    принимает: board - list[list[str]] - игровое поле
    возвращает: bool - True если живых клеток кораблей не осталось
    """
    return all(cell != SHIP for row in board for cell in row)


def find_ship_cells(board, row, col):
    """Находит все клетки одного корабля по подбитой клетке.
    принимает: board - list[list[str]] - поле, row - int - строка, col - int - столбец
    возвращает: list[tuple[int, int]] - список клеток найденного корабля
    """
    stack = [(row, col)]
    visited = set()
    cells = []

    while stack:
        r, c = stack.pop()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        if board[r][c] not in (HIT, SHIP):
            continue
        cells.append((r, c))
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE and (nr, nc) not in visited:
                if board[nr][nc] in (HIT, SHIP):
                    stack.append((nr, nc))

    return cells


def is_ship_sunk(board, ship_cells):
    """Проверяет, потоплен ли корабль полностью.
    принимает: board - list[list[str]] - поле, ship_cells - list[tuple[int, int]] - клетки корабля
    возвращает: bool - True если среди клеток корабля нет целых частей
    """
    return all(board[r][c] != SHIP for r, c in ship_cells)


def get_zone_around(ship_cells):
    """Возвращает клетки вокруг потопленного корабля.
    принимает: ship_cells - list[tuple[int, int]] - клетки корабля
    возвращает: set[tuple[int, int]] - множество клеток вокруг корабля
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
    """Сортирует список длин кораблей по убыванию.
    принимает: ships_list - list[int] - список длин кораблей
    возвращает: list[int] - отсортированный список длин
    """
    return sorted(ships_list, reverse=True)


def _get_hunt_targets(board, hit_cells):
    """Вычисляет приоритетные цели для добивания корабля.

    Если известны 2+ подбитых клетки — определяет направление и стреляет
    только по продолжениям вдоль оси. Если одна клетка — все 4 соседа.

    принимает: board - list[list[str]] - поле игрока,
               hit_cells - list[tuple[int, int]] - уже подбитые клетки текущего корабля
    возвращает: list[tuple[int, int]] - список целей в порядке приоритета
    """
    if len(hit_cells) >= 2:
        rows = [r for r, c in hit_cells]
        cols = [c for r, c in hit_cells]

        if len(set(rows)) == 1:
            # горизонталь: стреляем влево от минимума и вправо от максимума
            row = rows[0]
            min_col = min(cols)
            max_col = max(cols)
            targets = []
            if max_col + 1 < SIZE and board[row][max_col + 1] not in (HIT, MISS):
                targets.append((row, max_col + 1))
            if min_col - 1 >= 0 and board[row][min_col - 1] not in (HIT, MISS):
                targets.append((row, min_col - 1))
            return targets

        if len(set(cols)) == 1:
            # вертикаль: стреляем выше минимума и ниже максимума
            col = cols[0]
            min_row = min(rows)
            max_row = max(rows)
            targets = []
            if max_row + 1 < SIZE and board[max_row + 1][col] not in (HIT, MISS):
                targets.append((max_row + 1, col))
            if min_row - 1 >= 0 and board[min_row - 1][col] not in (HIT, MISS):
                targets.append((min_row - 1, col))
            return targets

    # одна клетка или неопределённое направление — все 4 соседа
    r0, c0 = hit_cells[0]
    targets = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r0 + dr, c0 + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] not in (HIT, MISS):
            targets.append((nr, nc))
    return targets


class PlacementController:
    """Логика ручной расстановки кораблей без привязки к интерфейсу."""

    def __init__(self):
        """Создаёт контроллер ручной расстановки."""
        self.board = make_board()
        self.ship_index = 0
        self.horizontal = True
        self.ships = list(SHIPS)

    def toggle_orientation(self):
        """Меняет ориентацию текущего корабля.
        принимает: нет
        возвращает: None
        """
        self.horizontal = not self.horizontal

    def get_next_ship_length(self):
        """Возвращает длину следующего корабля.
        принимает: нет
        возвращает: int | None - длина корабля или None
        """
        if self.ship_index >= len(self.ships):
            return None
        return self.ships[self.ship_index]

    def is_finished(self):
        """Проверяет, завершена ли ручная расстановка.
        принимает: нет
        возвращает: bool - True если все корабли поставлены
        """
        return self.ship_index >= len(self.ships)

    def get_ship_cells(self, row, col):
        """Возвращает клетки текущего корабля по стартовой позиции.
        принимает: row - int - строка, col - int - столбец
        возвращает: list[tuple[int, int]] - список клеток или пустой список
        """
        if self.is_finished():
            return []
        length = self.ships[self.ship_index]
        cells = []
        for i in range(length):
            r = row if self.horizontal else row + i
            c = col + i if self.horizontal else col
            if not (0 <= r < SIZE and 0 <= c < SIZE):
                return []
            cells.append((r, c))
        return cells

    def place_ship(self, row, col):
        """Пытается поставить очередной корабль.
        принимает: row - int - строка, col - int - столбец
        возвращает: list[tuple[int, int]] - клетки поставленного корабля или пустой список
        """
        cells = self.get_ship_cells(row, col)
        if not cells or not can_place(self.board, cells):
            return []
        for r, c in cells:
            self.board[r][c] = SHIP
        self.ship_index += 1
        return cells


class Game:
    """Основная логика игры, ИИ и статистика партии."""

    def __init__(self):
        """Создаёт объект игры и все вспомогательные структуры."""
        self.player_board = None
        self.computer_board = None
        self.current_turn = 'player'
        self.history = Stack()
        self.computer_targets = Queue()
        # первое попадание текущей серии (для пересчёта направления)
        self._hunt_first_hit = None
        # все подбитые клетки текущего преследуемого корабля
        self._hunt_hits = []
        self.computer_coords = SortedCoordList(SIZE)
        self.computer_bst = ShipBST()
        self.shots = 0
        self.hits = 0
        self.player_shots = 0
        self.enemy_sunk_ships = []
        self.player_sunk_ships = []
        self.last_player_sunk_length = None

    def setup(self):
        """Создаёт новые поля и расставляет корабли случайно.
        принимает: нет
        возвращает: None
        """
        self.player_board = make_board()
        self.computer_board = make_board()
        place_ships(self.player_board)
        place_ships(self.computer_board)
        self._reset_runtime_state()
        self._rebuild_enemy_indexes()

    def setup_with_player_board(self, player_board):
        """Создаёт новую игру с уже готовым полем игрока.
        принимает: player_board - list[list[str]] - поле игрока с расставленными кораблями
        возвращает: None
        """
        self.player_board = [row[:] for row in player_board]
        self.computer_board = make_board()
        place_ships(self.computer_board)
        self._reset_runtime_state()
        self._rebuild_enemy_indexes()

    def _reset_runtime_state(self):
        """Сбрасывает счётчики и структуры во время старта новой игры.
        принимает: нет
        возвращает: None
        """
        self.current_turn = 'player'
        self.history = Stack()
        self.computer_targets = Queue()
        self._hunt_first_hit = None
        self._hunt_hits = []
        self.computer_coords = SortedCoordList(SIZE)
        self.computer_bst = ShipBST()
        self.shots = 0
        self.hits = 0
        self.player_shots = 0
        self.enemy_sunk_ships = []
        self.player_sunk_ships = []
        self.last_player_sunk_length = None

    def _rebuild_enemy_indexes(self):
        """Перестраивает структуры поиска по полю компьютера.
        принимает: нет
        возвращает: None
        """
        self.computer_coords = SortedCoordList(SIZE)
        self.computer_bst = ShipBST()
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
        return get_sorted_ships_stats(remaining)

    def get_enemy_ship_statistics(self):
        """Возвращает статистику кораблей противника.
        принимает: нет
        возвращает: dict - полная статистика по кораблям
        """
        remaining = self.get_remaining_enemy_ships()
        sunk = get_sorted_ships_stats(self.enemy_sunk_ships)
        return {
            'all': get_sorted_ships_stats(SHIPS),
            'remaining': remaining,
            'sunk': sunk,
            'remaining_counter': Counter(remaining),
            'sunk_counter': Counter(sunk),
        }

    def get_enemy_alive_cells_in_row(self, row):
        """Возвращает живые клетки кораблей противника в заданной строке через BST.
        принимает: row - int - номер строки
        возвращает: list[int] - отсортированный список столбцов
        """
        return sorted(self.computer_bst.get_cols_in_row(row))

    def player_shoot(self, row, col):
        """Выполняет выстрел игрока по полю компьютера.
        принимает: row - int - строка, col - int - столбец
        возвращает: dict - результат выстрела и служебные данные
        """
        self.last_player_sunk_length = None
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
            ship_cells = find_ship_cells(self.computer_board, row, col)
            result['ship_cells'] = ship_cells

            if is_ship_sunk(self.computer_board, ship_cells):
                length = len(ship_cells)
                zone = get_zone_around(ship_cells)
                self.enemy_sunk_ships.append(length)
                self.last_player_sunk_length = length
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
            ship_cells = find_ship_cells(self.computer_board, r, c)
            for cell in ship_cells:
                visited.add(cell)
            if is_ship_sunk(self.computer_board, ship_cells):
                zones.update(get_zone_around(ship_cells))

        return {'hits': hits, 'misses': misses, 'zones': zones}

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
        # выбор клетки
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
            ship_cells = find_ship_cells(self.player_board, row, col)
            result['ship_cells'] = ship_cells

            if is_ship_sunk(self.player_board, ship_cells):
                # корабль потоплен — сброс состояния охоты
                zone = get_zone_around(ship_cells)
                self.player_sunk_ships.append(len(ship_cells))
                self._hunt_first_hit = None
                self._hunt_hits = []
                self.computer_targets.clear()
                result['result'] = 'sunk'
                result['zone'] = zone
            else:
                # продолжаем добивать: храним только подбитые (HIT) клетки
                if self._hunt_first_hit is None:
                    self._hunt_first_hit = (row, col)
                self._hunt_hits = [
                    (r, c) for r, c in ship_cells
                    if self.player_board[r][c] == HIT
                ]
                # пересчитываем очередь по всем известным попаданиям
                self._refill_hunt_queue()
                result['result'] = 'hit'

            result['game_over'] = all_ships_sunk(self.player_board)
            return result

        # промах
        self.player_board[row][col] = MISS
        self.history.push(('computer', row, col, EMPTY, None))

        # если промах во время добивания — пересчитываем цели
        if self._hunt_hits:
            # обновляем список подбитых (исключаем возможные SHIP, которые могли попасть туда)
            self._hunt_hits = [
                (r, c) for r, c in self._hunt_hits
                if self.player_board[r][c] == HIT
            ]
            self._refill_hunt_queue()

        self._switch_turn()
        result['result'] = 'miss'
        return result

    def get_accuracy(self):
        """Считает точность игрока.
        принимает: нет
        возвращает: float - процент попаданий
        """
        if self.player_shots == 0:
            return 0.0
        return self.hits / self.player_shots * 100

    def is_finished(self):
        """Проверяет, закончилась ли партия.
        принимает: нет
        возвращает: bool - True если одна из сторон проиграла
        """
        return all_ships_sunk(self.computer_board) or all_ships_sunk(self.player_board)

    def _switch_turn(self):
        """Передаёт ход другой стороне.
        принимает: нет
        возвращает: None
        """
        self.current_turn = 'computer' if self.current_turn == 'player' else 'player'