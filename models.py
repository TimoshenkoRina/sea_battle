from collections import deque
import bisect


class Stack:
    """Стек для хранения истории ходов игрока (отмена выстрела)."""

    def __init__(self):
        """Создаёт пустой стек."""
        self._data = []

    def push(self, item):
        """Добавляет запись хода в стек.
        принимает: item - кортеж (row, col, old_value) — координаты и старое состояние клетки
        возвращает: None
        """
        self._data.append(item)

    def pop(self):
        """Убирает и возвращает последний ход.
        возвращает: кортеж (row, col, old_value) или None, если стек пуст
        """
        if self.is_empty():
            return None
        return self._data.pop()

    def peek(self):
        """Возвращает последний ход без извлечения.
        возвращает: последний элемент или None
        """
        if self.is_empty():
            return None
        return self._data[-1]

    def is_empty(self):
        """Проверяет, пуст ли стек.
        возвращает: bool
        """
        return len(self._data) == 0


class Queue:
    """Очередь приоритетных целей компьютера после первого попадания."""

    def __init__(self):
        """Создаёт пустую очередь."""
        self._data = deque()

    def enqueue(self, item):
        """Добавляет клетку в конец очереди.
        принимает: item - (row, col)
        возвращает: None
        """
        self._data.append(item)

    def dequeue(self):
        """Извлекает клетку из начала очереди.
        возвращает: (row, col) или None если пусто
        """
        if self.is_empty():
            return None
        return self._data.popleft()

    def clear(self):
        """Очищает очередь.
        возвращает: None
        """
        self._data.clear()

    def is_empty(self):
        """Проверяет, пуста ли очередь.
        возвращает: bool
        """
        return len(self._data) == 0


class SortedCoordList:
    """Отсортированный список координат для бинарного поиска.

    Хранит координаты живых клеток кораблей в каждой строке/столбце.
    Позволяет быстро проверить наличие целей через бинарный поиск.
    """

    def __init__(self, size: int):
        """Создаёт структуру для поля заданного размера.
        принимает: size - int, размер поля (число строк/столбцов)
        """
        self._size = size
        # _rows[r] — отсортированный список столбцов с живыми кораблями в строке r
        self._rows = [[] for _ in range(size)]
        # _cols[c] — отсортированный список строк с живыми кораблями в столбце c
        self._cols = [[] for _ in range(size)]

    def add(self, row: int, col: int):
        """Добавляет координату клетки корабля.
        принимает: row - int, col - int
        возвращает: None
        """
        bisect.insort(self._rows[row], col)
        bisect.insort(self._cols[col], row)

    def remove(self, row: int, col: int):
        """Удаляет координату (корабль подбит).
        принимает: row - int, col - int
        возвращает: None
        """
        idx = bisect.bisect_left(self._rows[row], col)
        if idx < len(self._rows[row]) and self._rows[row][idx] == col:
            self._rows[row].pop(idx)
        idx = bisect.bisect_left(self._cols[col], row)
        if idx < len(self._cols[col]) and self._cols[col][idx] == row:
            self._cols[col].pop(idx)

    def has_ship_in_row(self, row: int) -> bool:
        """Бинарным поиском проверяет, остались ли корабли в строке.
        принимает: row - int
        возвращает: bool - True если есть хотя бы одна живая клетка
        """
        return len(self._rows[row]) > 0

    def has_ship_in_col(self, col: int) -> bool:
        """Бинарным поиском проверяет, остались ли корабли в столбце.
        принимает: col - int
        возвращает: bool
        """
        return len(self._cols[col]) > 0

    def search_in_row(self, row: int, col: int) -> bool:
        """Бинарный поиск: есть ли корабль в строке row в позиции col.
        принимает: row - int, col - int
        возвращает: bool
        """
        lst = self._rows[row]
        idx = bisect.bisect_left(lst, col)
        return idx < len(lst) and lst[idx] == col

    def all_sunk(self) -> bool:
        """Проверяет, все ли корабли потоплены (все списки пусты).
        возвращает: bool
        """
        return all(len(r) == 0 for r in self._rows)


class BSTreeNode:
    """Узел бинарного дерева поиска — ключ: строка поля, значение: множество столбцов."""

    def __init__(self, row: int):
        """Создаёт узел для заданной строки.
        принимает: row - int, номер строки
        """
        self.row = row
        self.cols = set()
        self.left = None
        self.right = None


class ShipBST:
    """Бинарное дерево поиска для быстрого нахождения неподбитых клеток по строке.

    Ключ — номер строки, значение — множество столбцов с живыми кораблями.
    """

    def __init__(self):
        """Создаёт пустое дерево."""
        self._root = None

    def insert(self, row: int, col: int):
        """Добавляет клетку (row, col) в дерево.
        принимает: row - int, col - int
        возвращает: None
        """
        self._root = self._insert(self._root, row, col)

    def _insert(self, node, row: int, col: int):
        """Рекурсивная вставка узла.
        принимает: node - BSTreeNode или None, row - int, col - int
        возвращает: BSTreeNode
        """
        if node is None:
            n = BSTreeNode(row)
            n.cols.add(col)
            return n
        if row < node.row:
            node.left = self._insert(node.left, row, col)
        elif row > node.row:
            node.right = self._insert(node.right, row, col)
        else:
            node.cols.add(col)
        return node

    def remove(self, row: int, col: int):
        """Удаляет клетку после попадания.
        принимает: row - int, col - int
        возвращает: None
        """
        node = self._find(self._root, row)
        if node:
            node.cols.discard(col)

    def get_cols_in_row(self, row: int) -> set:
        """Возвращает множество столбцов с живыми кораблями в строке.
        принимает: row - int
        возвращает: set[int] — может быть пустым
        """
        node = self._find(self._root, row)
        return node.cols if node else set()

    def _find(self, node, row: int):
        """Поиск узла по строке.
        принимает: node - BSTreeNode или None, row - int
        возвращает: BSTreeNode или None
        """
        if node is None or node.row == row:
            return node
        if row < node.row:
            return self._find(node.left, row)
        return self._find(node.right, row)

    def all_sunk(self) -> bool:
        """Проверяет, все ли корабли потоплены.
        возвращает: bool
        """
        return self._all_empty(self._root)

    def _all_empty(self, node) -> bool:
        """Рекурсивно проверяет, пусты ли все узлы.
        принимает: node - BSTreeNode или None
        возвращает: bool
        """
        if node is None:
            return True
        return len(node.cols) == 0 and self._all_empty(node.left) and self._all_empty(node.right)
