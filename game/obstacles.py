import random


def spawn_initial_obstacles(game) -> None:
    # Fill the first screen span so gameplay starts immediately.
    for _ in range(5):
        spawn_obstacle(game)


def spawn_obstacle(game) -> None:
    # Mix several obstacle archetypes for more varied runs.
    kind_roll = random.random()
    if kind_roll < 0.18:
        kind = "stairs"
    elif kind_roll < 0.43:
        kind = "cone"
    elif kind_roll < 0.62:
        kind = "barrier"
    elif kind_roll < 0.80:
        kind = "barrel"
    else:
        kind = "block"

    if kind == "stairs":
        width = random.randint(120, 190)
        height = random.randint(38, 66)
        steps = random.randint(4, 6)
        # Give stairs a bit more room so they read clearly before contact.
        gap = random.randint(game.OBSTACLE_MIN_GAP + 80, game.OBSTACLE_MAX_GAP + 140)
    elif kind == "cone":
        width = random.randint(24, 36)
        height = random.randint(30, 46)
        steps = 0
        gap = random.randint(game.OBSTACLE_MIN_GAP - 90, game.OBSTACLE_MAX_GAP - 150)
    elif kind == "barrier":
        width = random.randint(84, 128)
        height = random.randint(40, 58)
        steps = 0
        gap = random.randint(game.OBSTACLE_MIN_GAP - 20, game.OBSTACLE_MAX_GAP - 40)
    elif kind == "barrel":
        width = random.randint(34, 48)
        height = random.randint(44, 66)
        steps = 0
        gap = random.randint(game.OBSTACLE_MIN_GAP - 70, game.OBSTACLE_MAX_GAP - 120)
    else:
        width = random.randint(30, 60)
        height = random.randint(32, 72)
        steps = 0
        gap = random.randint(game.OBSTACLE_MIN_GAP, game.OBSTACLE_MAX_GAP)

    game.obstacles.append(
        {
            "x": float(game.next_obstacle_x),
            "w": float(width),
            "h": float(height),
            "passed": 0.0,
            "kind": kind,
            "steps": steps,
        }
    )
    game.next_obstacle_x += gap


def update_obstacles(game, dt: float) -> None:
    # Obstacles are recycled by spawn/remove to keep list size bounded.
    shift = game.scroll_speed * dt
    for obstacle in game.obstacles:
        # Move left based on world speed.
        obstacle["x"] -= shift

        # Mark once when obstacle fully passes player (reserved for future use).
        if obstacle["passed"] == 0.0 and obstacle["x"] + obstacle["w"] < game.PLAYER_X:
            obstacle["passed"] = 1.0

    # Remove elements that are fully off-screen.
    game.obstacles = [o for o in game.obstacles if o["x"] + o["w"] > -30]

    # Keep a stable pool size so spacing remains predictable.
    while len(game.obstacles) < 6:
        spawn_obstacle(game)
