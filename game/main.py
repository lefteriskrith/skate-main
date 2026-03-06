import os
import sys
import tkinter as tk

from .core import SkateGame


def _resolve_asset(*parts: str) -> str:
    # Support both normal run and PyInstaller onefile extraction dir.
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    return os.path.join(base, *parts)


def main() -> None:
    # Create top-level window.
    root = tk.Tk()
    try:
        root.iconbitmap(_resolve_asset("assets", "skaterush_logo.ico"))
    except Exception:
        # Non-critical: game can still run without custom icon.
        pass
    # Build game object (it starts its own tick loop in __init__).
    SkateGame(root)
    # Hand control to Tk event loop.
    root.mainloop()
