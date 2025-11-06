# Requirements

- Python with tkinter.
- PySat, `pip install python-sat`.

# Usages

Run the game by `python game.py`

- Generate the minefield by clicking on any square in the board and the game will start immediately.
- The game will try to not generate the mine under your first click unless it's taking too long.
- Change board size by the `Size` text input field. The board is always a square.
- Change amount of mines by the `Mines` text input field. The board is not guaranteed to generate that amount of mines you've inputted but it will try.
- If you want to regenerate your board, click the `Reset` button.
- Use the `Solve Once` button to solve the board as much as possible within a single iteration. If nothing changes, it means that the solver gives up.
- Use the `Solve All` button to keep solving until it no longer can solve or the board is done.
- Delay toggle button is used to introduce artificial delay for the solver for extra excitement.

- Recommends to see the solver running at board size 30 and with 100-200 mines. 


