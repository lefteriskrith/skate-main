import math


def on_jump(game, _event) -> None:
    if game.on_ground and game.running:
        game.on_ground = False
        game.player_vy = game.JUMP_VELOCITY
        game.air_trick_used = False
        game.trick_label = ""


def on_down_press(game, _event) -> None:
    # Air-only trick: kickflip.
    if not game.on_ground and game.running:
        # Allow down-trigger even if another trick was queued; this makes input reliable.
        game.air_trick_used = True
        game.trick_label = "Kickflip"
        game.flip_remaining = 360.0
        game.player_vy -= 110.0


def on_left_press(game, _event) -> None:
    # Left acts as brake on ground, backflip trigger in air.
    if not game.on_ground and game.running and not game.air_trick_used:
        game.air_trick_used = True
        game.trick_label = "Backflip"
        game.board_pitch_remaining = 360.0
        game.rider_pitch_remaining = 360.0
        game.player_vy -= 120.0
        return
    game.left_pressed = True


def on_left_release(game, _event) -> None:
    game.left_pressed = False


def on_right_press(game, _event) -> None:
    # Right acts as accelerate on ground, 180 trigger in air.
    if not game.on_ground and game.running and not game.air_trick_used:
        game.air_trick_used = True
        game.trick_label = "180 Turn"
        game.board_yaw_remaining = 180.0
        game.rider_yaw_remaining = 180.0
        game.player_vy -= 70.0
        return
    game.right_pressed = True


def on_right_release(game, _event) -> None:
    game.right_pressed = False


def advance_angle(angle: float, remaining: float, rate: float, dt: float) -> tuple[float, float]:
    """Advance an angle toward a finite target span at fixed rate."""
    if remaining <= 0:
        return angle, 0.0
    step = min(remaining, rate * dt)
    return (angle + step) % 360, remaining - step


def update_player(game, dt: float) -> None:
    # Vertical motion and trick state are updated in one place to avoid drift.
    if not game.on_ground:
        game.player_vy += game.GRAVITY * dt
        game.player_y += game.player_vy * dt

        floor_y = game.GROUND_Y - game.PLAYER_H
        if game.player_y >= floor_y:
            game.player_y = floor_y
            game.player_vy = 0.0
            game.on_ground = True
            game.air_trick_used = False
            game.trick_label = ""
            game.flip_angle = 0.0
            game.flip_remaining = 0.0
            game.board_yaw_angle = 0.0
            game.board_yaw_remaining = 0.0
            game.board_pitch_angle = 0.0
            game.board_pitch_remaining = 0.0
            game.rider_yaw_angle = 0.0
            game.rider_yaw_remaining = 0.0
            game.rider_pitch_angle = 0.0
            game.rider_pitch_remaining = 0.0

    game.flip_angle, game.flip_remaining = advance_angle(
        game.flip_angle, game.flip_remaining, game.KICKFLIP_RATE, dt
    )
    game.board_yaw_angle, game.board_yaw_remaining = advance_angle(
        game.board_yaw_angle, game.board_yaw_remaining, game.TURN180_RATE, dt
    )
    game.rider_yaw_angle, game.rider_yaw_remaining = advance_angle(
        game.rider_yaw_angle, game.rider_yaw_remaining, game.TURN180_RATE, dt
    )
    game.board_pitch_angle, game.board_pitch_remaining = advance_angle(
        game.board_pitch_angle, game.board_pitch_remaining, game.BACKFLIP_RATE, dt
    )
    game.rider_pitch_angle, game.rider_pitch_remaining = advance_angle(
        game.rider_pitch_angle, game.rider_pitch_remaining, game.BACKFLIP_RATE, dt
    )


def rotate_point(x: float, y: float, cx: float, cy: float, angle_deg: float) -> tuple[float, float]:
    """Rotate point (x, y) around center (cx, cy) by degrees."""
    if abs(angle_deg) < 0.0001:
        return x, y
    rad = math.radians(angle_deg)
    dx = x - cx
    dy = y - cy
    return (
        cx + dx * math.cos(rad) - dy * math.sin(rad),
        cy + dx * math.sin(rad) + dy * math.cos(rad),
    )
