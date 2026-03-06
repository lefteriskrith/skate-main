"""Game package exports.

Desktop runtime exposes ``SkateGame`` from ``core`` (tkinter-based). Android
runtime imports submodules like ``game.config`` and should not require tkinter.
"""

try:
    # Desktop path.
    from .core import SkateGame
except ModuleNotFoundError:
    # Android build does not ship tkinter; keep package importable.
    SkateGame = None
