import random
import tkinter as tk
from tkinter import messagebox

from game import _all_ships_sunk, EMPTY, Game, HIT, MISS, SHIP, SIZE  #импорт логики игры и констант

#цвета и настройки интерфейса
COLOR_BG = '#1a1f2e'  #цвет фона всего окна
COLOR_SURFACE = '#242938'  #цвет фона всплывающих окон
COLOR_EMPTY = '#2e3650'  #цвет пустой клетки поля
COLOR_EMPTY_HVR = '#3a4468'  #цвет пустой клетки при наведении мыши
COLOR_SHIP = '#7f8a04'  #цвет клетки с кораблём игрока
COLOR_HIT = '#871407'  #цвет клетки с попаданием
COLOR_MISS = '#6c7a9c'  #цвет клетки с промахом
COLOR_SUNK_ZONE = '#6c7a9c' #цвет зазора вокруг потопленного корабля
COLOR_TEXT = '#e8eaf0'  #цвет основного текста (светло-серый)
COLOR_ACCENT = '#4fc3f7'  #цвет акцентных элементов — заголовков, кнопок (голубой)
COLOR_WIN = '#43e97b'  #цвет текста при победе игрока (зелёный)
COLOR_LOSE = '#e63946'  #цвет текста при поражении (красный)

CELL = 44  #размер одной клетки в пикселях, используется для расчёта размеров
PAD = 6  #отступ между клетками в пикселях


def _find_ship_cells(board, row, col):
    """
    находит все клетки корабля, которому принадлежит указанная клетка
    :param board:
    :param row:
    :param col:
    :return: список клеток корабля
    """
    cells = [(row, col)]  #начинаем обход с клетки, в которую попали
    for r, c in cells:  #итерируемся по уже найденным клеткам
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:  #проверяем, что сосед не выходит за границы поля
                if board[nr][nc] == HIT and (nr, nc) not in cells:  #если сосед тоже подбит и ещё не в списке, добавляем его
                    cells.append((nr, nc))
    return cells  #возвращаем все клетки корабля


def _is_ship_sunk(board, ship_cells):
    """
    проверяет, полностью ли потоплен корабль (нет ли уцелевших клеток рядом)
    :param board:
    :param ship_cells:
    :return:
    """
    for r, c in ship_cells:  #перебираем все клетки корабля
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == SHIP:  #если рядом есть живая часть корабля, возвращаем false, что корабль ещё не потоплен
                return False
    return True  #иначе вернём обратное


def _get_zone_around(ship_cells):
    """
    возвращает клетки-зазор вокруг корабля (которые не заняты самим кораблем)
    :param ship_cells:
    :return:
    """
    ship_set = set(ship_cells)  #множество клеток корабля для быстрой проверки
    zone = set()  #результирующее множество клеток-зазора
    for r, c in ship_cells:  #перебираем каждую клетку корабля
        for dr in range(-1, 2): #смещение по строке
            for dc in range(-1, 2):  #смещение по столбцу, все 8 соседей плюс сама клетка
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE and (nr, nc) not in ship_set:
                    zone.add((nr, nc))
    return zone  #возвращаем все клетки вокруг корабля


class BoardWidget:
    """
    виджет игрового поля, сетка кнопок с подсветкой и поддержкой hover
    """
    def __init__(self, parent, title, clickable, on_click=None):
        """
        создаёт фрейм с заголовком и сеткой клеток
        :param parent:
        :param title:
        :param clickable:
        :param on_click:
        """
        self.clickable = clickable  #можно ли кликать по клеткам
        self.on_click = on_click  #внешний обработчик клика
        self.buttons = {}  #словарь для доступа к любой клетке по координатам
        self.sunk_zones = set()  #множество координат клеток-зазора вокруг потопленных кораблей

        frame = tk.Frame(parent, bg=COLOR_BG)  #контейнер для заголовка и сетки
        frame.pack(side=tk.LEFT, padx=18)

        tk.Label(frame, text=title, bg=COLOR_BG, fg=COLOR_ACCENT, font=('Arial', 12, 'bold')).pack(pady=(0, 8))  #заголовок над полем

        grid = tk.Frame(frame, bg=COLOR_BG)  #фрейм для сетки клеток
        grid.pack()

        tk.Label(grid, text='', bg=COLOR_BG, width=2).grid(row=0, column=0)  #пустая ячейка пересечения заголовков
        for i in range(SIZE):
            tk.Label(grid, text=str(i + 1), bg=COLOR_BG, fg='#7a8caa', font=('Arial', 9), width=3).grid(row=0, column=i + 1)
            tk.Label(grid, text=str(i + 1), bg=COLOR_BG, fg='#7a8caa', font=('Arial', 9), width=2).grid(row=i + 1, column=0)

        for r in range(SIZE):
            for c in range(SIZE):
                btn = tk.Button(
                    grid, width=2, height=1, bg=COLOR_EMPTY, bd=0, relief='flat',
                    cursor='hand2' if clickable else 'arrow',
                    activebackground=COLOR_EMPTY_HVR
                )
                btn.grid(row=r + 1, column=c + 1, padx=2, pady=2)  #размещаем кнопку в сетке
                self.buttons[(r, c)] = btn  #сохраняем ссылку на кнопку по её координатам

                if clickable:
                    btn.bind('<Enter>', lambda e, b=btn, p=(r, c): self._hover(b, p, True))  #подсветка при наведении мыши
                    btn.bind('<Leave>', lambda e, b=btn, p=(r, c): self._hover(b, p, False))
                    btn.config(command=lambda row=r, col=c: self._click(row, col))  #обработчик клика с захватом текущих r, c

    def _hover(self, btn, pos, entering):
        """
        подсвечивает клетку при наведении, если она ещё не обстреляна
        :param btn:
        :param pos:
        :param entering:
        :return:
        """
        if btn.cget('bg') in (COLOR_HIT, COLOR_MISS, COLOR_SHIP, COLOR_SUNK_ZONE):  #проверка подсветки
            return
        btn.config(bg=COLOR_EMPTY_HVR if entering else COLOR_EMPTY)  #делаем светлее при входе

    def _click(self, row, col):
        """
        передаёт клик во внешний обработчик
        :param row:
        :param col:
        :return:
        """
        if self.on_click:  #проверяем, задан ли внешний обработчик
            self.on_click(row, col)  #передаём координаты клика

    def set_cell(self, row, col, state):
        """
        обновляет цвет клетки по её состоянию
        :param row:
        :param col:
        :param state:
        :return:
        """
        colors = {  #набор цветов для разных состояний клетки
            'ship':  COLOR_SHIP,  #корабль игрока
            'hit':   COLOR_HIT,  #попадание
            'miss':  COLOR_MISS,  #промах
            'zone':  COLOR_SUNK_ZONE,  #зазор
            'empty': COLOR_EMPTY  # пустая клетка
        }
        self.buttons[(row, col)].config(bg=colors.get(state, COLOR_EMPTY))  #устанавливаем цвет

    def mark_sunk_zone(self, zone_cells):
        """
        закрашивает клетки-зазор вокруг потопленного корабля
        :param zone_cells:
        :return:
        """
        for r, c in zone_cells:  #перебираем все клетки зазора
            if self.buttons[(r, c)].cget('bg') != COLOR_HIT:  #не перекрашиваем клетки с попаданием
                self.set_cell(r, c, 'zone')  #красим клетку в цвет зазора
        self.sunk_zones.update(zone_cells)

    def disable_all(self):
        """
        отключает клики по всему полю
        :return:
        """
        for btn in self.buttons.values():
            btn.config(state='disabled', cursor='arrow')


class SeaBattleApp:
    """
    класс главного окна приложения
    """
    def __init__(self, root):
        """
        инициализирует окно, создаёт игру и строит интерфейс
        :param root:
        """
        self.root = root
        self.root.title('Морской бой')
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.game = Game()
        self._after_id = None

        self._build_ui()
        self._new_game()

    def _build_ui(self):
        """
        строит все виджеты интерфейса
        :return:
        """
        header = tk.Frame(self.root, bg=COLOR_BG)  #фрейм для заголовка приложения
        header.pack(pady=(18, 4))
        tk.Label(header, text='⚓  МОРСКОЙ БОЙ', bg=COLOR_BG, fg=COLOR_ACCENT, font=('Arial', 18, 'bold')).pack()

        self.status_var = tk.StringVar(value='Новая игра...')  #переменная для строки статуса
        tk.Label(self.root, textvariable=self.status_var, bg=COLOR_BG, fg=COLOR_TEXT, font=('Arial', 11), height=2).pack()

        boards_frame = tk.Frame(self.root, bg=COLOR_BG)  #контейнер для игровых полей
        boards_frame.pack(padx=20, pady=8)

        self.player_widget = BoardWidget(boards_frame, 'Ваше поле', clickable=False)
        self.enemy_widget = BoardWidget(boards_frame, 'Поле противника', clickable=True, on_click=self._player_shot)

        legend = tk.Frame(self.root, bg=COLOR_BG)  #фрейм для легенды цветов
        legend.pack(pady=6)
        legend_items = [
            (COLOR_SHIP, 'Ваш корабль'),
            (COLOR_HIT, 'Попадание'),
            (COLOR_MISS, 'Промах'),
            (COLOR_SUNK_ZONE, 'Зона затопления (убит)')
        ]
        for color, label in legend_items:  #рисуем каждый элемент легенды
            dot = tk.Frame(legend, bg=color, width=14, height=14)
            dot.pack(side=tk.LEFT, padx=(10, 3))
            tk.Label(legend, text=label, bg=COLOR_BG, fg='#7a8caa', font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 6))

        controls = tk.Frame(self.root, bg=COLOR_BG)  #фрейм для кнопок управления и счётчика
        controls.pack(pady=(8, 18))
        tk.Button(
            controls, text='Новая игра', bg='#2e3650', fg=COLOR_ACCENT,
            font=('Arial', 10, 'bold'), relief='flat', padx=16, pady=6,
            activebackground='#3a4468', command=self._new_game  #по нажатию сбросить и начать заново
        ).pack(side=tk.LEFT, padx=8)

        self.turn_var = tk.StringVar(value='')  #переменная для строки выстрелы/точность
        tk.Label(controls, textvariable=self.turn_var, bg=COLOR_BG, fg='#7a8caa', font=('Arial', 10)).pack(side=tk.LEFT, padx=8)

    def _new_game(self):
        """
        сбрасывает состояние и начинает новую партию
        :return:
        """
        if self._after_id:  #если есть запланированный ход компьютера, отменяем его, чтобы не сломать новую игру
            self.root.after_cancel(self._after_id)
            self._after_id = None

        self.game.setup()  #пересоздаём доски и случайно расставляем корабли для обоих игроков
        self.shots = 0
        self.player_shots = 0
        self.hits = 0

        for r in range(SIZE):  #перебираем строки и столбцы поля
            for c in range(SIZE):
                cell = self.game.player_board[r][c]
                self.player_widget.set_cell(r, c, 'ship' if cell == SHIP else 'empty')
                self.enemy_widget.set_cell(r, c, 'empty')
                self.enemy_widget.buttons[(r, c)].config(state='normal', cursor='hand2')

        self.player_widget.sunk_zones.clear()  #очищаем зазоры предыдущей игры на поле игрока и компьютера
        self.enemy_widget.sunk_zones.clear()
        self.status_var.set('Ваш ход -- выберите клетку поля противника')
        self.turn_var.set('Ход 1')  #сбрасываем счётчик ходов

    def _player_shot(self, row, col):
        """
        обрабатывает выстрел игрока по клетке поля компьютера
        :param row:
        :param col:
        :return:
        """
        board = self.game.computer_board  #ссылка на скрытое поле компьютера
        btn = self.enemy_widget.buttons[(row, col)]  #кнопка, по которой кликнул игрок

        if btn.cget('state') == 'disabled':  #если клетка уже обстреляна или заблокирована — игнорируем
            return

        self.shots += 1  #увеличиваем общий счётчик выстрелов и счётчик выстрелов игрока
        self.player_shots += 1
        cell = board[row][col]  #смотрим, что находится в выбранной клетке

        if cell == SHIP:  #если игрок попал в корабль
            board[row][col] = HIT
            self.hits += 1
            self.enemy_widget.set_cell(row, col, 'hit')
            btn.config(state='disabled')

            ship_cells = _find_ship_cells(board, row, col)  #находим все клетки подбитого корабля и проверяем, потоплен ли корабль целиком
            if _is_ship_sunk(board, ship_cells):
                zone = _get_zone_around(ship_cells)  #вычисляем зазор вокруг потопленного корабля
                self.enemy_widget.mark_sunk_zone(zone)
                for r, c in zone:
                    self.enemy_widget.buttons[(r, c)].config(state='disabled', cursor='arrow')  #блокируем зазор
                self.status_var.set('Корабль потоплен! Стреляйте ещё.')
            else:
                self.status_var.set('Попадание! Продолжайте ходить.')  #если корабль ранен, но не потоплен, то ход остаётся у игрока

            if _all_ships_sunk(board):  #проверяем, не осталось ли вражеских кораблей
                self._end_game(winner='player')
                return
        else:  #если игрок промахнулся
            board[row][col] = MISS
            self.enemy_widget.set_cell(row, col, 'miss')
            btn.config(state='disabled')
            self.status_var.set('Промах. Ход компьютера...')
            self._update_turn_label()
            self._after_id = self.root.after(700, self._computer_shot)
            return

        self._update_turn_label()  #обновляем счётчик выстрелов и точности после хода игрока

    def _computer_shot(self):
        """
        выполняет ход компьютера, выбирает клетку и обновляет поле игрока
        :return:
        """
        self._after_id = None

        board = self.game.player_board  #ссылка на поле игрока
        targets = self.game.computer_targets  #очередь приоритетных целей (соседи подбитых клеток)

        if not targets.is_empty():  # есть приоритетные цели, то бьём по ним
            row, col = targets.dequeue()
            while board[row][col] in (HIT, MISS):
                if targets.is_empty():  #если очередь закончилась, то переходим к случайному выстрелу
                    row, col = self._random_shot_on_player()
                    break
                row, col = targets.dequeue()  #берём следующую цель
        else:
            row, col = self._random_shot_on_player()  #если нет приоритетов, то стреляем случайно

        cell = board[row][col]  #содержимое выбранной клетки
        self.shots += 1

        if cell == SHIP:  #если компьютер попал в корабль игрока
            board[row][col] = HIT
            self.player_widget.set_cell(row, col, 'hit')

            ship_cells = _find_ship_cells(board, row, col)
            if _is_ship_sunk(board, ship_cells):  #проверяем, потоплен ли корабль
                zone = _get_zone_around(ship_cells)
                self.player_widget.mark_sunk_zone(zone)
                self.status_var.set('Компьютер потопил ваш корабль!')
            else:
                self.status_var.set('Компьютер попал! Снова ход компьютера...')  #если корабль ранен, компьютер ходит ещё
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] not in (HIT, MISS):  #если сосед в границах поля и не обстрелян
                        targets.enqueue((nr, nc))  #добавляем соседа как приоритетную цель

            if _all_ships_sunk(board):  #если все корабли игрока потоплены
                self._end_game(winner='computer')
                return

            self._after_id = self.root.after(800, self._computer_shot)
        else:  #если промах компьютера
            board[row][col] = MISS
            self.player_widget.set_cell(row, col, 'miss')
            self.status_var.set('Компьютер промахнулся. Ваш ход!')

        self._update_turn_label()  #обновляем счётчик выстрелов после хода компьютера

    def _random_shot_on_player(self):
        """
        выбирает случайную необстрелянную клетку поля игрока
        :return:
        """
        board = self.game.player_board  #ссылка на поле игрока
        while True:  #ищем подходящую клетку
            r = random.randint(0, SIZE - 1)
            c = random.randint(0, SIZE - 1)
            if board[r][c] not in (HIT, MISS):
                return r, c  #возвращаем её координаты

    def _update_turn_label(self):
        """
        обновляет счётчик ходов и точность игрока
        :return:
        """
        acc = f'{self.hits / self.player_shots * 100:.0f}%' if self.player_shots else '—'  #считаем точность
        self.turn_var.set(f'Выстрелов: {self.shots}  |  Точность: {acc}')  #обновляем строку под кнопкой

    def _end_game(self, winner):
        """
        завершает партию, блокирует поле и показывает итог
        :param winner:
        :return:
        """
        self.enemy_widget.disable_all()  #блокируем поле врага
        if winner == 'player':  #определяем победителя
            self.status_var.set('🏆 Вы победили!')
            msg = f'Поздравляем! Вы потопили все корабли!\nВыстрелов: {self.shots}  |  Попаданий: {self.hits}'  # итоговая статистика
            color = COLOR_WIN
        else:
            self.status_var.set('💀 Компьютер победил')
            msg = 'Компьютер потопил все ваши корабли.\nПопробуйте ещё раз!'
            color = COLOR_LOSE

        popup = tk.Toplevel(self.root)  #создаём всплывающее окно поверх главного
        popup.title('Игра окончена')
        popup.configure(bg=COLOR_SURFACE)
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text=msg, bg=COLOR_SURFACE, fg=color, font=('Arial', 12, 'bold'), pady=20, padx=30).pack()  # текст итога с отступами
        tk.Button(
            popup, text='Новая игра', bg='#2e3650', fg=COLOR_ACCENT, font=('Arial', 10, 'bold'),
            relief='flat', padx=14, pady=6,
            command=lambda: (popup.destroy(), self._new_game())  #закрываем попап и сразу запускаем новую игру
        ).pack(pady=(0, 16))


def main():
    """
    запускает tkinter-приложение
    :return:
    """
    root = tk.Tk()  #создаём главное окно tkinter
    SeaBattleApp(root)  #создаём приложение
    root.mainloop()

if __name__ == '__main__':
    main()