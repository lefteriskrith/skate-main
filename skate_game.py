"""Entry point script so the game runs with `python skate_game.py`."""

# Main game class (state + loop).
from game.core import SkateGame
# Simple launcher function that creates Tk window and starts loop.
from game.main import main


# Start only when this file is executed directly.
if __name__ == "__main__":
    main()
