import math

from .player import rotate_point


def draw_background(game) -> None:
    # Layered sky + hills + road.
    # Base color bands (sky, midground, ground).
    game.canvas.create_rectangle(0, 0, game.WIDTH, game.HEIGHT, fill="#b8c5d1", width=0)
    game.canvas.create_rectangle(0, 250, game.WIDTH, game.HEIGHT, fill="#7f8a95", width=0)
    game.canvas.create_rectangle(0, game.GROUND_Y, game.WIDTH, game.HEIGHT, fill="#5e665c", width=0)

    # Soft cloud groups.
    clouds = [
        (130, 96, 88),
        (300, 74, 72),
        (520, 105, 94),
        (760, 82, 80),
    ]
    for cx, cy, r in clouds:
        game.canvas.create_oval(cx - r, cy - 22, cx + r, cy + 22, fill="#e5edf4", outline="")
        game.canvas.create_oval(cx - r * 0.62, cy - 36, cx + r * 0.25, cy + 8, fill="#e5edf4", outline="")
        game.canvas.create_oval(cx - r * 0.1, cy - 34, cx + r * 0.6, cy + 10, fill="#e5edf4", outline="")

    x_shift = -game.hills_offset
    # Repeat hill clusters across three wrapped regions.
    for base_x in (x_shift - game.WIDTH, x_shift, x_shift + game.WIDTH):
        game.canvas.create_oval(base_x - 230, 220, base_x + 210, 500, fill="#6e7a85", width=0)
        game.canvas.create_oval(base_x + 150, 230, base_x + 620, 510, fill="#65717c", width=0)
        game.canvas.create_oval(base_x + 510, 225, base_x + 1020, 520, fill="#5c6872", width=0)

    # Midground park strip with trees.
    game.canvas.create_rectangle(0, 292, game.WIDTH, 366, fill="#6f7b74", width=0)

    # Farther (upper) tree row: smaller trees to create depth.
    far_tree_x = -int(game.road_offset * 0.14) - 30
    while far_tree_x < game.WIDTH + 40:
        game.canvas.create_rectangle(far_tree_x + 10, 306, far_tree_x + 15, 326, fill="#4a4033", outline="")
        game.canvas.create_oval(far_tree_x, 292, far_tree_x + 24, 314, fill="#4a694a", outline="")
        game.canvas.create_oval(far_tree_x + 5, 285, far_tree_x + 28, 307, fill="#547554", outline="")
        far_tree_x += 70

    # Near tree row.
    tree_x = -int(game.road_offset * 0.22) - 40
    while tree_x < game.WIDTH + 60:
        trunk_x1 = tree_x + 16
        game.canvas.create_rectangle(trunk_x1, 322, trunk_x1 + 8, 354, fill="#4d4336", outline="")
        game.canvas.create_oval(tree_x, 294, tree_x + 40, 332, fill="#4f6f50", outline="")
        game.canvas.create_oval(tree_x + 8, 282, tree_x + 46, 320, fill="#5b7a59", outline="")
        tree_x += 96

    # Visual road profile: downhill segments, then flat again.
    def road_profile_y(world_x: float) -> float:
        # Keep visuals aligned with collision floor so skater does not appear to bob up/down.
        return game.GROUND_Y

    # Paint over road top so profile is visible without changing gameplay collisions.
    road_points: list[float] = []
    x = 0
    while x <= game.WIDTH:
        # Convert screen x to world x so moving offset affects profile.
        wx = x + game.road_offset
        road_points.extend((x, road_profile_y(wx)))
        x += 24
    road_points.extend((game.WIDTH, game.HEIGHT, 0, game.HEIGHT))
    game.canvas.create_polygon(road_points, fill="#40464d", outline="")

    # Road shoulders.
    game.canvas.create_rectangle(0, game.GROUND_Y, game.WIDTH, game.GROUND_Y + 7, fill="#596269", width=0)
    game.canvas.create_rectangle(0, game.GROUND_Y + 36, game.WIDTH, game.GROUND_Y + 44, fill="#2f353a", width=0)

    # Dashed center line.
    dash_x = -game.road_offset
    while dash_x < game.WIDTH + 50:
        game.canvas.create_rectangle(
            dash_x,
            game.GROUND_Y + 20,
            dash_x + 42,
            game.GROUND_Y + 26,
            fill="#ddd6a8",
            width=0,
        )
        dash_x += 88

    # Subtle asphalt texture.
    tex_x = -game.grime_offset
    while tex_x < game.WIDTH + 80:
        game.canvas.create_oval(tex_x + 8, game.GROUND_Y + 11, tex_x + 30, game.GROUND_Y + 18, fill="#353b41", outline="")
        game.canvas.create_oval(
            tex_x + 34,
            game.GROUND_Y + 26,
            tex_x + 62,
            game.GROUND_Y + 33,
            fill="#343a40",
            outline="",
        )
        tex_x += 74


def draw_obstacles(game) -> None:
    # Obstacle rendering is intentionally stylized and low-detail.
    for obstacle in game.obstacles:
        x1 = obstacle["x"]
        y1 = game.GROUND_Y - obstacle["h"]
        x2 = obstacle["x"] + obstacle["w"]
        y2 = game.GROUND_Y
        kind = obstacle.get("kind", "block")

        # Ground contact shadow improves depth/readability.
        game.canvas.create_oval(x1 - 6, y2 - 1, x2 + 6, y2 + 10, fill="#495047", outline="")
        if kind == "stairs":
            # Draw descending steps instead of one block.
            steps = int(obstacle.get("steps", 5))
            step_w = max(18, (x2 - x1) / steps)
            for i in range(steps):
                sx1 = x1 + i * step_w
                sx2 = x1 + (i + 1) * step_w
                step_h = obstacle["h"] * (1 - (i / (steps + 1)))
                sy1 = y2 - step_h
                game.canvas.create_rectangle(sx1, sy1, sx2, y2, fill="#606770", outline="#444b54", width=1)
                # Top lip on each stair to make shape legible at speed.
                game.canvas.create_rectangle(sx1 + 2, sy1 + 2, sx2 - 2, sy1 + 6, fill="#838b95", width=0)
                game.canvas.create_line(sx1 + 3, sy1 + 8, sx2 - 3, sy1 + 8, fill="#6f7782", width=1)
        else:
            # Draw classic box obstacle with top highlight.
            game.canvas.create_rectangle(x1, y1, x2, y2, fill="#5c636d", outline="#424a54", width=2)
            game.canvas.create_rectangle(x1 + 5, y1 + 6, x2 - 5, y1 + 12, fill="#7f8894", width=0)
            # Add a subtle side face so blocks don't look flat.
            side_w = min(8, max(4, (x2 - x1) * 0.18))
            game.canvas.create_polygon(
                x2,
                y1 + 1,
                x2 + side_w,
                y1 + 5,
                x2 + side_w,
                y2 + 1,
                x2,
                y2 - 2,
                fill="#49505a",
                outline="",
            )


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
    # Yaw controls visible board length (foreshortening).
    yaw_face = max(0.30, abs(math.cos(yaw_rad)))
    # Kickflip is a roll around the deck's long axis:
    # keep deck length, vary only visible thickness/underside.
    roll_face = max(0.10, abs(math.cos(roll_rad)))
    thickness = 1.6 + 6.2 * roll_face
    tilt = 0.0
    underside = math.cos(roll_rad) < 0
    half_len = deck_len * yaw_face / 2
    # Small "flick drop" makes kickflip read more natural.
    board_center_y += 7.0 * (1.0 - abs(math.cos(roll_rad)))

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
        # Wheels are attached to the deck and must follow kickflip roll too.
        roll_cos = math.cos(roll_rad)
        wheel_mount = thickness / 2 + wheel_r + 1
        wheel_cy = board_center_y + wheel_mount * roll_cos
        # Make wheels look thinner when board is edge-on during the flip.
        visible_wheel_r = max(2.0, wheel_r * max(0.25, abs(roll_cos)))
        if game.on_ground and abs(game.board_pitch_angle) < 1:
            wheel_cy = game.GROUND_Y - wheel_r + 1
            visible_wheel_r = wheel_r
        ltx = deck_x1 + max(16, (deck_x2 - deck_x1) * 0.24)
        rtx = deck_x2 - max(16, (deck_x2 - deck_x1) * 0.24)
        ltx, lty = rotate_point(ltx, wheel_cy, board_center_x, board_center_y, game.board_pitch_angle)
        rtx, rty = rotate_point(rtx, wheel_cy, board_center_x, board_center_y, game.board_pitch_angle)
        game.canvas.create_oval(
            ltx - visible_wheel_r,
            lty - visible_wheel_r,
            ltx + visible_wheel_r,
            lty + visible_wheel_r,
            fill="#253547",
            width=0,
        )
        game.canvas.create_oval(
            rtx - visible_wheel_r,
            rty - visible_wheel_r,
            rtx + visible_wheel_r,
            rty + visible_wheel_r,
            fill="#253547",
            width=0,
        )

    rider_dir = -1 if math.cos(math.radians(game.rider_yaw_angle)) < 0 else 1
    # Build a simple stick-figure skeleton, then rotate it by rider pitch.
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
    title_x = game.WIDTH - 72
    title_y = 18
    logo_cx = title_x
    logo_cy = 66

    def make_board_points(angle_deg: float) -> list[float]:
        # Build a tiny board shape and rotate it around logo center.
        half_len = 30
        half_w = 6
        local = [
            (-half_len + 6, -half_w),
            (half_len - 6, -half_w),
            (half_len, 0),
            (half_len - 6, half_w),
            (-half_len + 6, half_w),
            (-half_len, 0),
        ]
        rad = math.radians(angle_deg)
        c = math.cos(rad)
        s = math.sin(rad)
        pts: list[float] = []
        for lx, ly in local:
            x = logo_cx + lx * c - ly * s
            y = logo_cy + lx * s + ly * c
            pts.extend((x, y))
        return pts

    game.canvas.create_polygon(make_board_points(40), fill="#2a394f", outline="#1a2533", width=2)
    game.canvas.create_polygon(make_board_points(-40), fill="#476589", outline="#1a2533", width=2)
    game.canvas.create_oval(logo_cx - 6, logo_cy - 6, logo_cx + 6, logo_cy + 6, fill="#1a2533", width=0)
    game.canvas.create_text(
        title_x,
        title_y,
        text="Skate Rush",
        fill="#18222c",
        font=("Segoe UI", 12, "bold"),
        anchor="n",
    )

    controls = (
        "Up: Jump | Left: Souza (air: Backflip) | Right: Brositni Souza (air: 180) "
        "| Down (air): Kickflip | R: Restart"
    )
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


def draw_menu(game) -> None:
    # Modal overlay used at boot and when Escape is pressed.
    game.canvas.create_rectangle(0, 0, game.WIDTH, game.HEIGHT, fill="#111722", stipple="gray50", width=0)
    panel_x1, panel_y1, panel_x2, panel_y2 = 190, 70, 770, 470
    game.canvas.create_rectangle(panel_x1, panel_y1, panel_x2, panel_y2, fill="#e6edf4", outline="#556274", width=3)
    game.canvas.create_text(480, 104, text="Skate Rush", fill="#1a2633", font=("Segoe UI", 28, "bold"))
    game.menu_hitboxes = []

    if game.menu_screen == "main":
        start_label = "Resume" if game.running and game.score > 0 else "Start"
        if not game.running:
            start_label = "Restart"
        entries = [
            ("start", start_label),
            ("open_sound", "Sound"),
            ("open_tricks", "Tricks"),
        ]
        y = 172
        for idx, (_, text) in enumerate(entries):
            selected = idx == game.menu_index
            fill = "#d9e9fb" if selected else "#f2f6fa"
            border = "#3f77b6" if selected else "#9cafc2"
            x1, y1, x2, y2 = 252, y - 24, 708, y + 24
            game.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=border, width=2)
            game.canvas.create_text(480, y, text=text, fill="#1d2a38", font=("Segoe UI", 16, "bold"))
            game.menu_hitboxes.append({"rect": (x1, y1, x2, y2), "action": entries[idx][0]})
            y += 62

        game.canvas.create_text(
            480,
            430,
            text="Click or Enter on an option | Esc: close menu",
            fill="#3e4d5f",
            font=("Segoe UI", 11),
        )
        return

    if game.menu_screen == "sound":
        game.canvas.create_text(480, 156, text="Sound", fill="#1d2a38", font=("Segoe UI", 22, "bold"))
        game.canvas.create_text(480, 188, text="Use Left/Right or click - / +", fill="#3e4d5f", font=("Segoe UI", 11))

        sx1, sy1, sx2, sy2 = 292, 236, 668, 286
        game.canvas.create_rectangle(sx1, sy1, sx2, sy2, fill="#f2f6fa", outline="#9cafc2", width=2)

        bx1, by1, bx2, by2 = 318, 246, 358, 276
        game.canvas.create_rectangle(bx1, by1, bx2, by2, fill="#dfe9f3", outline="#7d8e9e", width=2)
        game.canvas.create_text((bx1 + bx2) // 2, (by1 + by2) // 2, text="-", fill="#1d2a38", font=("Segoe UI", 16, "bold"))
        game.menu_hitboxes.append({"rect": (bx1, by1, bx2, by2), "action": "sound_down"})

        px1, py1, px2, py2 = 602, 246, 642, 276
        game.canvas.create_rectangle(px1, py1, px2, py2, fill="#dfe9f3", outline="#7d8e9e", width=2)
        game.canvas.create_text((px1 + px2) // 2, (py1 + py2) // 2, text="+", fill="#1d2a38", font=("Segoe UI", 16, "bold"))
        game.menu_hitboxes.append({"rect": (px1, py1, px2, py2), "action": "sound_up"})

        bar_x = 394
        for i in range(3):
            lx1 = bar_x + i * 56
            color = "#2f7bd1" if i < game.volume_level else "#c9d5e2"
            game.canvas.create_rectangle(lx1, 248, lx1 + 36, 274, fill=color, outline="")

        back_selected = game.sound_focus == 1
        bfill = "#d9e9fb" if back_selected else "#f2f6fa"
        bborder = "#3f77b6" if back_selected else "#9cafc2"
        x1, y1, x2, y2 = 360, 360, 600, 408
        game.canvas.create_rectangle(x1, y1, x2, y2, fill=bfill, outline=bborder, width=2)
        game.canvas.create_text(480, 384, text="Back", fill="#1d2a38", font=("Segoe UI", 14, "bold"))
        game.menu_hitboxes.append({"rect": (x1, y1, x2, y2), "action": "back_main"})

        game.canvas.create_text(
            480,
            440,
            text="Enter on Back to return",
            fill="#3e4d5f",
            font=("Segoe UI", 11),
        )
        return

    # Tricks screen.
    game.canvas.create_text(480, 152, text="Tricks", fill="#1d2a38", font=("Segoe UI", 22, "bold"))
    trick_lines = [
        "Up: Jump (+1)",
        "Down in air: Kickflip (+5)",
        "Right in air: 180 Turn (+5)",
        "Down + Right in one jump: 360 Flip (+10 total)",
        "Hold Left on ground: Souza",
        "Hold Right on ground: Front Souza",
        "Souza score: +1 every 1.5 sec",
    ]
    ty = 198
    for line in trick_lines:
        game.canvas.create_text(280, ty, text=line, fill="#213346", font=("Segoe UI", 13), anchor="w")
        ty += 30

    x1, y1, x2, y2 = 360, 390, 600, 438
    game.canvas.create_rectangle(x1, y1, x2, y2, fill="#d9e9fb", outline="#3f77b6", width=2)
    game.canvas.create_text(480, 414, text="Back", fill="#1d2a38", font=("Segoe UI", 14, "bold"))
    game.menu_hitboxes.append({"rect": (x1, y1, x2, y2), "action": "back_main"})
    game.canvas.create_text(480, 446, text="Enter or click Back", fill="#3e4d5f", font=("Segoe UI", 11))
