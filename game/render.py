import math

from .player import rotate_point


def draw_background(game) -> None:
    # Layered sky + hills + road stripes.
    game.canvas.create_rectangle(0, 0, game.WIDTH, game.HEIGHT, fill="#c9d3db", width=0)
    game.canvas.create_rectangle(0, 270, game.WIDTH, game.HEIGHT, fill="#9eaab3", width=0)
    game.canvas.create_rectangle(0, game.GROUND_Y, game.WIDTH, game.HEIGHT, fill="#6f7569", width=0)

    x_shift = -game.hills_offset
    for base_x in (x_shift - game.WIDTH, x_shift, x_shift + game.WIDTH):
        game.canvas.create_oval(base_x - 230, 210, base_x + 210, 490, fill="#7f8f9b", width=0)
        game.canvas.create_oval(base_x + 150, 220, base_x + 620, 500, fill="#77848f", width=0)
        game.canvas.create_oval(base_x + 510, 215, base_x + 1020, 510, fill="#6f7a85", width=0)

    # Rough skyline silhouette to avoid flat/vector look.
    skyline_y = 300
    bx = -((game.hills_offset * 0.7) % 220)
    while bx < game.WIDTH + 220:
        w = 70 + int((bx * 0.13) % 40)
        h = 70 + int((bx * 0.21) % 90)
        x1 = bx
        x2 = bx + w
        y1 = skyline_y - h
        game.canvas.create_rectangle(x1, y1, x2, skyline_y, fill="#656f78", outline="")
        game.canvas.create_rectangle(x1 + 8, y1 + 10, x2 - 8, y1 + 14, fill="#7f8b95", width=0)
        bx += w + 16

    stripe_w = 92
    x = -game.road_offset
    while x < game.WIDTH:
        game.canvas.create_rectangle(
            x,
            game.GROUND_Y + 36,
            x + 48,
            game.GROUND_Y + 44,
            fill="#a8ab9a",
            width=0,
        )
        x += stripe_w

    # Dirt/stain strips for a grimier environment.
    grime_x = -game.grime_offset
    while grime_x < game.WIDTH:
        game.canvas.create_oval(
            grime_x + 10,
            game.GROUND_Y + 10,
            grime_x + 55,
            game.GROUND_Y + 28,
            fill="#55584f",
            outline="",
        )
        game.canvas.create_oval(
            grime_x + 35,
            game.GROUND_Y + 18,
            grime_x + 90,
            game.GROUND_Y + 34,
            fill="#4b4f47",
            outline="",
        )
        grime_x += 85

    # Subtle grain dots for a dirtier visual style.
    for i in range(56):
        gx = int((i * 173 + game.grime_offset * 4) % game.WIDTH)
        gy = 180 + int((i * 97) % 250)
        shade = "#707870" if i % 2 == 0 else "#646b64"
        game.canvas.create_rectangle(gx, gy, gx + 2, gy + 2, fill=shade, width=0)


def draw_obstacles(game) -> None:
    # Obstacle rendering is intentionally stylized and low-detail.
    for obstacle in game.obstacles:
        x1 = obstacle["x"]
        y1 = game.GROUND_Y - obstacle["h"]
        x2 = obstacle["x"] + obstacle["w"]
        y2 = game.GROUND_Y
        kind = obstacle.get("kind", "block")

        game.canvas.create_rectangle(x1 - 2, y2 - 2, x2 + 2, y2 + 4, fill="#4b5147", width=0)
        if kind == "stairs":
            steps = int(obstacle.get("steps", 5))
            step_w = max(18, (x2 - x1) / steps)
            for i in range(steps):
                sx1 = x1 + i * step_w
                sx2 = x1 + (i + 1) * step_w
                step_h = obstacle["h"] * (1 - (i / (steps + 1)))
                sy1 = y2 - step_h
                game.canvas.create_rectangle(sx1, sy1, sx2, y2, fill="#5e6369", outline="#454a50", width=1)
                game.canvas.create_line(sx1 + 3, sy1 + 5, sx2 - 3, sy1 + 5, fill="#777d84", width=1)
        else:
            game.canvas.create_rectangle(x1, y1, x2, y2, fill="#575d64", outline="#43484f", width=2)
            game.canvas.create_rectangle(x1 + 5, y1 + 6, x2 - 5, y1 + 11, fill="#757c85", width=0)


def draw_player(game) -> None:
    # Board/rider are drawn from current trick angles.
    px = game.PLAYER_X
    py = game.player_y

    board_center_x = px + game.PLAYER_W / 2
    board_center_y = py + game.PLAYER_H - 12
    deck_len = 100
    wheel_r = 7

    roll_rad = math.radians(game.flip_angle if not game.on_ground else 0.0)
    yaw_rad = math.radians(game.board_yaw_angle if not game.on_ground else 0.0)
    yaw_face = max(0.30, abs(math.cos(yaw_rad)))
    thickness = 5.2 + 1.6 * abs(math.cos(roll_rad))
    tilt = 4 * math.sin(roll_rad)
    underside = math.cos(roll_rad) < 0
    half_len = deck_len * yaw_face / 2

    deck_x1 = board_center_x - half_len
    deck_x2 = board_center_x + half_len
    deck_top = board_center_y - thickness / 2
    deck_bottom = board_center_y + thickness / 2
    deck_color = "#4d71a6" if not underside else "#2b3f5c"
    edge_color = "#314a6a"

    # Nose/tail are lifted upward on both sides.
    lift = 10
    board_pts = [
        (deck_x1 + 10, deck_top + tilt),
        (deck_x2 - 10, deck_top - tilt),
        (deck_x2, board_center_y - lift - tilt),
        (deck_x2 - 10, deck_bottom - tilt),
        (deck_x1 + 10, deck_bottom + tilt),
        (deck_x1, board_center_y - lift + tilt),
    ]
    flat_pts: list[float] = []
    for x, y in board_pts:
        rx, ry = rotate_point(x, y, board_center_x, board_center_y, game.board_pitch_angle)
        flat_pts.extend((rx, ry))
    game.canvas.create_polygon(flat_pts, fill=deck_color, outline=edge_color, width=2)

    if yaw_face > 0.33:
        # Wheels follow board pitch in air and snap to floor on ground.
        wheel_cy = deck_bottom + wheel_r + 1
        if game.on_ground and abs(game.board_pitch_angle) < 1:
            wheel_cy = game.GROUND_Y - wheel_r + 1
        ltx = deck_x1 + max(16, (deck_x2 - deck_x1) * 0.24)
        rtx = deck_x2 - max(16, (deck_x2 - deck_x1) * 0.24)
        ltx, lty = rotate_point(ltx, wheel_cy, board_center_x, board_center_y, game.board_pitch_angle)
        rtx, rty = rotate_point(rtx, wheel_cy, board_center_x, board_center_y, game.board_pitch_angle)
        game.canvas.create_oval(ltx - wheel_r, lty - wheel_r, ltx + wheel_r, lty + wheel_r, fill="#253547", width=0)
        game.canvas.create_oval(rtx - wheel_r, rty - wheel_r, rtx + wheel_r, rty + wheel_r, fill="#253547", width=0)

    rider_dir = -1 if math.cos(math.radians(game.rider_yaw_angle)) < 0 else 1
    left_ankle_x = deck_x1 + max(14, (deck_x2 - deck_x1) * 0.30)
    right_ankle_x = deck_x2 - max(14, (deck_x2 - deck_x1) * 0.30)
    ankle_y = deck_top - 2
    hip_y = py + 14
    shoulder_y = hip_y - 30
    head_center_y = shoulder_y - 16
    body_color = "#5f8ac9" if game.running else "#7b7b7b"

    left_hip_x = px + (39 - 9 * rider_dir)
    right_hip_x = px + (39 + 9 * rider_dir)
    left_knee_x = left_hip_x - 4
    right_knee_x = right_hip_x + 4
    knee_y = hip_y + 16

    lhip = rotate_point(left_hip_x, hip_y, board_center_x, board_center_y, game.rider_pitch_angle)
    lknee = rotate_point(left_knee_x, knee_y, board_center_x, board_center_y, game.rider_pitch_angle)
    lankle = rotate_point(left_ankle_x, ankle_y, board_center_x, board_center_y, game.rider_pitch_angle)
    rhip = rotate_point(right_hip_x, hip_y, board_center_x, board_center_y, game.rider_pitch_angle)
    rknee = rotate_point(right_knee_x, knee_y, board_center_x, board_center_y, game.rider_pitch_angle)
    rankle = rotate_point(right_ankle_x, ankle_y, board_center_x, board_center_y, game.rider_pitch_angle)

    game.canvas.create_line(lhip[0], lhip[1], lknee[0], lknee[1], lankle[0], lankle[1], fill="#334155", width=5)
    game.canvas.create_line(rhip[0], rhip[1], rknee[0], rknee[1], rankle[0], rankle[1], fill="#334155", width=5)

    torso_l = rotate_point(px + 24, shoulder_y, board_center_x, board_center_y, game.rider_pitch_angle)
    torso_r = rotate_point(px + 56, shoulder_y, board_center_x, board_center_y, game.rider_pitch_angle)
    torso_br = rotate_point(px + 56, hip_y, board_center_x, board_center_y, game.rider_pitch_angle)
    torso_bl = rotate_point(px + 24, hip_y, board_center_x, board_center_y, game.rider_pitch_angle)
    game.canvas.create_polygon(
        torso_l[0],
        torso_l[1],
        torso_r[0],
        torso_r[1],
        torso_br[0],
        torso_br[1],
        torso_bl[0],
        torso_bl[1],
        fill=body_color,
        outline="",
    )
    head = rotate_point(px + 40, head_center_y + 2, board_center_x, board_center_y, game.rider_pitch_angle)
    game.canvas.create_oval(head[0] - 15, head[1] - 14, head[0] + 15, head[1] + 16, fill="#ffe0cc", width=0)
    # Simple cap: dome + brim.
    game.canvas.create_oval(head[0] - 13, head[1] - 15, head[0] + 13, head[1] - 4, fill="#2d2f33", width=0)
    game.canvas.create_rectangle(head[0] + 5, head[1] - 8, head[0] + 18, head[1] - 5, fill="#2d2f33", width=0)
    la = rotate_point(px + 27, shoulder_y + 8, board_center_x, board_center_y, game.rider_pitch_angle)
    lb = rotate_point(px + 11, shoulder_y + 22, board_center_x, board_center_y, game.rider_pitch_angle)
    ra = rotate_point(px + 53, shoulder_y + 8, board_center_x, board_center_y, game.rider_pitch_angle)
    rb = rotate_point(px + 67, shoulder_y + 20, board_center_x, board_center_y, game.rider_pitch_angle)
    game.canvas.create_line(la[0], la[1], lb[0], lb[1], fill=body_color, width=4)
    game.canvas.create_line(ra[0], ra[1], rb[0], rb[1], fill=body_color, width=4)


def draw_hud(game) -> None:
    # HUD stays minimal to avoid cluttering animation readability.
    controls = "Up: Jump | Left: Slow (air: Backflip) | Right: Speed Up (air: 180) | Down (air): Kickflip | R: Restart"
    game.canvas.create_text(18, 18, text=controls, fill="#1f2d3a", font=("Segoe UI", 11), anchor="nw")

    if game.trick_label:
        game.canvas.create_text(
            18,
            40,
            text=f"Trick: {game.trick_label}",
            fill="#2c4d6a",
            font=("Segoe UI", 11, "bold"),
            anchor="nw",
        )

    if not game.running:
        game.canvas.create_rectangle(220, 160, 740, 350, fill="#ffffff", outline="#9fb2c8", width=3)
        game.canvas.create_text(480, 215, text="You crashed!", fill="#243444", font=("Segoe UI", 28, "bold"))
        game.canvas.create_text(480, 258, text=f"Final score: {game.score}", fill="#32485f", font=("Segoe UI", 18))
        game.canvas.create_text(480, 300, text="Press R to play again", fill="#47627b", font=("Segoe UI", 14))
