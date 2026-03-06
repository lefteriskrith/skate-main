import tkinter as tk

from .core import SkateGame


def main() -> None:
    # Create top-level window.
    root = tk.Tk()
    # Build game object (it starts its own tick loop in __init__).
    SkateGame(root)
    # Hand control to Tk event loop.
    root.mainloop()
