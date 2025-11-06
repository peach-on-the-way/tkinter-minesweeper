import tkinter as tk
from tkinter import messagebox
import random
import solver
import time

font = ("Courier", 20, "bold")

dpos = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
cell_number_colors = [
    "blue",
    "green",
    "red",
    "navy",
    "firebrick",
    "darkturquoise",
    "black",
    "darkgray",
]

cell_content_bomb = "💣"
cell_content_bomb_exploded = "💥"
cell_content_flag = "🚩"
cell_content_flag_wrong = "❌"

class Board(tk.Frame):
    def __init__(self, master, board_size, mines, cell_size):
        super().__init__(master)
        self.board_size = board_size
        self.mines = mines
        self.cell_size = cell_size
        self.board_generated = False
        self.initialize_cell_buttons()
        self.interaction_enabled = True

    def reset(self):
        for column in self.cell_buttons:
            for button in column:
                button.destroy()
        self.board_generated = False
        self.initialize_cell_buttons()

    def initialize_board_data(self):
        self.exploded = False
        self.cells_revealed = set()
        self.cells_flagged_locations = set()
        self.cells_grid_flagged = [[False for i in range(self.board_size)] for i in range(self.board_size)]
        self.cells_grid_info = [[0 for i in range(self.board_size)] for i in range(self.board_size)]
        self.cells_unrevealed = { (x, y) for x in range(self.board_size) for y in range(self.board_size)}
        self.mine_locations = set()

    def setup_grid_info(self):
        for x, y in self.mine_locations:
            for dx, dy in dpos:
                test_x = x + dx
                test_y = y + dy
                if not 0 <= test_x < self.board_size or not 0 <= test_y < self.board_size:
                    continue
                if not type(self.cells_grid_info[test_x][test_y]) is int:
                    continue

                self.cells_grid_info[test_x][test_y] += 1

    def generate_random_board(self):
        self.initialize_board_data()
        for _ in range(self.mines):
            mine_x = random.randint(0, self.board_size - 1)
            mine_y = random.randint(0, self.board_size - 1)
            self.cells_grid_info[mine_x][mine_y] = '*'
            self.mine_locations.add((mine_x, mine_y))
        self.setup_grid_info()

    def setup_custom_board(self, mine_locations=None, cells_to_reveal=None, cells_to_flag=None):
        self.initialize_board_data()
        if mine_locations:
            self.mine_locations = set(mine_locations)
            for x, y in self.mine_locations:
                self.cells_grid_info[x][y] = '*'
        self.setup_grid_info()
        if cells_to_reveal:
            for pos in cells_to_reveal:
                board.reveal_cell(*pos)
        if cells_to_flag:
            for pos in cells_to_flag:
                board.cell_flag(*pos)

    def initialize_cell_buttons(self):
        self.cell_buttons = []
        for x in range(self.board_size):
            column = []
            for y in range(self.board_size):
                # Make button square
                cell_button_frame = tk.Frame(
                    self,
                    width=self.cell_size,
                    height=self.cell_size,
                )
                cell_button_frame.grid_propagate(False) # Prevent the frame from resizing
                cell_button_frame.grid_columnconfigure(0, weight=1) # Allows the button to fill the frame
                cell_button_frame.grid_rowconfigure(0, weight=1)
                cell_button_frame.grid(column=x, row=y, sticky=tk.NSEW)

                cell_button = tk.Button(
                    cell_button_frame,
                    font=font,
                    highlightthickness=0,
                )
                cell_button.configure(command=self.on_cell_left_clicked(x, y))
                cell_button.bind("<Button-3>", self.on_cell_right_clicked(x, y))
                cell_button.grid(column=0, row=0, sticky=tk.NSEW)
                column.append(cell_button_frame)
            self.cell_buttons.append(column)

    def button_at(self, x, y):
        if not (0 <= x < self.board_size \
            and 0 <= y < self.board_size):
            return None

        return self.cell_buttons[x][y].winfo_children()[0]

    def pos_inside_board(self, x, y):
        return 0 <= x < self.board_size and 0 <= y < self.board_size

    def cell_is_revealed(self, x, y):
        return (x, y) in self.cells_revealed

    def cell_is_empty(self, x, y):
        return self.cells_grid_info[x][y] == 0

    def cell_is_number(self, x, y):
        val = self.cells_grid_info[x][y]
        if not isinstance(val, int):
            return False
        return 1 >= val >= 8

    def cell_is_bomb(self, x, y):
        return self.cells_grid_info[x][y] == "*"

    def cell_is_flagged(self, x, y):
        return self.cells_grid_flagged[x][y]

    def show_cell_button(self, x, y):
        if self.cell_is_empty(x, y):
            if self.cell_is_flagged(x, y):
                self.button_at(x, y).config(
                    text=cell_content_flag,
                )
        elif self.cell_is_bomb(x, y):
            if self.cell_is_flagged(x, y):
                self.button_at(x, y).config(
                    text=cell_content_flag,
                )
            else:
                color = "black"
                self.button_at(x, y).config(
                    text=cell_content_bomb,
                    disabledforeground=color,
                    foreground=color
                )
        else:
            if self.cell_is_flagged(x, y):
                self.button_at(x, y).config(
                    text=cell_content_flag_wrong,
                    foreground="red",
                    disabledforeground="red",
                )
            else:
                color = cell_number_colors[self.cells_grid_info[x][y] - 1]
                content = str(self.cells_grid_info[x][y]) 
                self.button_at(x, y).config(
                    text=content,
                    disabledforeground=color,
                    foreground=color
                )

    def reveal_cell(self, x, y):
        if (x, y) in self.cells_revealed:
            return

        self.cells_unrevealed.remove((x, y))
        self.cells_revealed.add((x, y))
        if self.cell_is_empty(x, y) and not self.cell_is_flagged(x, y):
            for dx, dy in dpos:
                testx = x + dx
                testy = y + dy
                if 0 <= testx < self.board_size \
                    and 0 <= testy < self.board_size \
                    and type(self.cells_grid_info[testx][testy]) is int:
                    self.reveal_cell(testx, testy)

        self.button_at(x, y).config(
            relief=tk.SUNKEN,
            state=tk.DISABLED,
        )

        if self.cell_is_empty(x, y):
            pass
        elif self.cell_is_bomb(x, y):
            self.button_at(x, y).config(
                text=cell_content_bomb_exploded,
                disabledforeground="black",
                background="red"
            )
        else:
            self.button_at(x, y).config(
                text=str(self.cells_grid_info[x][y]),
                disabledforeground=cell_number_colors[self.cells_grid_info[x][y] - 1]
            )
        self.cells_revealed.add((x, y))

    def reveal_all(self):
        for x in range(self.board_size):
            for y in range(self.board_size):
                if (x, y) in self.cells_revealed:
                    continue

                self.show_cell_button(x, y)
                self.button_at(x, y).config(
                    state=tk.DISABLED
                )

    def find_number_cells_adjacent_to_unrevealed_cell(self):
        cells = set()
        for mine_x, mine_y in self.mine_locations:
            for dx, dy in dpos:
                testx = mine_x + dx
                testy = mine_y + dy
                if not self.pos_inside_board(testx, testy) \
                    or not self.cell_is_revealed(testx, testy) \
                    or (testx, testy) in self.mine_locations:
                    continue

                number_cell_x, number_cell_y = testx, testy
                for dx, dy in dpos:
                    testx = number_cell_x + dx
                    testy = number_cell_y + dy
                    if not self.cell_is_revealed(testx, testy):
                        continue
                    cells.add((number_cell_x, number_cell_y))
                    break
        return cells


    def cell_flag_without_event(self, x, y):
        if (x, y) in self.cells_revealed or self.exploded:
            return
        self.button_at(x, y).config(text=cell_content_flag, state=tk.DISABLED)
        self.cells_grid_flagged[x][y] = True
        self.cells_flagged_locations.add((x, y))
        

    def cell_flag(self, x, y):
        self.cell_flag_without_event(x, y)
        self.event_generate("<<CellFlagged>>")

    def cell_unflag(self, x, y):
        if (x, y) in self.cells_revealed or self.exploded:
            return
        self.button_at(x, y).config(text="", state=tk.NORMAL)
        self.cells_grid_flagged[x][y] = False
        self.cells_flagged_locations.remove((x, y))
        self.event_generate("<<CellUnflagged>>")


    def on_cell_left_clicked(self, x, y):
        def on_cell_left_clicked_inner():
            if not self.interaction_enabled:
                return

            # Attempts til giving up generating good start
            attempts = 1000
            while not self.board_generated:
                self.generate_random_board()
                attempts -= 1
                if not self.cell_is_empty(x, y) and attempts > 0:
                    continue
                self.board_generated = True
                self.event_generate("<<BoardGenerated>>")
                break

            if self.cells_grid_info[x][y] == "*":
                self.reveal_cell(x, y)
                self.reveal_all()
                self.event_generate("<<CellExploded>>")
                self.exploded = True
            else: 
                self.reveal_cell(x, y)
                self.event_generate("<<CellRevealed>>")

        return on_cell_left_clicked_inner

    def on_cell_right_clicked(self, x, y):
        def on_cell_right_clicked_inner(event):
            if not self.interaction_enabled:
                return
            if not self.board_generated \
                or (x, y) in self.cells_revealed \
                or self.exploded:
                return
            if self.cells_grid_flagged[x][y]:
                self.cell_unflag(x, y)
            else:
                self.cell_flag(x, y)
        return on_cell_right_clicked_inner


def update_mines_left_label(args):
    mines_left = len(board.mine_locations) - len(board.cells_flagged_locations)
    mines_left_str.set(f"{mines_left} mines left")

def check_board_completed(args):
    if len(board.mine_locations) == len(board.cells_flagged_locations) \
        and len(board.cells_revealed) == board.board_size * board.board_size - len(board.mine_locations):
        messagebox.showinfo("Game completed", "All mines found!")
        board.interaction_enabled = False

def exploded(args):
    messagebox.showwarning("Game over", "You activated a mine...")

def reset():
    board.reset()
    mines_left_str.set(f"? mines left")
    board.interaction_enabled = True

def solve_once():
    if not board.board_generated or board.exploded:
        return
    
    result = solver.solve_once(board)
    if result == None:
        print("Cannot solve")
        return

    for cell, is_mine in result.items():
        if not board.board_generated or board.exploded:
            break

        x, y = cell
        if is_mine:
            board.cell_flag_without_event(x, y)
        else:
            if not board.exploded:
                board.reveal_cell(x, y)
            if board.cells_grid_info[x][y] == "*":
                board.reveal_all()
                board.exploded = True
                break

    if board.exploded:
        board.event_generate("<<CellExploded>>")
    board.event_generate("<<CellFlagged>>")

def solve_all():
    while True:
        result = solver.solve_once(board)
        if result == None:
            print("Solve all finished")
            return
        if not board.board_generated or board.exploded:
            return
        
        for cell, is_mine in result.items():
            x, y = cell
            if is_mine:
                board.cell_flag_without_event(x, y)
            else:
                if not board.exploded:
                    board.reveal_cell(x, y)
                if board.cells_grid_info[x][y] == "*":
                    board.reveal_all()
                    board.exploded = True

        if board.exploded:
            board.event_generate("<<CellExploded>>")
        board.event_generate("<<CellFlagged>>")

# Preemptively load caches for common cases
for neighbors_count in range(1, 8):
    for mines_count in range(1, neighbors_count + 1):
        solver.load_cache(neighbors_count, mines_count)

root = tk.Tk()

top_bar = tk.Frame()
top_bar.grid(column=0, row=0)
top_bar.grid_columnconfigure(0, weight=1)
top_bar.grid_columnconfigure(1, weight=1)

mines_left_str = tk.StringVar()
mines_left_str.set("? mines left")
mines_left_label = tk.Label(top_bar, textvariable=mines_left_str, font=font)
mines_left_label.grid(column=0, row=0)

reset_button = tk.Button(top_bar, text="Reset", font=font, command=reset)
reset_button.grid(column=1, row=0)

board = Board(root, 9, 9, 70)
board.grid(column=0, row=1)

board.bind("<<BoardGenerated>>", update_mines_left_label)
board.bind("<<CellFlagged>>", update_mines_left_label)
board.bind("<<CellUnflagged>>", update_mines_left_label)

board.bind("<<BoardGenerated>>", check_board_completed, True)
board.bind("<<CellFlagged>>", check_board_completed, True)
board.bind("<<CellUnflagged>>", check_board_completed, True)
board.bind("<<CellRevealed>>", check_board_completed, True)

board.bind("<<CellExploded>>", exploded)

root.mainloop()
