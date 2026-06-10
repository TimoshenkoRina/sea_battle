import tkinter as tk
from tkinter import messagebox

from game import (
    Game,
    SIZE, SHIPS, SHIP, HIT, MISS, EMPTY,
    find_ship_cells, is_ship_sunk, get_zone_around,
    all_ships_sunk, place_ships, make_board, can_place,
)

# цвета и настройки интерфейса
COLOR_BG = '#1a1f2e'
COLOR_SURFACE = '#242938'
COLOR_EMPTY = '#2e3650'
COLOR_EMPTY_HVR = '#3a4468'
COLOR_SHIP = '#7f8a04'
COLOR_SHIP_PLACE = '#4a7a04'   # цвет корабля при ручной расстановке
COLOR_SHIP_PREVIEW = '#5a9a04' # цвет превью при наведении
COLOR_HIT = '#871407'
COLOR_MISS = '#6c7a9c'
COLOR_SUNK_ZONE = '#6c7a9c'
COLOR_TEXT = '#e8eaf0'
COLOR_ACCENT = '#4fc3f7'
COLOR_WIN = '#43e97b'
COLOR_LOSE = '#e63946'
COLOR_UNDO = '#f0a500'




class BoardWidget:
    """Виджет игрового поля: сетка кнопок с подсветкой и поддержкой hover."""

    def __init__(self, parent, title, clickable, on_click=None):
        """Создаёт фрейм с заголовком и сеткой клеток.
        принимает: parent - tk.Widget, title - str, clickable - bool,
                   on_click - callable(row, col) или None
        """
        self.clickable = clickable
        self.on_click = on_click
        self.buttons = {}
        self.sunk_zones = set()

        self.frame = tk.Frame(parent, bg=COLOR_BG)
        self.frame.pack(side=tk.LEFT, padx=18)

        tk.Label(
            self.frame, text=title, bg=COLOR_BG, fg=COLOR_ACCENT,
            font=('Arial', 12, 'bold')
        ).pack(pady=(0, 8))

        grid = tk.Frame(self.frame, bg=COLOR_BG)
        grid.pack()

        tk.Label(grid, text='', bg=COLOR_BG, width=2).grid(row=0, column=0)
        for i in range(SIZE):
            tk.Label(
                grid, text=str(i + 1), bg=COLOR_BG, fg='#7a8caa',
                font=('Arial', 9), width=3
            ).grid(row=0, column=i + 1)
            tk.Label(
                grid, text=str(i + 1), bg=COLOR_BG, fg='#7a8caa',
                font=('Arial', 9), width=2
            ).grid(row=i + 1, column=0)

        for r in range(SIZE):
            for c in range(SIZE):
                btn = tk.Button(
                    grid, width=2, height=1, bg=COLOR_EMPTY, bd=0,
                    relief='flat',
                    cursor='hand2' if clickable else 'arrow',
                    activebackground=COLOR_EMPTY_HVR
                )
                btn.grid(row=r + 1, column=c + 1, padx=2, pady=2)
                self.buttons[(r, c)] = btn

                if clickable:
                    btn.bind('<Enter>', lambda e, b=btn, p=(r, c): self._hover(b, p, True))
                    btn.bind('<Leave>', lambda e, b=btn, p=(r, c): self._hover(b, p, False))
                    btn.config(command=lambda row=r, col=c: self._click(row, col))

    def _hover(self, btn, pos, entering):
        """Подсвечивает клетку при наведении, если она ещё не обстреляна.
        принимает: btn - tk.Button, pos - (int, int), entering - bool
        """
        if btn.cget('bg') in (COLOR_HIT, COLOR_MISS, COLOR_SHIP, COLOR_SUNK_ZONE):
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
        принимает: row - int, col - int,
                   state - str: 'ship', 'hit', 'miss', 'zone', 'empty', 'preview'
        """
        colors = {
            'ship':    COLOR_SHIP,
            'placing': COLOR_SHIP_PLACE,
            'preview': COLOR_SHIP_PREVIEW,
            'hit':     COLOR_HIT,
            'miss':    COLOR_MISS,
            'zone':    COLOR_SUNK_ZONE,
            'empty':   COLOR_EMPTY,
        }
        self.buttons[(row, col)].config(bg=colors.get(state, COLOR_EMPTY))

    def mark_sunk_zone(self, zone_cells):
        """Закрашивает клетки-зазор вокруг потопленного корабля.
        принимает: zone_cells - set[(int, int)]
        """
        for r, c in zone_cells:
            if self.buttons[(r, c)].cget('bg') != COLOR_HIT:
                self.set_cell(r, c, 'zone')
        self.sunk_zones.update(zone_cells)

    def disable_all(self):
        """Отключает клики по всему полю."""
        for btn in self.buttons.values():
            btn.config(state='disabled', cursor='arrow')


class PlacementPhase:
    """Фаза ручной расстановки кораблей игрока."""

    def __init__(self, board_widget, on_done):
        """Запускает фазу расстановки.
        принимает: board_widget - BoardWidget поля игрока,
                   on_done - callable(board) вызывается когда все корабли расставлены
        """
        self.widget = board_widget
        self.on_done = on_done
        self.board = make_board()
        # список кораблей для расстановки (по убыванию)
        self.ships_to_place = sorted(SHIPS, reverse=True)
        self.current_idx = 0
        self.horizontal = True   # ориентация текущего корабля
        self._preview_cells = [] # клетки текущего превью

        # активируем клики и hover на поле игрока
        for r in range(SIZE):
            for c in range(SIZE):
                btn = self.widget.buttons[(r, c)]
                btn.config(state='normal', cursor='hand2')
                btn.bind('<Enter>', lambda e, rr=r, cc=c: self._on_hover(rr, cc))
                btn.bind('<Leave>', lambda e: self._clear_preview())
                btn.config(command=lambda rr=r, cc=c: self._on_click(rr, cc))

    def _current_length(self):
        """Возвращает длину текущего корабля для расстановки.
        возвращает: int - длина корабля или 0 если все расставлены
        """
        if self.current_idx >= len(self.ships_to_place):
            return 0
        return self.ships_to_place[self.current_idx]

    def _get_cells(self, row, col):
        """Вычисляет клетки корабля начиная с (row, col) с учётом ориентации.
        принимает: row - int, col - int
        возвращает: list[(int, int)] или None если выходит за границы
        """
        length = self._current_length()
        cells = []
        for i in range(length):
            r = row + (0 if self.horizontal else i)
            c = col + (i if self.horizontal else 0)
            if not (0 <= r < SIZE and 0 <= c < SIZE):
                return None
            cells.append((r, c))
        return cells

    def _on_hover(self, row, col):
        """Показывает превью корабля при наведении мыши.
        принимает: row - int, col - int
        """
        self._clear_preview()
        cells = self._get_cells(row, col)
        if cells is None:
            return
        valid = can_place(self.board, cells)
        for r, c in cells:
            self.widget.set_cell(r, c, 'preview' if valid else 'hit')
        self._preview_cells = cells

    def _clear_preview(self):
        """Убирает превью с поля."""
        for r, c in self._preview_cells:
            current = self.board[r][c]
            self.widget.set_cell(r, c, 'placing' if current == SHIP else 'empty')
        self._preview_cells = []

    def _on_click(self, row, col):
        """Ставит корабль на поле при клике, если позиция допустима.
        принимает: row - int, col - int
        """
        cells = self._get_cells(row, col)
        if cells is None or not can_place(self.board, cells):
            return
        for r, c in cells:
            self.board[r][c] = SHIP
            self.widget.set_cell(r, c, 'placing')
        self.current_idx += 1
        self._preview_cells = []
        if self.current_idx >= len(self.ships_to_place):
            # все корабли расставлены
            self._finish()

    def toggle_orientation(self):
        """Переключает ориентацию текущего корабля (горизонталь/вертикаль)."""
        self.horizontal = not self.horizontal

    def _finish(self):
        """Завершает расстановку и передаёт доску в колбэк."""
        # убираем обработчики hover/click с поля
        for r in range(SIZE):
            for c in range(SIZE):
                btn = self.widget.buttons[(r, c)]
                btn.unbind('<Enter>')
                btn.unbind('<Leave>')
                btn.config(command='', cursor='arrow', state='disabled')
        # перекрашиваем корабли в обычный цвет
        for r in range(SIZE):
            for c in range(SIZE):
                if self.board[r][c] == SHIP:
                    self.widget.set_cell(r, c, 'ship')
        self.on_done(self.board)


class SeaBattleApp:
    """Класс главного окна приложения."""

    def __init__(self, root):
        """Инициализирует окно, создаёт игру и строит интерфейс.
        принимает: root - tk.Tk
        """
        self.root = root
        self.root.title('Морской бой')
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.game = Game()
        self._after_id = None
        self._computer_thinking = False
        self._placement = None  # активная фаза расстановки или None

        self._build_ui()
        self._ask_placement_mode()

    def _build_ui(self):
        """Строит все виджеты интерфейса."""
        header = tk.Frame(self.root, bg=COLOR_BG)
        header.pack(pady=(18, 4))
        tk.Label(
            header, text='⚓  МОРСКОЙ БОЙ', bg=COLOR_BG, fg=COLOR_ACCENT,
            font=('Arial', 18, 'bold')
        ).pack()

        self.status_var = tk.StringVar(value='Новая игра...')
        tk.Label(
            self.root, textvariable=self.status_var,
            bg=COLOR_BG, fg=COLOR_TEXT, font=('Arial', 11), height=2
        ).pack()

        boards_frame = tk.Frame(self.root, bg=COLOR_BG)
        boards_frame.pack(padx=20, pady=8)

        self.player_widget = BoardWidget(boards_frame, 'Ваше поле', clickable=False)
        self.enemy_widget = BoardWidget(
            boards_frame, 'Поле противника',
            clickable=True, on_click=self._player_shot
        )

        # легенда цветов
        legend = tk.Frame(self.root, bg=COLOR_BG)
        legend.pack(pady=6)
        for color, label in [
            (COLOR_SHIP, 'Ваш корабль'),
            (COLOR_HIT,  'Попадание'),
            (COLOR_MISS, 'Промах'),
        ]:
            tk.Frame(legend, bg=color, width=14, height=14).pack(side=tk.LEFT, padx=(10, 3))
            tk.Label(
                legend, text=label, bg=COLOR_BG, fg='#7a8caa', font=('Arial', 9)
            ).pack(side=tk.LEFT, padx=(0, 6))

        # кнопки управления
        controls = tk.Frame(self.root, bg=COLOR_BG)
        controls.pack(pady=(8, 4))

        tk.Button(
            controls, text='Новая игра', bg='#2e3650', fg=COLOR_ACCENT,
            font=('Arial', 10, 'bold'), relief='flat', padx=16, pady=6,
            activebackground='#3a4468', command=self._ask_placement_mode
        ).pack(side=tk.LEFT, padx=8)

        self.rotate_btn = tk.Button(
            controls, text='Повернуть [R]', bg='#2e3650', fg='#a0c4ff',
            font=('Arial', 10, 'bold'), relief='flat', padx=16, pady=6,
            activebackground='#3a4468', command=self._rotate_ship,
            state='disabled'
        )
        self.rotate_btn.pack(side=tk.LEFT, padx=8)

        self.undo_btn = tk.Button(
            controls, text='Отменить ход', bg='#2e3650', fg=COLOR_UNDO,
            font=('Arial', 10, 'bold'), relief='flat', padx=16, pady=6,
            activebackground='#3a4468', command=self._undo_shot,
            state='disabled'
        )
        self.undo_btn.pack(side=tk.LEFT, padx=8)

        # горячая клавиша R для поворота
        self.root.bind('<r>', lambda e: self._rotate_ship())
        self.root.bind('<R>', lambda e: self._rotate_ship())

        # строка с оставшимися кораблями
        self.stats_var = tk.StringVar(value='')
        tk.Label(
            self.root, textvariable=self.stats_var,
            bg=COLOR_BG, fg='#7a8caa', font=('Arial', 9)
        ).pack(pady=(0, 14))

    def _ask_placement_mode(self):
        """Спрашивает пользователя: расставить корабли вручную или случайно."""
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self._computer_thinking = False
        self._placement = None

        # сбрасываем поля визуально
        self.game.setup()
        for r in range(SIZE):
            for c in range(SIZE):
                self.player_widget.set_cell(r, c, 'empty')
                self.enemy_widget.set_cell(r, c, 'empty')
                self.enemy_widget.buttons[(r, c)].config(state='disabled', cursor='arrow')
        self.player_widget.sunk_zones.clear()
        self.enemy_widget.sunk_zones.clear()
        self.undo_btn.config(state='disabled')
        self.rotate_btn.config(state='disabled')

        answer = messagebox.askyesno(
            'Расстановка кораблей',
            'Хотите расставить корабли вручную?\n\n'
            'Да — расставить самостоятельно\n'
            'Нет — случайная расстановка'
        )
        if answer:
            self._start_manual_placement()
        else:
            self._start_random_game()

    def _start_random_game(self):
        """Запускает партию со случайной расстановкой кораблей."""
        # game.setup() уже вызван в _ask_placement_mode
        for r in range(SIZE):
            for c in range(SIZE):
                cell = self.game.player_board[r][c]
                self.player_widget.set_cell(r, c, 'ship' if cell == SHIP else 'empty')
                self.enemy_widget.buttons[(r, c)].config(state='normal', cursor='hand2')
        self.status_var.set('Ваш ход — выберите клетку поля противника')
        self.undo_btn.config(state='normal')
        self._update_stats_label()

    def _start_manual_placement(self):
        """Запускает фазу ручной расстановки кораблей."""
        # создаём чистую доску для игрока вместо случайной
        self.game.player_board = make_board()
        self.rotate_btn.config(state='normal')
        self._update_placement_status()
        self._placement = PlacementPhase(
            self.player_widget,
            on_done=self._on_placement_done
        )

    def _update_placement_status(self):
        """Обновляет статус во время ручной расстановки."""
        if self._placement is None:
            return
        idx = self._placement.current_idx
        if idx >= len(self._placement.ships_to_place):
            return
        length = self._placement.ships_to_place[idx]
        orient = 'горизонтально' if self._placement.horizontal else 'вертикально'
        remaining = self._placement.ships_to_place[idx:]
        ships_str = ' '.join(f'[{s}]' for s in remaining)
        self.status_var.set(
            f'Ставим корабль длиной {length} ({orient}). '
            f'Осталось: {ships_str}\n'
            f'[R] — повернуть'
        )

    def _rotate_ship(self):
        """Переключает ориентацию текущего корабля при расстановке."""
        if self._placement is None:
            return
        self._placement.toggle_orientation()
        self._update_placement_status()

    def _on_placement_done(self, board):
        """Вызывается когда игрок закончил расстановку кораблей.
        принимает: board - list[list[str]] - доска с расставленными кораблями
        """
        self.game.player_board = board
        self.rotate_btn.config(state='disabled')
        self._placement = None
        # активируем поле врага
        for r in range(SIZE):
            for c in range(SIZE):
                self.enemy_widget.buttons[(r, c)].config(state='normal', cursor='hand2')
        self.status_var.set('Корабли расставлены! Ваш ход — выберите клетку противника')
        self.undo_btn.config(state='normal')
        self._update_stats_label()

    def _player_shot(self, row, col):
        """Обрабатывает выстрел игрока по клетке поля компьютера.
        принимает: row - int, col - int
        """
        if self._computer_thinking or self._placement is not None:
            return
        btn = self.enemy_widget.buttons[(row, col)]
        if btn.cget('state') == 'disabled':
            return

        result = self.game.player_shoot(row, col)

        if result in ('hit', 'sunk'):
            self.enemy_widget.set_cell(row, col, 'hit')
            btn.config(state='disabled')

            ship_cells = find_ship_cells(self.game.computer_board, row, col)
            if result == 'sunk':
                zone = get_zone_around(ship_cells)
                self.enemy_widget.mark_sunk_zone(zone)
                for r, c in zone:
                    self.enemy_widget.buttons[(r, c)].config(state='disabled', cursor='arrow')
                self.status_var.set('Корабль потоплен! Стреляйте ещё.')
            else:
                self.status_var.set('Попадание! Продолжайте ходить.')

            if all_ships_sunk(self.game.computer_board):
                self._end_game(winner='player')
                return

        else:  # miss
            self.enemy_widget.set_cell(row, col, 'miss')
            btn.config(state='disabled')
            self.status_var.set('Промах. Ход компьютера...')
            self._computer_thinking = True
            self.undo_btn.config(state='disabled')
            self._after_id = self.root.after(700, self._computer_shot)
            return

        self._update_stats_label()

    def _undo_shot(self):
        """Отменяет последний выстрел игрока и восстанавливает клетку."""
        if self._computer_thinking or self._placement is not None:
            return
        result = self.game.undo_player_shot()
        if result is None:
            self.status_var.set('Нет ходов для отмены.')
            return
        row, col, _ = result
        self.enemy_widget.set_cell(row, col, 'empty')
        self.enemy_widget.buttons[(row, col)].config(state='normal', cursor='hand2')
        self.status_var.set(f'Ход отменён ({row + 1}, {col + 1}). Стреляйте снова.')
        self._update_stats_label()

    def _computer_shot(self):
        """Выполняет ход компьютера и обновляет поле игрока."""
        self._after_id = None

        row, col, result = self.game.computer_shoot()

        if result in ('hit', 'sunk'):
            self.player_widget.set_cell(row, col, 'hit')
            ship_cells = find_ship_cells(self.game.player_board, row, col)
            if result == 'sunk':
                zone = get_zone_around(ship_cells)
                self.player_widget.mark_sunk_zone(zone)
                self.status_var.set('Компьютер потопил ваш корабль!')
            else:
                self.status_var.set('Компьютер попал! Снова ход компьютера...')

            if all_ships_sunk(self.game.player_board):
                self._computer_thinking = False
                self._end_game(winner='computer')
                return

            self._after_id = self.root.after(800, self._computer_shot)
        else:  # miss
            self.player_widget.set_cell(row, col, 'miss')
            self.status_var.set('Компьютер промахнулся. Ваш ход!')
            self._computer_thinking = False
            self.undo_btn.config(state='normal')

    def _update_stats_label(self):
        """Обновляет строку с оставшимися кораблями противника."""
        remaining = self.game.get_remaining_enemy_ships()
        if remaining:
            ships_str = '  '.join(f'[{s}]' for s in remaining)
            self.stats_var.set(f'Осталось кораблей:  {ships_str}')
        else:
            self.stats_var.set('Все корабли противника потоплены!')

    def _end_game(self, winner):
        """Завершает партию, блокирует поле и показывает итог.
        принимает: winner - str: 'player' или 'computer'
        """
        self.enemy_widget.disable_all()
        self.undo_btn.config(state='disabled')

        if winner == 'player':
            self.status_var.set('🏆 Вы победили!')
            self._show_win_popup()
        else:
            self.status_var.set('💀 Компьютер победил')
            self._show_lose_popup()

    def _show_win_popup(self):
        """Показывает попап победы с мемом Уильяма Дефо."""
        popup = tk.Toplevel(self.root)
        popup.title('Победа!')
        popup.configure(bg=COLOR_SURFACE)
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(
            popup, text='🏆 Поздравляем! Вы потопили все корабли!',
            bg=COLOR_SURFACE, fg=COLOR_WIN,
            font=('Arial', 13, 'bold'), pady=12, padx=20
        ).pack()

        tk.Button(
            popup, text='Новая игра', bg='#2e3650', fg=COLOR_ACCENT,
            font=('Arial', 10, 'bold'), relief='flat', padx=14, pady=6,
            command=lambda: (popup.destroy(), self._ask_placement_mode())
        ).pack(pady=(0, 16))

    def _show_lose_popup(self):
        """Показывает попап поражения."""
        popup = tk.Toplevel(self.root)
        popup.title('Игра окончена')
        popup.configure(bg=COLOR_SURFACE)
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(
            popup, text='Компьютер потопил все ваши корабли.\nПопробуйте ещё раз!',
            bg=COLOR_SURFACE, fg=COLOR_LOSE,
            font=('Arial', 12, 'bold'), pady=20, padx=30
        ).pack()
        tk.Button(
            popup, text='Новая игра', bg='#2e3650', fg=COLOR_ACCENT,
            font=('Arial', 10, 'bold'), relief='flat', padx=14, pady=6,
            command=lambda: (popup.destroy(), self._ask_placement_mode())
        ).pack(pady=(0, 16))


def main():
    """Запускает tkinter-приложение."""
    root = tk.Tk()
    SeaBattleApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
