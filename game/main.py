import tkinter as tk

from .core import SkateGame


def main() -> None:
    root = tk.Tk()
    SkateGame(root)
    root.mainloop()

