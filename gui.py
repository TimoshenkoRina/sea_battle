import tkinter as tk
from tkinter import messagebox

from game import *

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
    """Виджет игрового поля"""

    def __init__(self, parent, title, clickable, on_click=None):
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
                    btn.bind('<Enter>', lambda e, b=btn, p=(r, c): self.hover(b, p, True))
                    btn.bind('<Leave>', lambda e, b=btn, p=(r, c): self.hover(b, p, False))
                    btn.config(command=lambda row=r, col=c: self.click(row, col))

    def hover(self, btn, pos, entering):
        """Подсвечивает клетку при наведении, если она ещё не обстреляна"""
        if btn.cget('bg') in (COLOR_HIT, COLOR_MISS, COLOR_SHIP, COLOR_SUNK_ZONE):
            return
        btn.config(bg=COLOR_EMPTY_HVR if entering else COLOR_EMPTY)

    def click(self, row, col):
        """Передаёт клик во внешний обработчик"""
        if self.on_click:
            self.on_click(row, col)

    def set_cell(self, row, col, state):
        """Обновляет цвет клетки по её состоянию"""
        colors = {
            'ship': COLOR_SHIP,
            'hit': COLOR_HIT,
            'miss': COLOR_MISS,
            'zone': COLOR_SUNK_ZONE,
            'empty': COLOR_EMPTY,
        }
        self.buttons[(row, col)].config(bg=colors.get(state, COLOR_EMPTY))

    def mark_sunk_zone(self, zone_cells):
        """Закрашивает клетки вокруг потопленного корабля"""
        for r, c in zone_cells:
            if self.buttons[(r, c)].cget('bg') != COLOR_HIT:
                self.set_cell(r, c, 'zone')
        self.sunk_zones.update(zone_cells)

    def disable_all(self):
        """Отключает клики по всему полю"""
        for btn in self.buttons.values():
            btn.config(state='disabled', cursor='arrow')


class SeaBattleApp:
    """Класс главного окна приложения"""

    def __init__(self, root):
        self.root = root
        self.root.title('Морской бой')
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.game = Game()
        self.after_id = None
        self.computer_thinking = False
        self.placement_controller = None
        self.player_board_click_enabled = False
        self.win_image = None

        self.build_ui()
        self.root.bind('<r>', self.toggle_placement_orientation)
        self.root.bind('<R>', self.toggle_placement_orientation)
        self.new_game()

    def build_ui(self):
        """Строит все виджеты интерфейса"""
        header = tk.Frame(self.root, bg=COLOR_BG)
        header.pack(pady=(18, 4))
        tk.Label(
            header, text='МОРСКОЙ БОЙ', bg=COLOR_BG, fg=COLOR_ACCENT,
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
            clickable=True, on_click=self.player_shot
        )

        for r in range(SIZE):
            for c in range(SIZE):
                self.player_widget.buttons[(r, c)].config(
                    command=lambda row=r, col=c: self.player_board_click(row, col)
                )

        legend = tk.Frame(self.root, bg=COLOR_BG)
        legend.pack(pady=6)
        for color, label in [
            (COLOR_SHIP, 'Ваш корабль'),
            (COLOR_HIT, 'Попадание'),
            (COLOR_MISS, 'Промах'),
        ]:
            tk.Frame(legend, bg=color, width=14, height=14).pack(side=tk.LEFT, padx=(10, 3))
            tk.Label(
                legend, text=label, bg=COLOR_BG, fg='#7a8caa', font=('Arial', 9)
            ).pack(side=tk.LEFT, padx=(0, 6))

        controls = tk.Frame(self.root, bg=COLOR_BG)
        controls.pack(pady=(8, 4))

        tk.Button(
            controls, text='Новая игра', bg='#2e3650', fg=COLOR_ACCENT,
            font=('Arial', 10, 'bold'), relief='flat', padx=16, pady=6,
            activebackground='#3a4468', command=self.new_game
        ).pack(side=tk.LEFT, padx=8)

        self.undo_btn = tk.Button(
            controls, text='Отменить ход', bg='#2e3650', fg=COLOR_UNDO,
            font=('Arial', 10, 'bold'), relief='flat', padx=16, pady=6,
            activebackground='#3a4468', command=self.undo_shot
        )
        self.undo_btn.pack(side=tk.LEFT, padx=8)

        self.stats_var = tk.StringVar(value='')
        tk.Label(
            self.root, textvariable=self.stats_var,
            bg=COLOR_BG, fg='#7a8caa', font=('Arial', 9)
        ).pack(pady=(0, 14))

    def reset_board_widgets(self, player_clickable=False):
        """Сбрасывает визуальное состояние обоих полей"""
        for r in range(SIZE):
            for c in range(SIZE):
                self.player_widget.set_cell(r, c, 'empty')
                self.enemy_widget.set_cell(r, c, 'empty')
                p_state = 'normal' if player_clickable else 'disabled'
                p_cursor = 'hand2' if player_clickable else 'arrow'
                e_state = 'disabled' if player_clickable else 'normal'
                e_cursor = 'arrow' if player_clickable else 'hand2'
                self.player_widget.buttons[(r, c)].config(state=p_state, cursor=p_cursor)
                self.enemy_widget.buttons[(r, c)].config(state=e_state, cursor=e_cursor)
        self.player_widget.sunk_zones.clear()
        self.enemy_widget.sunk_zones.clear()

    def new_game(self):
        """Сбрасывает состояние и начинает новую игру"""
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.computer_thinking = False
        self.placement_controller = None
        self.player_board_click_enabled = False

        manual = messagebox.askyesno(
            'Расстановка кораблей',
            'Хотите расставить корабли вручную?'
        )

        if manual:
            self.start_manual_setup()
            return

        self.game.setup()
        self.reset_board_widgets(player_clickable=False)
        for r in range(SIZE):
            for c in range(SIZE):
                if self.game.player_board[r][c] == SHIP:
                    self.player_widget.set_cell(r, c, 'ship')
        self.status_var.set('Ваш ход — выберите клетку поля противника')
        self.undo_btn.config(state='normal')
        self.update_stats_label()

    def start_manual_setup(self):
        """Запускает режим ручной расстановки кораблей"""
        self.game = Game()
        self.placement_controller = PlacementController()
        self.player_board_click_enabled = True

        self.reset_board_widgets(player_clickable=True)

        next_ship = self.placement_controller.get_next_ship_length()
        self.status_var.set(
            f'Ручная расстановка. Поставьте корабль длины {next_ship}. R — поворот.'
        )
        self.undo_btn.config(state='disabled')
        self.update_stats_label()

    def toggle_placement_orientation(self, event=None):
        """Переключает ориентацию корабля в режиме ручной расстановки"""
        if self.placement_controller is None:
            return
        self.placement_controller.toggle_orientation()
        next_ship = self.placement_controller.get_next_ship_length()
        orientation = 'горизонтально' if self.placement_controller.horizontal else 'вертикально'
        self.status_var.set(
            f'Ручная расстановка. Поставьте корабль длины {next_ship} '
            f'({orientation}). R — поворот.'
        )

    def player_board_click(self, row, col):
        """Обрабатывает клик по полю игрока во время ручной расстановки"""
        if not self.player_board_click_enabled or self.placement_controller is None:
            return

        placed_cells = self.placement_controller.place_ship(row, col)
        if not placed_cells:
            self.status_var.set('Нельзя поставить корабль в эту позицию.')
            return

        for r, c in placed_cells:
            self.player_widget.set_cell(r, c, 'ship')

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
            self.update_stats_label()
            return

        next_ship = self.placement_controller.get_next_ship_length()
        orientation = 'горизонтально' if self.placement_controller.horizontal else 'вертикально'
        self.status_var.set(
            f'Поставлено. Теперь корабль длины {next_ship} ({orientation}). R — поворот.'
        )

    def player_shot(self, row, col):
        """Обрабатывает выстрел игрока по клетке поля компьютера"""
        if self.computer_thinking or self.placement_controller is not None:
            return
        btn = self.enemy_widget.buttons[(row, col)]
        if btn.cget('state') == 'disabled':
            return

        shot_result = self.game.player_shoot(row, col)
        result = shot_result['result']

        if result in ('hit', 'sunk'):
            self.enemy_widget.set_cell(row, col, 'hit')
            btn.config(state='disabled')

            if result == 'sunk':
                zone = shot_result['zone']
                self.enemy_widget.mark_sunk_zone(zone)
                for r, c in zone:
                    self.enemy_widget.buttons[(r, c)].config(state='disabled', cursor='arrow')
                self.status_var.set('Корабль потоплен! Стреляйте ещё.')
            else:
                self.status_var.set('Попадание! Продолжайте ходить.')

            if shot_result['game_over']:
                self.end_game(winner='player')
                return

        else:
            self.enemy_widget.set_cell(row, col, 'miss')
            btn.config(state='disabled')
            self.status_var.set('Промах. Ход компьютера...')
            self.computer_thinking = True
            self.undo_btn.config(state='disabled')
            self.after_id = self.root.after(700, self.computer_shot)
            return

        self.update_stats_label()

    def undo_shot(self):
        """Отменяет последний выстрел игрока и восстанавливает клетку"""
        if self.computer_thinking or self.placement_controller is not None:
            return
        result = self.game.undo_player_shot()
        if result is None:
            self.status_var.set('Нет ходов для отмены.')
            return
        row, col, _ = result
        self.status_var.set(f'Ход отменён ({row + 1}, {col + 1}). Стреляйте снова.')
        self.restore_enemy_visual_state()
        self.update_stats_label()

    def restore_enemy_visual_state(self):
        """Восстанавливает состояние поля противника по данным игры"""
        state = self.game.get_enemy_visual_state()
        hits = state['hits']
        misses = state['misses']
        zones = state['zones']

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
                    self.enemy_widget.set_cell(r, c, 'empty')
                    btn.config(state='normal', cursor='hand2')

        self.enemy_widget.sunk_zones.update(zones)

    def computer_shot(self):
        """Выполняет ход компьютера и обновляет поле игрока"""
        self._after_id = None
        shot_result = self.game.computer_shoot()
        row = shot_result['row']
        col = shot_result['col']
        result = shot_result['result']

        if result in ('hit', 'sunk'):
            self.player_widget.set_cell(row, col, 'hit')
            self.root.update_idletasks()
            if result == 'sunk':
                self.player_widget.mark_sunk_zone(shot_result['zone'])
                self.root.update_idletasks()
                self.status_var.set('Компьютер потопил ваш корабль!')
            else:
                self.status_var.set('Компьютер попал! Снова ход компьютера...')

            if shot_result['game_over']:
                self.computer_thinking = False
                self.end_game(winner='computer')
                return

            self.after_id = self.root.after(800, self.computer_shot)
        else:
            self.player_widget.set_cell(row, col, 'miss')
            self.root.update_idletasks()
            self.status_var.set('Компьютер промахнулся. Ваш ход!')
            self.computer_thinking = False
            self.undo_btn.config(state='normal')

    def update_stats_label(self):
        """Обновляет строку с оставшимися кораблями противника"""
        remaining = self.game.get_remaining_enemy_ships()
        if remaining:
            ships_str = '  '.join(f'[{s}]' for s in remaining)
            self.stats_var.set(f'Осталось кораблей:  {ships_str}')
        else:
            self.stats_var.set('Все корабли противника потоплены!')

    def end_game(self, winner):
        """Завершает партию, блокирует поле и показывает итог"""
        self.enemy_widget.disable_all()
        self.undo_btn.config(state='disabled')
        if winner == 'player':
            self.status_var.set('🏆 Вы победили!')
            msg = 'Поздравляем! Вы потопили все корабли!'
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
            command=lambda: (popup.destroy(), self.new_game())
        ).pack(pady=(0, 16))


def main():
    root = tk.Tk()
    SeaBattleApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()