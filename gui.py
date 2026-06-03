import tkinter as tk
from tkinter import messagebox
import random
from game import (
    Game, SIZE, SHIP, HIT, MISS, EMPTY,
    _all_ships_sunk, _make_board, _place_ships,
)

# --- цвета ---
COLOR_BG        = '#1a1f2e'
COLOR_SURFACE   = '#242938'
COLOR_EMPTY     = '#2e3650'
COLOR_EMPTY_HVR = '#3a4468'
COLOR_SHIP      = '#3d5a80'  # корабли игрока (видимые)
COLOR_HIT       = '#e63946'  # попадание
COLOR_MISS      = '#6c7a9c'  # промах
COLOR_SUNK_ZONE = '#4a3040'  # зазор вокруг убитого корабля
COLOR_TEXT      = '#e8eaf0'
COLOR_ACCENT    = '#4fc3f7'
COLOR_WIN       = '#43e97b'
COLOR_LOSE      = '#e63946'

CELL = 44  # размер клетки в пикселях
PAD  = 6   # отступ между клетками


def _find_ship_cells(board, row, col):
    """Находит все клетки корабля, которому принадлежит указанная клетка.
    принимает: board - list[list[str]], row - int, col - int
    возвращает: list[(int, int)] - список клеток корабля
    """
    visited = set()
    stack = [(row, col)]
    cells = []
    while stack:
        r, c = stack.pop()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        if 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == HIT:
            cells.append((r, c))
            # ищем только по горизонтали и вертикали
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((r + dr, c + dc))
    return cells


def _is_ship_sunk(board, ship_cells):
    """Проверяет, полностью ли потоплен корабль (нет ли уцелевших клеток рядом).
    принимает: board - list[list[str]], ship_cells - list[(int, int)]
    возвращает: bool
    """
    for r, c in ship_cells:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                if board[nr][nc] == SHIP:
                    return False
    return True


def _get_zone_around(ship_cells):
    """Возвращает клетки-зазор вокруг корабля (не занятые самим кораблем).
    принимает: ship_cells - list[(int, int)]
    возвращает: set[(int, int)]
    """
    ship_set = set(ship_cells)
    zone = set()
    for r, c in ship_cells:
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE:
                    if (nr, nc) not in ship_set:
                        zone.add((nr, nc))
    return zone


class BoardWidget:
    """Виджет игрового поля: сетка кнопок с поддержкой hover и подсветки."""

    def __init__(self, parent, title, clickable, on_click=None):
        """Создаёт фрейм с заголовком и сеткой клеток.
        принимает: parent - tk.Widget, title - str заголовок,
                   clickable - bool разрешить клики, on_click - callable(row, col)
        """
        self.clickable = clickable
        self.on_click = on_click
        self.buttons = {}    # (row, col) -> tk.Button
        self.sunk_zones = set()  # клетки-зазор убитых кораблей

        frame = tk.Frame(parent, bg=COLOR_BG)
        frame.pack(side=tk.LEFT, padx=18)

        tk.Label(
            frame, text=title, bg=COLOR_BG, fg=COLOR_ACCENT,
            font=('Segoe UI', 13, 'bold')
        ).pack(pady=(0, 8))

        grid = tk.Frame(frame, bg=COLOR_BG)
        grid.pack()

        # заголовки столбцов
        tk.Label(grid, text='', bg=COLOR_BG, width=2).grid(row=0, column=0)
        for c in range(SIZE):
            tk.Label(
                grid, text=str(c + 1), bg=COLOR_BG, fg='#7a8caa',
                font=('Segoe UI', 9), width=3
            ).grid(row=0, column=c + 1)

        for r in range(SIZE):
            # заголовок строки
            tk.Label(
                grid, text=str(r + 1), bg=COLOR_BG, fg='#7a8caa',
                font=('Segoe UI', 9), width=2
            ).grid(row=r + 1, column=0)

            for c in range(SIZE):
                btn = tk.Button(
                    grid,
                    width=2, height=1,
                    bg=COLOR_EMPTY,
                    relief='flat',
                    bd=0,
                    cursor='hand2' if clickable else 'arrow',
                    activebackground=COLOR_EMPTY_HVR,
                )
                btn.grid(row=r + 1, column=c + 1, padx=2, pady=2)
                self.buttons[(r, c)] = btn

                if clickable:
                    btn.bind('<Enter>', lambda e, b=btn, pos=(r, c): self._hover(b, pos, True))
                    btn.bind('<Leave>', lambda e, b=btn, pos=(r, c): self._hover(b, pos, False))
                    btn.config(command=lambda row=r, col=c: self._click(row, col))

    def _hover(self, btn, pos, entering):
        """Подсвечивает клетку при наведении, если она ещё не обстреляна.
        принимает: btn - tk.Button, pos - (int, int), entering - bool
        """
        r, c = pos
        current = btn.cget('bg')
        if current in (COLOR_HIT, COLOR_MISS, COLOR_SHIP, COLOR_SUNK_ZONE):
            return
        btn.config(bg=COLOR_EMPTY_HVR if entering else COLOR_EMPTY)

    def _click(self, row, col):
        """Передаёт клик во внешний обработчик.
        принимает: row - int, col - int
        """
        if self.on_click:
            self.on_click(row, col)

    def set_cell(self, row, col, state):
        """Обновляет цвет клетки по её состоянию.
        принимает: row - int, col - int, state - str ('ship'/'hit'/'miss'/'zone'/'empty')
        """
        colors = {
            'ship': COLOR_SHIP,
            'hit':  COLOR_HIT,
            'miss': COLOR_MISS,
            'zone': COLOR_SUNK_ZONE,
            'empty': COLOR_EMPTY,
        }
        self.buttons[(row, col)].config(bg=colors.get(state, COLOR_EMPTY))

    def mark_sunk_zone(self, zone_cells):
        """Закрашивает клетки-зазор вокруг потопленного корабля.
        принимает: zone_cells - iterable[(int, int)]
        """
        for r, c in zone_cells:
            if self.buttons[(r, c)].cget('bg') not in (COLOR_HIT,):
                self.set_cell(r, c, 'zone')
        self.sunk_zones.update(zone_cells)

    def disable_all(self):
        """Отключает клики по всему полю."""
        for btn in self.buttons.values():
            btn.config(state=tk.DISABLED, cursor='arrow')


class SeaBattleApp:
    """Главное окно приложения Морской бой."""

    def __init__(self, root):
        """Инициализирует окно, создаёт игру и строит интерфейс.
        принимает: root - tk.Tk
        """
        self.root = root
        self.root.title('Морской бой')
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.game = Game()
        self._build_ui()
        self._new_game()

    def _build_ui(self):
        """Строит все виджеты интерфейса."""
        # --- заголовок ---
        header = tk.Frame(self.root, bg=COLOR_BG)
        header.pack(pady=(18, 4))
        tk.Label(
            header, text='⚓  МОРСКОЙ БОЙ',
            bg=COLOR_BG, fg=COLOR_ACCENT,
            font=('Segoe UI', 20, 'bold')
        ).pack()

        # --- статус ---
        self.status_var = tk.StringVar(value='Новая игра...')
        tk.Label(
            self.root, textvariable=self.status_var,
            bg=COLOR_BG, fg=COLOR_TEXT,
            font=('Segoe UI', 11), height=2
        ).pack()

        # --- поля ---
        boards_frame = tk.Frame(self.root, bg=COLOR_BG)
        boards_frame.pack(padx=20, pady=8)

        self.player_widget = BoardWidget(
            boards_frame, 'Ваше поле', clickable=False
        )
        self.enemy_widget = BoardWidget(
            boards_frame, 'Поле противника', clickable=True,
            on_click=self._player_shot
        )

        # --- легенда ---
        legend = tk.Frame(self.root, bg=COLOR_BG)
        legend.pack(pady=6)
        items = [
            (COLOR_SHIP,      'Ваш корабль'),
            (COLOR_HIT,       'Попадание'),
            (COLOR_MISS,      'Промах'),
            (COLOR_SUNK_ZONE, 'Зазор (убит)'),
        ]
        for color, label in items:
            dot = tk.Frame(legend, bg=color, width=14, height=14)
            dot.pack(side=tk.LEFT, padx=(10, 3))
            tk.Label(legend, text=label, bg=COLOR_BG, fg='#7a8caa',
                     font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 6))

        # --- кнопки управления ---
        controls = tk.Frame(self.root, bg=COLOR_BG)
        controls.pack(pady=(8, 18))
        tk.Button(
            controls, text='Новая игра',
            bg='#2e3650', fg=COLOR_ACCENT,
            font=('Segoe UI', 10, 'bold'),
            relief='flat', padx=16, pady=6,
            activebackground='#3a4468',
            command=self._new_game
        ).pack(side=tk.LEFT, padx=8)

        # --- счётчик ходов ---
        self.turn_var = tk.StringVar(value='')
        tk.Label(
            controls, textvariable=self.turn_var,
            bg=COLOR_BG, fg='#7a8caa',
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT, padx=8)

    def _new_game(self):
        """Сбрасывает состояние и начинает новую партию."""
        self.game.setup()
        self.shots = 0
        self.hits = 0

        # рисуем оба поля
        for r in range(SIZE):
            for c in range(SIZE):
                # поле игрока — корабли видны
                cell = self.game.player_board[r][c]
                self.player_widget.set_cell(r, c, 'ship' if cell == SHIP else 'empty')
                # поле врага — пусто
                self.enemy_widget.set_cell(r, c, 'empty')
                self.enemy_widget.buttons[(r, c)].config(
                    state=tk.NORMAL, cursor='hand2'
                )

        self.player_widget.sunk_zones.clear()
        self.enemy_widget.sunk_zones.clear()

        self.status_var.set('Ваш ход — нажмите на клетку поля противника')
        self.turn_var.set('Ход 1')

    def _player_shot(self, row, col):
        """Обрабатывает выстрел игрока по клетке (row, col) поля компьютера.
        принимает: row - int, col - int
        """
        board = self.game.computer_board
        btn = self.enemy_widget.buttons[(row, col)]

        # игнорируем уже обстрелянные клетки
        if board[row][col] in (HIT, MISS) or (row, col) in self.enemy_widget.sunk_zones:
            return
        if btn.cget('state') == tk.DISABLED:
            return

        self.shots += 1
        cell = board[row][col]

        if cell == SHIP:
            board[row][col] = HIT
            self.hits += 1
            self.enemy_widget.set_cell(row, col, 'hit')
            btn.config(state=tk.DISABLED)

            # проверяем, потоплен ли корабль
            ship_cells = _find_ship_cells(board, row, col)
            if _is_ship_sunk(board, ship_cells):
                zone = _get_zone_around(ship_cells)
                self.enemy_widget.mark_sunk_zone(zone)
                # блокируем зазор — стрелять туда бессмысленно
                for r, c in zone:
                    self.enemy_widget.buttons[(r, c)].config(
                        state=tk.DISABLED, cursor='arrow'
                    )
                self.status_var.set('Корабль потоплен! Стреляйте ещё.')
            else:
                self.status_var.set('Попадание! Ход снова ваш.')

            # при попадании ход не передаётся
            if _all_ships_sunk(board):
                self._end_game(winner='player')
                return

        else:
            board[row][col] = MISS
            self.enemy_widget.set_cell(row, col, 'miss')
            btn.config(state=tk.DISABLED)
            self.status_var.set('Мимо. Ход компьютера...')
            self._update_turn_label()
            # компьютер ходит с небольшой задержкой
            self.root.after(700, self._computer_shot)
            return

        self._update_turn_label()

    def _computer_shot(self):
        """Выполняет ход компьютера: выбирает клетку и обновляет поле игрока."""
        board = self.game.player_board
        targets = self.game.computer_targets

        # выбираем клетку
        if not targets.is_empty():
            row, col = targets.dequeue()
            while board[row][col] in (HIT, MISS):
                if targets.is_empty():
                    row, col = self._random_shot_on_player()
                    break
                row, col = targets.dequeue()
        else:
            row, col = self._random_shot_on_player()

        cell = board[row][col]
        self.shots += 1

        if cell == SHIP:
            board[row][col] = HIT
            self.player_widget.set_cell(row, col, 'hit')

            ship_cells = _find_ship_cells(board, row, col)
            if _is_ship_sunk(board, ship_cells):
                zone = _get_zone_around(ship_cells)
                self.player_widget.mark_sunk_zone(zone)
                self.status_var.set('Компьютер потопил ваш корабль!')
            else:
                self.status_var.set('Компьютер попал! Снова ход компьютера...')
                # добавляем соседей в очередь
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < SIZE and 0 <= nc < SIZE:
                        if board[nr][nc] not in (HIT, MISS):
                            targets.enqueue((nr, nc))

            if _all_ships_sunk(board):
                self._end_game(winner='computer')
                return

            # после попадания компьютер ходит снова
            self.root.after(800, self._computer_shot)

        else:
            board[row][col] = MISS
            self.player_widget.set_cell(row, col, 'miss')
            self.status_var.set('Компьютер промахнулся. Ваш ход!')

        self._update_turn_label()

    def _random_shot_on_player(self):
        """Выбирает случайную необстрелянную клетку поля игрока.
        возвращает: (int, int)
        """
        board = self.game.player_board
        while True:
            r = random.randint(0, SIZE - 1)
            c = random.randint(0, SIZE - 1)
            if board[r][c] not in (HIT, MISS):
                return r, c

    def _update_turn_label(self):
        """Обновляет счётчик ходов и точность."""
        acc = f'{self.hits / self.shots * 100:.0f}%' if self.shots else '—'
        self.turn_var.set(f'Выстрелов: {self.shots}  |  Точность: {acc}')

    def _end_game(self, winner):
        """Завершает партию: блокирует поле и показывает итог.
        принимает: winner - str 'player' или 'computer'
        """
        self.enemy_widget.disable_all()
        if winner == 'player':
            self.status_var.set('🏆 Вы победили!')
            msg = f'Поздравляем! Вы потопили все корабли!\nВыстрелов: {self.shots}  |  Попаданий: {self.hits}'
            color = COLOR_WIN
        else:
            self.status_var.set('💀 Компьютер победил.')
            msg = 'Компьютер потопил все ваши корабли.\nПопробуйте ещё раз!'
            color = COLOR_LOSE

        popup = tk.Toplevel(self.root)
        popup.title('Игра окончена')
        popup.configure(bg=COLOR_SURFACE)
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(
            popup, text=msg,
            bg=COLOR_SURFACE, fg=color,
            font=('Segoe UI', 12, 'bold'),
            pady=20, padx=30
        ).pack()
        tk.Button(
            popup, text='Новая игра',
            bg='#2e3650', fg=COLOR_ACCENT,
            font=('Segoe UI', 10, 'bold'),
            relief='flat', padx=14, pady=6,
            command=lambda: (popup.destroy(), self._new_game())
        ).pack(pady=(0, 16))


def main():
    """Запускает Tkinter-приложение Морской бой."""
    root = tk.Tk()
    SeaBattleApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
