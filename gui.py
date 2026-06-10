import tkinter as tk
from tkinter import messagebox

from game import *

COLOR_BG       = '#1a1f2e'  # фон окна
COLOR_SURFACE  = '#242938'  # фон всплывающего окна
COLOR_EMPTY    = '#2e3650'  # пустая клетка
COLOR_EMPTY_HVR= '#3a4468'  # пустая клетка при наведении
COLOR_SHIP     = '#7f8a04'  # клетка с кораблём
COLOR_HIT      = '#871407'  # попадание
COLOR_MISS     = '#6c7a9c'  # промах
COLOR_SUNK_ZONE= '#6c7a9c'  # зона вокруг потопленного корабля
COLOR_TEXT     = '#e8eaf0'  # основной текст
COLOR_ACCENT   = '#4fc3f7'  # заголовки, кнопки
COLOR_WIN      = '#43e97b'
COLOR_LOSE     = '#e63946'
COLOR_UNDO     = '#f0a500'  # кнопка отмены


class BoardWidget:
    """Виджет игрового поля"""

    def __init__(self, parent, title, clickable, on_click=None):
        """Создаёт фрейм с заголовком и сеткой клеток.
        принимает: parent - tk.Widget - родительский контейнер
                   title - str - заголовок над полем
                   clickable - bool - можно ли кликать по клеткам
                   on_click - callable(row, col) | None - обработчик клика
        возвращает: None
        """
        self.clickable = clickable
        self.on_click = on_click
        # словарь (row, col) → кнопка
        self.buttons = {}
        # множество клеток, закрашенных как зона вокруг потопленного корабля
        self.sunk_zones = set()

        # внешний фрейм поля
        frame = tk.Frame(parent, bg=COLOR_BG)
        frame.pack(side=tk.LEFT, padx=18)

        # заголовок над полем
        tk.Label(
            frame, text=title, bg=COLOR_BG, fg=COLOR_ACCENT,
            font=('Arial', 12, 'bold')
        ).pack(pady=(0, 8))

        # сетка с нумерацией строк и столбцов
        grid = tk.Frame(frame, bg=COLOR_BG)
        grid.pack()

        # пустая ячейка в левом верхнем углу (пересечение осей)
        tk.Label(grid, text='', bg=COLOR_BG, width=2).grid(row=0, column=0)

        # номера столбцов (верхняя строка) и строк (левый столбец)
        for i in range(SIZE):
            tk.Label(
                grid, text=str(i + 1), bg=COLOR_BG, fg='#7a8caa',
                font=('Arial', 9), width=3
            ).grid(row=0, column=i + 1)
            tk.Label(
                grid, text=str(i + 1), bg=COLOR_BG, fg='#7a8caa',
                font=('Arial', 9), width=2
            ).grid(row=i + 1, column=0)

        # создаём кнопку для каждой клетки поля
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

                # hover и клик — только для кликабельных полей
                if clickable:
                    btn.bind('<Enter>', lambda e, b=btn, p=(r, c): self._hover(b, p, True))
                    btn.bind('<Leave>', lambda e, b=btn, p=(r, c): self._hover(b, p, False))
                    btn.config(command=lambda row=r, col=c: self._click(row, col))

    def _hover(self, btn, pos, entering):
        """Подсвечивает клетку при наведении, если она ещё не обстреляна.
        принимает: btn - tk.Button, pos - tuple[int, int], entering - bool
        возвращает: None
        """
        # уже закрашенные клетки не трогаем
        if btn.cget('bg') in (COLOR_HIT, COLOR_MISS, COLOR_SHIP, COLOR_SUNK_ZONE):
            return
        btn.config(bg=COLOR_EMPTY_HVR if entering else COLOR_EMPTY)

    def _click(self, row, col):
        """Передаёт клик во внешний обработчик.
        принимает: row - int, col - int
        возвращает: None
        """
        if self.on_click:
            self.on_click(row, col)

    def set_cell(self, row, col, state):
        """Обновляет цвет клетки по её состоянию.
        принимает: row - int, col - int
                   state - str: 'ship' | 'hit' | 'miss' | 'zone' | 'empty'
        возвращает: None
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
        """Закрашивает клетки вокруг потопленного корабля.
        принимает: zone_cells - set[tuple[int, int]]
        возвращает: None
        """
        for r, c in zone_cells:
            # попадания не перекрашиваем
            if self.buttons[(r, c)].cget('bg') != COLOR_HIT:
                self.set_cell(r, c, 'zone')
        self.sunk_zones.update(zone_cells)

    def disable_all(self):
        """Отключает клики по всему полю (конец игры).
        принимает: нет
        возвращает: None
        """
        for btn in self.buttons.values():
            btn.config(state='disabled', cursor='arrow')

class SeaBattleApp:
    """Главное окно приложения: соединяет интерфейс с логикой игры"""

    def __init__(self, root):
        """Инициализирует окно, создаёт игру и строит интерфейс.
        принимает: root - tk.Tk
        возвращает: None
        """
        self.root = root
        self.root.title('Морской бой')
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.game = Game()

        # id отложенного вызова компьютерного хода (нужен для отмены)
        self.after_id = None
        # флаг: сейчас думает компьютер — блокируем клики игрока
        self.computer_thinking = False
        # контроллер ручной расстановки, None если расстановка не идёт
        self.placement_controller = None
        # разрешены ли клики по своему полю (только во время расстановки)
        self.player_board_click_enabled = False

        self._build_ui()
        # клавиша R переворачивает корабль при расстановке
        self.root.bind('<r>', self._toggle_placement_orientation)
        self.root.bind('<R>', self._toggle_placement_orientation)
        self._new_game()

    def _build_ui(self):
        """Строит все виджеты интерфейса.
        принимает: нет
        возвращает: None
        """
        # заголовок приложения
        header = tk.Frame(self.root, bg=COLOR_BG)
        header.pack(pady=(18, 4))
        tk.Label(
            header, text='МОРСКОЙ БОЙ', bg=COLOR_BG, fg=COLOR_ACCENT,
            font=('Arial', 18, 'bold')
        ).pack()

        # строка статуса — показывает подсказки и результаты ходов
        self.status_var = tk.StringVar(value='Новая игра...')
        tk.Label(
            self.root, textvariable=self.status_var,
            bg=COLOR_BG, fg=COLOR_TEXT, font=('Arial', 11), height=2
        ).pack()

        # контейнер для двух полей рядом
        boards_frame = tk.Frame(self.root, bg=COLOR_BG)
        boards_frame.pack(padx=20, pady=8)

        # левое поле — игрок (не кликабельное в боевом режиме)
        self.player_widget = BoardWidget(boards_frame, 'Ваше поле', clickable=False)
        # правое поле — противник (кликабельное, выстрелы игрока)
        self.enemy_widget = BoardWidget(
            boards_frame, 'Поле противника',
            clickable=True, on_click=self._player_shot
        )

        # привязываем клик по своему полю для режима расстановки
        for r in range(SIZE):
            for c in range(SIZE):
                self.player_widget.buttons[(r, c)].config(
                    command=lambda row=r, col=c: self._player_board_click(row, col)
                )

        # легенда цветов под полями
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
            activebackground='#3a4468', command=self._new_game
        ).pack(side=tk.LEFT, padx=8)

        self.undo_btn = tk.Button(
            controls, text='Отменить ход', bg='#2e3650', fg=COLOR_UNDO,
            font=('Arial', 10, 'bold'), relief='flat', padx=16, pady=6,
            activebackground='#3a4468', command=self._undo_shot
        )
        self.undo_btn.pack(side=tk.LEFT, padx=8)

        # строка с оставшимися кораблями противника
        self.stats_var = tk.StringVar(value='')
        tk.Label(
            self.root, textvariable=self.stats_var,
            bg=COLOR_BG, fg='#7a8caa', font=('Arial', 9)
        ).pack(pady=(0, 14))

    def _reset_board_widgets(self, player_clickable=False):
        """Сбрасывает визуальное состояние обоих полей в пустое.
        принимает: player_clickable - bool - кликабельно ли поле игрока
        возвращает: None
        """
        for r in range(SIZE):
            for c in range(SIZE):
                self.player_widget.set_cell(r, c, 'empty')
                self.enemy_widget.set_cell(r, c, 'empty')

                # настройка поля игрока
                p_state  = 'normal'  if player_clickable else 'disabled'
                p_cursor = 'hand2'   if player_clickable else 'arrow'
                # настройка поля противника — инвертированная
                e_state  = 'disabled' if player_clickable else 'normal'
                e_cursor = 'arrow'    if player_clickable else 'hand2'

                self.player_widget.buttons[(r, c)].config(state=p_state, cursor=p_cursor)
                self.enemy_widget.buttons[(r, c)].config(state=e_state, cursor=e_cursor)

        # сбрасываем запомненные зоны потопленных кораблей
        self.player_widget.sunk_zones.clear()
        self.enemy_widget.sunk_zones.clear()

    def _new_game(self):
        """Сбрасывает состояние и начинает новую партию.
        принимает: нет
        возвращает: None
        """
        # отменяем запланированный ход компьютера, если он ещё не выполнился
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.computer_thinking = False
        self.placement_controller = None
        self.player_board_click_enabled = False

        # спрашиваем: ручная расстановка или случайная
        manual = messagebox.askyesno(
            'Расстановка кораблей',
            'Хотите расставить корабли вручную?'
        )

        if manual:
            self._start_manual_setup()
            return

        # случайная расстановка — сразу начинаем игру
        self.game.setup()
        self._reset_board_widgets(player_clickable=False)

        # показываем корабли игрока на его поле
        for r in range(SIZE):
            for c in range(SIZE):
                if self.game.player_board[r][c] == SHIP:
                    self.player_widget.set_cell(r, c, 'ship')

        self.status_var.set('Ваш ход — выберите клетку поля противника')
        self.undo_btn.config(state='normal')
        self._update_stats_label()

    def _start_manual_setup(self):
        """Запускает режим ручной расстановки кораблей.
        принимает: нет
        возвращает: None
        """
        self.game = Game()
        self.placement_controller = PlacementController()
        self.player_board_click_enabled = True

        # своё поле кликабельно, поле противника — нет
        self._reset_board_widgets(player_clickable=True)

        next_ship = self.placement_controller.get_next_ship_length()
        self.status_var.set(
            f'Ручная расстановка. Поставьте корабль длины {next_ship}. R — поворот.'
        )
        self.undo_btn.config(state='disabled')
        self._update_stats_label()

    def _toggle_placement_orientation(self, event=None):
        """Переключает ориентацию корабля (горизонталь ↔ вертикаль).
        принимает: event - tk.Event | None
        возвращает: None
        """
        # работает только во время расстановки
        if self.placement_controller is None:
            return

        self.placement_controller.toggle_orientation()
        next_ship   = self.placement_controller.get_next_ship_length()
        orientation = 'горизонтально' if self.placement_controller.horizontal else 'вертикально'
        self.status_var.set(
            f'Ручная расстановка. Поставьте корабль длины {next_ship} ' 
            f'({orientation}). R — поворот.'
        )

    def _player_board_click(self, row, col):
        """Обрабатывает клик по полю игрока во время ручной расстановки.
        принимает: row - int, col - int
        возвращает: None
        """
        # игнорируем клик вне режима расстановки
        if not self.player_board_click_enabled or self.placement_controller is None:
            return

        placed_cells = self.placement_controller.place_ship(row, col)

        # если корабль не влез — сообщаем и ждём другого клика
        if not placed_cells:
            self.status_var.set('Нельзя поставить корабль в эту позицию.')
            return

        # закрашиваем поставленный корабль
        for r, c in placed_cells:
            self.player_widget.set_cell(r, c, 'ship')

        # все корабли расставлены — запускаем игру
        if self.placement_controller.is_finished():
            self.game.setup(self.placement_controller.board)
            self.placement_controller = None
            self.player_board_click_enabled = False
            for r in range(SIZE):
                for c in range(SIZE):
                    self.player_widget.buttons[(r, c)].config(state='disabled', cursor='arrow')
                    self.enemy_widget.buttons[(r, c)].config(state='normal', cursor='hand2')
            self.status_var.set('Ваш ход — выберите клетку поля противника')
            self.undo_btn.config(state='normal')
            self._update_stats_label()
            return

        # предлагаем поставить следующий корабль
        next_ship   = self.placement_controller.get_next_ship_length()
        orientation = 'горизонтально' if self.placement_controller.horizontal else 'вертикально'
        self.status_var.set(
            f'Поставлено. Теперь корабль длины {next_ship} ({orientation}). R — поворот.'
        )

    def _player_shot(self, row, col):
        """Обрабатывает выстрел игрока по полю компьютера.
        принимает: row - int, col - int
        возвращает: None
        """
        # блокируем клики пока компьютер думает или идёт расстановка
        if self.computer_thinking or self.placement_controller is not None:
            return

        btn = self.enemy_widget.buttons[(row, col)]
        if btn.cget('state') == 'disabled':
            return

        shot_result = self.game.player_shoot(row, col)
        result = shot_result['result']

        if result in ('hit', 'sunk'):
            # попадание — закрашиваем клетку и блокируем её
            self.enemy_widget.set_cell(row, col, 'hit')
            btn.config(state='disabled')

            if result == 'sunk':
                # корабль потоплен — закрашиваем зону вокруг него
                zone = shot_result['zone']
                self.enemy_widget.mark_sunk_zone(zone)
                for r, c in zone:
                    self.enemy_widget.buttons[(r, c)].config(state='disabled', cursor='arrow')
                self.status_var.set('Корабль потоплен! Стреляйте ещё.')
            else:
                self.status_var.set('Попадание! Продолжайте ходить.')

            if shot_result['game_over']:
                self._end_game(winner='player')
                return

        else:
            # промах — ход переходит компьютеру через 700 мс
            self.enemy_widget.set_cell(row, col, 'miss')
            btn.config(state='disabled')
            self.status_var.set('Промах. Ход компьютера...')
            self.computer_thinking = True
            self.undo_btn.config(state='disabled')
            self.after_id = self.root.after(700, self._computer_shot)
            return

        # обновляем счётчик оставшихся кораблей после хода игрока
        self._update_stats_label()

    def _undo_shot(self):
        """Отменяет последний выстрел игрока и восстанавливает визуал.
        принимает: нет
        возвращает: None
        """
        if self.computer_thinking or self.placement_controller is not None:
            return

        result = self.game.undo_player_shot()
        if result is None:
            self.status_var.set('Нет ходов для отмены.')
            return

        row, col, _ = result
        self.status_var.set(f'Ход отменён ({row + 1}, {col + 1}). Стреляйте снова.')
        self._restore_enemy_visual_state()
        self._update_stats_label()

    def _restore_enemy_visual_state(self):
        """Перерисовывает поле противника по текущим данным игры.
        принимает: нет
        возвращает: None
        """
        state  = self.game.get_enemy_visual_state()
        hits   = state['hits']
        misses = state['misses']
        zones  = state['zones']

        self.enemy_widget.sunk_zones.clear()

        for r in range(SIZE):
            for c in range(SIZE):
                btn = self.enemy_widget.buttons[(r, c)]
                pos = (r, c)

                if pos in hits:
                    self.enemy_widget.set_cell(r, c, 'hit')
                    btn.config(state='disabled', cursor='arrow')
                elif pos in misses:
                    self.enemy_widget.set_cell(r, c, 'miss')
                    btn.config(state='disabled', cursor='arrow')
                elif pos in zones:
                    self.enemy_widget.set_cell(r, c, 'zone')
                    btn.config(state='disabled', cursor='arrow')
                else:
                    # клетка не тронута — разблокируем
                    self.enemy_widget.set_cell(r, c, 'empty')
                    btn.config(state='normal', cursor='hand2')

        self.enemy_widget.sunk_zones.update(zones)

    def _computer_shot(self):
        """Выполняет ход компьютера и обновляет поле игрока.
        принимает: нет
        возвращает: None
        """
        self.after_id = None
        shot_result = self.game.computer_shoot()
        row    = shot_result['row']
        col    = shot_result['col']
        result = shot_result['result']

        if result in ('hit', 'sunk'):
            self.player_widget.set_cell(row, col, 'hit')
            self.root.update_idletasks()  # сразу показываем попадание

            if result == 'sunk':
                self.player_widget.mark_sunk_zone(shot_result['zone'])
                self.root.update_idletasks()
                self.status_var.set('Компьютер потопил ваш корабль!')
            else:
                self.status_var.set('Компьютер попал! Снова ход компьютера...')

            if shot_result['game_over']:
                self.computer_thinking = False
                self._end_game(winner='computer')
                return

            # компьютер ходит снова через 800 мс
            self.after_id = self.root.after(800, self._computer_shot)

        else:
            # промах — возвращаем ход игроку
            self.player_widget.set_cell(row, col, 'miss')
            self.root.update_idletasks()
            self.status_var.set('Компьютер промахнулся. Ваш ход!')
            self.computer_thinking = False
            self.undo_btn.config(state='normal')

    def _update_stats_label(self):
        """Обновляет строку с оставшимися кораблями противника.
        принимает: нет
        возвращает: None
        """
        remaining = self.game.get_remaining_enemy_ships()
        if remaining:
            ships_str = '  '.join(f'[{s}]' for s in remaining)
            self.stats_var.set(f'Осталось кораблей:  {ships_str}')
        else:
            self.stats_var.set('Все корабли противника потоплены!')

    def _end_game(self, winner):
        """Завершает партию: блокирует поле и показывает итоговое окно.
        принимает: winner - str: 'player' или 'computer'
        возвращает: None
        """
        self.enemy_widget.disable_all()
        self.undo_btn.config(state='disabled')

        if winner == 'player':
            self.status_var.set('🏆 Вы победили!')
            msg   = 'Поздравляем! Вы потопили все корабли!'
            color = COLOR_WIN
        else:
            self.status_var.set('💀 Компьютер победил')
            msg   = 'Компьютер потопил все ваши корабли.\nПопробуйте ещё раз!'
            color = COLOR_LOSE

        # всплывающее окно с результатом
        popup = tk.Toplevel(self.root)
        popup.title('Игра окончена')
        popup.configure(bg=COLOR_SURFACE)
        popup.resizable(False, False)
        popup.grab_set()  # блокируем основное окно пока открыт popup

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
    """Запускает tkinter-приложение.
    принимает: нет
    возвращает: None
    """
    root = tk.Tk()
    SeaBattleApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()