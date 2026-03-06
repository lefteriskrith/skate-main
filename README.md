# Soft Skate Run

A small Python `tkinter` skate game prototype with simple tricks, obstacle dodging, and a modular project structure.

## Run

```powershell
python skate_game.py
```

## Syntax Check (`py_compile`)

```powershell
# Compile all Python files to bytecode (syntax validation only).
python -m py_compile `
  skate_game.py `
  game\__init__.py game\config.py game\core.py game\main.py `
  game\obstacles.py game\player.py game\render.py
```

## Controls

- `Up`: jump
- `Left`: slow down on ground, `Backflip` in air
- `Right`: speed up on ground, `180 Turn` in air
- `Down`: `Kickflip` in air
- `R`: reset run

## Architecture

```text
skate_game.py (entrypoint)
  -> game/main.py (startup)
      -> game/core.py (game loop + state + input wiring)
          -> game/player.py (movement + trick state updates)
          -> game/obstacles.py (spawn/update obstacle list)
          -> game/render.py (draw background/player/obstacles/hud)
          -> game/config.py (all constants/tuning)
```

## File Overview

- `skate_game.py`: backward-compatible launcher
- `game/config.py`: single place for dimensions, speeds, gravity, trick rates
- `game/core.py`: `SkateGame` class and frame update orchestration
- `game/player.py`: jump/trick handlers and player physics updates
- `game/obstacles.py`: obstacle generation and scrolling lifecycle
- `game/render.py`: all canvas rendering functions
- `game/main.py`: creates window and starts main loop

## Notes

- The game loop uses `dt` clamping for more stable physics on frame drops.
- Rendering and update logic are separated so gameplay tweaks do not require canvas code edits.
- Trick timing can be adjusted in `game/config.py` (`KICKFLIP_RATE`, `TURN180_RATE`, `BACKFLIP_RATE`).
