
def bisect_left_manual(lst, value):
    """Ищет левую позицию для элемента в отсортированном списке"""
    left = 0
    right = len(lst)

    while left < right:
        mid = (left + right) // 2
        if lst[mid] < value:
            left = mid + 1
        else:
            right = mid

    return left

def insort_left_manual(lst, value):
    """Вставляет элемент в отсортированный список"""
    index = bisect_left_manual(lst, value)
    lst.insert(index, value)


class Stack:
    """Стек для хранения истории ходов игрока"""

    def __init__(self):
        self.data = []

    def push(self, item):
        """Добавляет запись хода в стек"""
        self.data.append(item)

    def pop(self):
        """Убирает и возвращает последний ход"""
        return self.data.pop() if not self.is_empty() else None

    def peek(self):
        """Возвращает последний ход без извлечения"""
        return self.data[-1] if not self.is_empty() else None

    def is_empty(self):
        """Проверяет, пуст ли стек"""
        return len(self.data) == 0

class Queue:
    """Очередь приоритетных целей компьютера после первого попадания"""

    def __init__(self):
        """Создаёт пустую очередь"""
        self.data = []

    def enqueue(self, item):
        """Добавляет клетку в конец очереди"""
        self.data.append(item)

    def dequeue(self):
        """Извлекает клетку из начала очереди"""
        return self.data.pop(0) if not self.is_empty() else None

    def clear(self):
        """Очищает очередь"""
        self.data.clear()

    def is_empty(self):
        """Проверяет, пуста ли очередь"""
        return len(self.data) == 0

class SortedCoordList:
    """Отсортированный список координат для бинарного поиска.

    Хранит координаты живых клеток кораблей в каждой строке/столбце.
    Позволяет быстро проверить наличие целей через бинарный поиск.
    """

    def __init__(self, size):
        """Создаёт структуру для поля заданного размера"""
        self.size = size
        self.rows = [[] for i in range(size)]
        self.cols = [[] for i in range(size)]

    def add(self, row, col):
        """Добавляет координату клетки корабля"""
        insort_left_manual(self.rows[row], col)
        insort_left_manual(self.cols[col], row)

    def remove(self, row, col):
        """Удаляет координату"""
        row_index = bisect_left_manual(self.rows[row], col)
        if row_index < len(self.rows[row]) and self.rows[row][row_index] == col:
            self.rows[row].pop(row_index)

        col_index = bisect_left_manual(self.cols[col], row)
        if col_index < len(self.cols[col]) and self.cols[col][col_index] == row:
            self.cols[col].pop(col_index)

class BSTreeNode:
    """Узел бинарного дерева поиска — ключ: строка поля, значение: множество столбцов."""

    def __init__(self, row):
        self.row = row
        self.cols = set()
        self.left = None
        self.right = None

class ShipBST:
    """Бинарное дерево поиска для быстрого нахождения неподбитых клеток по строке."""

    def __init__(self):
        """Создаёт пустое дерево"""
        self.root = None

    def insert(self, row, col):
        """Добавляет клетку в дерево"""
        if self.root is None:
            self.root = BSTreeNode(row)
            self.root.cols.add(col)
            return

        current = self.root

        while True:
            if row < current.row:
                if current.left is None:
                    current.left = BSTreeNode(row)
                    current.left.cols.add(col)
                    return
                current = current.left

            elif row > current.row:
                if current.right is None:
                    current.right = BSTreeNode(row)
                    current.right.cols.add(col)
                    return
                current = current.right

            else:
                current.cols.add(col)
                return

    def remove(self, row, col):
        """Удаляет клетку из дерева"""
        node = self.find(row)
        if node is not None:
            node.cols.discard(col)

    def find(self, row):
        """Ищет узел по номеру строки"""
        current = self.root

        while current is not None:
            if row < current.row:
                current = current.left
            elif row > current.row:
                current = current.right
            else:
                return current

        return None