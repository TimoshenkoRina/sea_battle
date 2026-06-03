from collections import deque


class Stack:
    """Стек для хранения истории ходов (возможная отмена)."""

    def __init__(self):
        """Создаёт пустой стек."""
        self._data = []

    def push(self, item):
        """Добавляет ход в стек.
        принимает: item - любой объект хода
        возвращает: None
        """
        self._data.append(item)

    def pop(self):
        """Убирает и возвращает последний ход.
        возвращает: последний элемент или None, если стек пуст
        """
        if self.is_empty():
            return None
        return self._data.pop()

    def is_empty(self):
        """Проверяет, пуст ли стек.
        возвращает: bool - True если пуст
        """
        return len(self._data) == 0


class Queue:
    """Очередь для хранения приоритетных клеток следующего выстрела компьютера."""

    def __init__(self):
        """Создаёт пустую очередь."""
        self._data = deque()

    def enqueue(self, item):
        """Добавляет клетку в конец очереди.
        принимает: item - координаты клетки (row, col)
        возвращает: None
        """
        self._data.append(item)

    def dequeue(self):
        """Извлекает клетку из начала очереди.
        возвращает: элемент (row, col) или None если очередь пуста
        """
        if self.is_empty():
            return None
        return self._data.popleft()

    def is_empty(self):
        """Проверяет, пуста ли очередь.
        возвращает: bool - True если пуста
        """
        return len(self._data) == 0


class TreeNode:
    """Узел дерева поиска — одна клетка поля."""

    def __init__(self, row, col, parent=None):
        """Создаёт узел с координатами и ссылкой на родителя.
        принимает: row - int номер строки, col - int номер столбца,
                   parent - TreeNode или None
        """
        self.row = row
        self.col = col
        self.parent = parent
        self.children = []


class Tree:
    """Дерево поиска клеток поля по строкам (для стратегии компьютера)."""

    def __init__(self):
        """Создаёт пустое дерево."""
        self.root = None
        self._nodes = []

    def add_node(self, node, parent=None):
        """Добавляет узел в дерево.
        принимает: node - TreeNode, parent - TreeNode или None (корень если None)
        возвращает: None
        """
        if self.root is None:
            self.root = node
        else:
            node.parent = parent
            if parent is not None:
                parent.children.append(node)
        self._nodes.append(node)

    def remove_node(self, node):
        """Удаляет узел и отвязывает его от родителя.
        принимает: node - TreeNode
        возвращает: None
        """
        if node.parent is not None:
            node.parent.children.remove(node)
        if node in self._nodes:
            self._nodes.remove(node)
        if self.root is node:
            self.root = None
