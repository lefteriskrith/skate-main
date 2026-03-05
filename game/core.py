import time
import tkinter as tk

from . import config as cfg
from . import obstacles, player, render


class SkateGame:
    """Main orchestrator: owns state and runs the frame loop."""
    WIDTH = cfg.WIDTH
    HEIGHT = cfg.HEIGHT
    GROUND_Y = cfg.GROUND_Y
    PLAYER_X = cfg.PLAYER_X
    PLAYER_W = cfg.PLAYER_W
    PLAYER_H = cfg.PLAYER_H
    GRAVITY = cfg.GRAVITY
    JUMP_VELOCITY = cfg.JUMP_VELOCITY
    BASE_SCROLL_SPEED = cfg.BASE_SCROLL_SPEED
    MIN_SCROLL_SPEED = cfg.MIN_SCROLL_SPEED
    MAX_SCROLL_SPEED = cfg.MAX_SCROLL_SPEED
    SLOW_ACCEL = cfg.SLOW_ACCEL
    FAST_ACCEL = cfg.FAST_ACCEL
    RETURN_ACCEL = cfg.RETURN_ACCEL
    OBSTACLE_MIN_GAP = cfg.OBSTACLE_MIN_GAP
    OBSTACLE_MAX_GAP = cfg.OBSTACLE_MAX_GAP
    KICKFLIP_RATE = cfg.KICKFLIP_RATE
    TURN180_RATE = cfg.TURN180_RATE
    BACKFLIP_RATE = cfg.BACKFLIP_RATE

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Skate Rush")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg="#d6ecff",
            highlightthickness=0,
        )
        self.canvas.pack()

        self.status = tk.StringVar(value="Score: 0")
        self.status_label = tk.Label(
            root,
            textvariable=self.status,
            font=("Segoe UI", 12, "bold"),
            bg="#f2f7fb",
            fg="#23313f",
            pady=6,
        )
        self.status_label.pack(fill="x")

        self.running = True
        self.score = 0

        self.scroll_speed = self.BASE_SCROLL_SPEED
        self.player_y = self.GROUND_Y - self.PLAYER_H
        self.player_vy = 0.0
        self.on_ground = True

        self.flip_angle = 0.0
        self.flip_remaining = 0.0
        self.board_yaw_angle = 0.0
        self.board_yaw_remaining = 0.0
        self.board_pitch_angle = 0.0
        self.board_pitch_remaining = 0.0
        self.rider_yaw_angle = 0.0
        self.rider_yaw_remaining = 0.0
        self.rider_pitch_angle = 0.0
        self.rider_pitch_remaining = 0.0
        self.air_trick_used = False
        self.trick_label = ""

        self.left_pressed = False
        self.right_pressed = False

        self.road_offset = 0.0
        self.hills_offset = 0.0
        self.grime_offset = 0.0

        self.obstacles: list[dict[str, float | str | int]] = []
        self.next_obstacle_x = self.WIDTH + 180

        obstacles.spawn_initial_obstacles(self)
        self._bind_keys()
        self.root.focus_force()

        self.last_time = time.perf_counter()
        self._tick()

    def _bind_keys(self) -> None:
        # Bind globally so controls keep working even if focus shifts to widgets.
        self.root.bind_all("<KeyPress-Up>", self._on_jump)
        self.root.bind_all("<KeyPress-Down>", self._on_down_press)
        self.root.bind_all("<KeyPress-Left>", self._on_left_press)
        self.root.bind_all("<KeyRelease-Left>", self._on_left_release)
        self.root.bind_all("<KeyPress-Right>", self._on_right_press)
        self.root.bind_all("<KeyRelease-Right>", self._on_right_release)
        self.root.bind_all("<r>", self._reset)
        self.root.bind_all("<R>", self._reset)

    def _on_jump(self, event: tk.Event) -> None:
        player.on_jump(self, event)

    def _on_down_press(self, event: tk.Event) -> None:
        player.on_down_press(self, event)

    def _on_left_press(self, event: tk.Event) -> None:
        player.on_left_press(self, event)

    def _on_left_release(self, event: tk.Event) -> None:
        player.on_left_release(self, event)

    def _on_right_press(self, event: tk.Event) -> None:
        player.on_right_press(self, event)

    def _on_right_release(self, event: tk.Event) -> None:
        player.on_right_release(self, event)

    def _reset(self, _event: tk.Event | None = None) -> None:
        # Hard reset of runtime state while keeping window/widgets alive.
        self.running = True
        self.score = 0
        self.scroll_speed = self.BASE_SCROLL_SPEED

        self.player_y = self.GROUND_Y - self.PLAYER_H
        self.player_vy = 0.0
        self.on_ground = True

        self.flip_angle = 0.0
        self.flip_remaining = 0.0
        self.board_yaw_angle = 0.0
        self.board_yaw_remaining = 0.0
        self.board_pitch_angle = 0.0
        self.board_pitch_remaining = 0.0
        self.rider_yaw_angle = 0.0
        self.rider_yaw_remaining = 0.0
        self.rider_pitch_angle = 0.0
        self.rider_pitch_remaining = 0.0
        self.air_trick_used = False
        self.trick_label = ""

        self.left_pressed = False
        self.right_pressed = False

        self.road_offset = 0.0
        self.hills_offset = 0.0
        self.grime_offset = 0.0

        self.obstacles.clear()
        self.next_obstacle_x = self.WIDTH + 180
        obstacles.spawn_initial_obstacles(self)

        self.last_time = time.perf_counter()
        self.status.set("Score: 0")

    def _approach(self, value: float, target: float, amount: float) -> float:
        if value < target:
            return min(target, value + amount)
        return max(target, value - amount)

    def _update_speed(self, dt: float) -> None:
        # Keep cruise speed stable; left/right are used for ground manuals.
        self.scroll_speed = self._approach(
            self.scroll_speed,
            self.BASE_SCROLL_SPEED,
            self.RETURN_ACCEL * dt,
        )

        self.scroll_speed = max(self.MIN_SCROLL_SPEED, min(self.MAX_SCROLL_SPEED, self.scroll_speed))

    def _update_background_motion(self, dt: float) -> None:
        # Background layers move slower than foreground for cheap parallax.
        self.road_offset = (self.road_offset + self.scroll_speed * dt) % 92
        self.hills_offset = (self.hills_offset + self.scroll_speed * 0.2 * dt) % self.WIDTH
        self.grime_offset = (self.grime_offset + self.scroll_speed * 0.35 * dt) % 340

    def _check_collision(self) -> bool:
        px1 = self.PLAYER_X + 6
        py1 = self.player_y + 6
        px2 = self.PLAYER_X + self.PLAYER_W - 8
        py2 = self.player_y + self.PLAYER_H - 4

        for obstacle in self.obstacles:
            ox1 = obstacle["x"]
            oy1 = self.GROUND_Y - obstacle["h"]
            ox2 = obstacle["x"] + obstacle["w"]
            oy2 = self.GROUND_Y

            if not (px1 < ox2 and px2 > ox1):
                continue

            if obstacle.get("kind") == "stairs":
                # Use descending profile instead of full rectangle hitbox.
                contact_x = max(ox1, min(ox2, (px1 + px2) * 0.5))
                t = (contact_x - ox1) / max(1.0, (ox2 - ox1))
                stair_top = self.GROUND_Y - obstacle["h"] * (1.0 - 0.8 * t)
                if py2 > stair_top and py1 < oy2:
                    return True
                continue

            if py1 < oy2 and py2 > oy1:
                return True
        return False

    def _tick(self) -> None:
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now
        # Clamp dt to keep physics stable on lag spikes.
        dt = max(1 / 120, min(1 / 20, dt))

        if self.running:
            self._update_speed(dt)
            player.update_player(self, dt)
            obstacles.update_obstacles(self, dt)
            self._update_background_motion(dt)
            if self._check_collision():
                self.running = False

        self.status.set(f"Score: {self.score}   Speed: {int(self.scroll_speed)}")

        self.canvas.delete("all")
        render.draw_background(self)
        render.draw_obstacles(self)
        render.draw_player(self)
        render.draw_hud(self)

        self.root.after(cfg.FRAME_DELAY_MS, self._tick)
