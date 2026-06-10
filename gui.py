import tkinter as tk

from game import (
    Game,
    SIZE, SHIPS, SHIP, HIT, MISS, EMPTY,
    find_ship_cells, is_ship_sunk, get_zone_around,
    all_ships_sunk, get_sorted_ships_stats,
)

# цвета и настройки интерфейса
COLOR_BG = '#1a1f2e'
COLOR_SURFACE = '#242938'
COLOR_EMPTY = '#2e3650'
COLOR_EMPTY_HVR = '#3a4468'
COLOR_SHIP = '#7f8a04'
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

        frame = tk.Frame(parent, bg=COLOR_BG)
        frame.pack(side=tk.LEFT, padx=18)

        tk.Label(
            frame, text=title, bg=COLOR_BG, fg=COLOR_ACCENT,
            font=('Arial', 12, 'bold')
        ).pack(pady=(0, 8))

        grid = tk.Frame(frame, bg=COLOR_BG)
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
                   state - str: 'ship', 'hit', 'miss', 'zone', 'empty'
        """
        colors = {
            'ship':  COLOR_SHIP,
            'hit':   COLOR_HIT,
            'miss':  COLOR_MISS,
            'zone':  COLOR_SUNK_ZONE,
            'empty': COLOR_EMPTY,
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
        # флаг: ожидаем ли хода компьютера прямо сейчас
        self._computer_thinking = False

        self._build_ui()
        self._new_game()

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
            (COLOR_SHIP,      'Ваш корабль'),
            (COLOR_HIT,       'Попадание'),
            (COLOR_MISS,      'Промах'),
            (COLOR_SUNK_ZONE, 'Зона затопления (убит)'),
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
            activebackground='#3a4468', command=self._new_game
        ).pack(side=tk.LEFT, padx=8)

        self.undo_btn = tk.Button(
            controls, text='Отменить ход', bg='#2e3650', fg=COLOR_UNDO,
            font=('Arial', 10, 'bold'), relief='flat', padx=16, pady=6,
            activebackground='#3a4468', command=self._undo_shot
        )
        self.undo_btn.pack(side=tk.LEFT, padx=8)

        self.turn_var = tk.StringVar(value='')
        tk.Label(
            controls, textvariable=self.turn_var,
            bg=COLOR_BG, fg='#7a8caa', font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=8)

        # строка статистики по кораблям
        self.stats_var = tk.StringVar(value='')
        tk.Label(
            self.root, textvariable=self.stats_var,
            bg=COLOR_BG, fg='#7a8caa', font=('Arial', 9)
        ).pack(pady=(0, 14))

    def _new_game(self):
        """Сбрасывает состояние и начинает новую партию."""
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self._computer_thinking = False

        self.game.setup()

        for r in range(SIZE):
            for c in range(SIZE):
                cell = self.game.player_board[r][c]
                self.player_widget.set_cell(r, c, 'ship' if cell == SHIP else 'empty')
                self.enemy_widget.set_cell(r, c, 'empty')
                self.enemy_widget.buttons[(r, c)].config(state='normal', cursor='hand2')

        self.player_widget.sunk_zones.clear()
        self.enemy_widget.sunk_zones.clear()
        self.status_var.set('Ваш ход — выберите клетку поля противника')
        self.turn_var.set('Ход 1')
        self.undo_btn.config(state='normal')
        self._update_stats_label()

    def _player_shot(self, row, col):
        """Обрабатывает выстрел игрока по клетке поля компьютера.
        принимает: row - int, col - int
        """
        if self._computer_thinking:
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
            self._update_turn_label()
            self._after_id = self.root.after(700, self._computer_shot)
            return

        self._update_turn_label()
        self._update_stats_label()

    def _undo_shot(self):
        """Отменяет последний выстрел игрока и восстанавливает клетку."""
        if self._computer_thinking:
            return
        result = self.game.undo_player_shot()
        if result is None:
            self.status_var.set('Нет ходов для отмены.')
            return
        row, col, _ = result
        self.enemy_widget.set_cell(row, col, 'empty')
        self.enemy_widget.buttons[(row, col)].config(state='normal', cursor='hand2')
        self.status_var.set(f'Ход отменён ({row + 1}, {col + 1}). Стреляйте снова.')
        self._update_turn_label()
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

        self._update_turn_label()

    def _update_turn_label(self):
        """Обновляет счётчик ходов и точность игрока."""
        acc = f'{self.game.get_accuracy():.0f}%' if self.game.player_shots else '—'
        self.turn_var.set(f'Выстрелов: {self.game.shots}  |  Точность: {acc}')

    def _update_stats_label(self):
        """Обновляет строку статистики с отсортированным списком кораблей."""
        sorted_ships = get_sorted_ships_stats(SHIPS)
        ships_str = '  '.join(f'[{s}]' for s in sorted_ships)
        self.stats_var.set(f'Корабли по размеру:  {ships_str}')

    def _end_game(self, winner):
        """Завершает партию, блокирует поле и показывает итог.
        принимает: winner - str: 'player' или 'computer'
        """
        self.enemy_widget.disable_all()
        self.undo_btn.config(state='disabled')
        if winner == 'player':
            self.status_var.set('🏆 Вы победили!')
            msg = (
                f'Поздравляем! Вы потопили все корабли!\n'
                f'Выстрелов: {self.game.shots}  |  Попаданий: {self.game.hits}'
            )
            color = COLOR_WIN
        else:
            self.status_var.set('💀 Компьютер победил')
            msg = 'Компьютер потопил все ваши корабли.\nПопробуйте ещё раз!'
            color = COLOR_LOSE

        popup = tk.Toplevel(self.root)
        popup.title('Игра окончена')
        popup.configure(bg=COLOR_SURFACE)
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(
            popup, text=msg, bg=COLOR_SURFACE, fg=color,
            font=('Arial', 12, 'bold'), pady=20, padx=30
        ).pack()
        tk.Button(
            popup, text='Новая игра', bg='#2e3650', fg=COLOR_ACCENT,
            font=('Arial', 10, 'bold'), relief='flat', padx=14, pady=6,
            command=lambda: (popup.destroy(), self._new_game())
        ).pack(pady=(0, 16))


def main():
    """Запускает tkinter-приложение."""
    root = tk.Tk()
    SeaBattleApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
