import time
import tkinter as tk

from . import config as cfg
from . import music, obstacles, player, render


class SkateGame:
    """Main orchestrator: owns state and runs the frame loop."""
    # Mirror constants from config for shorter access inside methods.
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
        # Keep references to root window and basic window setup.
        self.root = root
        self.root.title("Skate Rush")
        self.root.resizable(False, False)

        # Main draw surface.
        self.canvas = tk.Canvas(
            root,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg="#d6ecff",
            highlightthickness=0,
        )
        self.canvas.pack()

        # Bottom status line (score only).
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

        # Global run/score state.
        self.running = True
        self.score = 0
        self.menu_open = True
        self.menu_screen = "main"
        self.menu_index = 0
        self.menu_items = ["start", "sound", "tricks"]
        self.sound_focus = 0
        self.volume_level = 2
        self.menu_hitboxes: list[dict[str, object]] = []

        # Player physics state.
        self.scroll_speed = self.BASE_SCROLL_SPEED
        self.player_y = self.GROUND_Y - self.PLAYER_H
        self.player_vy = 0.0
        self.on_ground = True

        # Trick animation state.
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
        self.air_kickflip_used = False
        self.air_turn180_used = False
        self.air_backflip_used = False
        self.trick_label = ""
        self.manual_score_timer = 0.0

        # Ground input flags (manual stance).
        self.left_pressed = False
        self.right_pressed = False

        # Parallax offsets for background layers.
        self.road_offset = 0.0
        self.hills_offset = 0.0
        self.grime_offset = 0.0

        # Dynamic obstacle pool.
        self.obstacles: list[dict[str, float | str | int]] = []
        self.next_obstacle_x = self.WIDTH + 180

        # Background music loop.
        self.music = music.MusicPlayer()
        self.music.set_volume(self.volume_level)
        self.music.start()

        # Prepare first batch of obstacles and controls.
        obstacles.spawn_initial_obstacles(self)
        self._bind_keys()
        self.canvas.bind("<Button-1>", self._on_click)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.focus_force()

        # Kick off frame timing.
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
        self.root.bind_all("<Escape>", self._on_escape)
        self.root.bind_all("<Return>", self._on_enter)
        self.root.bind_all("<KP_Enter>", self._on_enter)
        self.root.bind_all("<r>", self._reset)
        self.root.bind_all("<R>", self._reset)

    def _on_jump(self, event: tk.Event) -> None:
        if self.menu_open:
            self._menu_move(-1)
            return
        # Delegate to player module to keep responsibilities separated.
        player.on_jump(self, event)

    def _on_down_press(self, event: tk.Event) -> None:
        if self.menu_open:
            self._menu_move(1)
            return
        player.on_down_press(self, event)

    def _on_left_press(self, event: tk.Event) -> None:
        if self.menu_open:
            self._adjust_volume(-1)
            return
        player.on_left_press(self, event)

    def _on_left_release(self, event: tk.Event) -> None:
        player.on_left_release(self, event)

    def _on_right_press(self, event: tk.Event) -> None:
        if self.menu_open:
            self._adjust_volume(1)
            return
        player.on_right_press(self, event)

    def _on_right_release(self, event: tk.Event) -> None:
        if self.menu_open:
            return
        player.on_right_release(self, event)

    def _on_escape(self, _event: tk.Event) -> None:
        self.menu_open = not self.menu_open
        if self.menu_open:
            self.menu_screen = "main"
            self.left_pressed = False
            self.right_pressed = False

    def _on_enter(self, _event: tk.Event) -> None:
        if not self.menu_open:
            return
        self._menu_activate()

    def _on_click(self, event: tk.Event) -> None:
        if not self.menu_open:
            return
        self._menu_click(event.x, event.y)

    def _on_close(self) -> None:
        self.music.stop()
        self.root.destroy()

    def _menu_move(self, step: int) -> None:
        if self.menu_screen == "main":
            self.menu_index = (self.menu_index + step) % len(self.menu_items)
            return
        if self.menu_screen == "sound":
            self.sound_focus = (self.sound_focus + step) % 2
            return

    def _menu_activate(self) -> None:
        if self.menu_screen == "sound":
            if self.sound_focus == 0:
                self._adjust_volume(1)
            else:
                self.menu_screen = "main"
            return
        if self.menu_screen == "tricks":
            self.menu_screen = "main"
            return

        selected = self.menu_items[self.menu_index]
        if selected == "start":
            if not self.running:
                self._reset()
            self.menu_open = False
        elif selected == "sound":
            self.menu_screen = "sound"
            self.sound_focus = 0
        elif selected == "tricks":
            self.menu_screen = "tricks"

    def _adjust_volume(self, delta: int) -> None:
        if self.menu_screen != "sound":
            return
        new_level = max(0, min(3, self.volume_level + delta))
        if new_level == self.volume_level:
            return
        self.volume_level = new_level
        self.music.set_volume(self.volume_level)

    def _menu_click(self, x: int, y: int) -> None:
        for hit in self.menu_hitboxes:
            x1, y1, x2, y2 = hit["rect"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                action = str(hit["action"])
                if action == "start":
                    if not self.running:
                        self._reset()
                    self.menu_open = False
                    self.menu_screen = "main"
                elif action == "open_sound":
                    self.menu_screen = "sound"
                    self.sound_focus = 0
                elif action == "open_tricks":
                    self.menu_screen = "tricks"
                elif action == "sound_down":
                    self._adjust_volume(-1)
                elif action == "sound_up":
                    self._adjust_volume(1)
                elif action == "back_main":
                    self.menu_screen = "main"
                return

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
        self.air_kickflip_used = False
        self.air_turn180_used = False
        self.air_backflip_used = False
        self.trick_label = ""
        self.manual_score_timer = 0.0

        self.left_pressed = False
        self.right_pressed = False

        self.road_offset = 0.0
        self.hills_offset = 0.0
        self.grime_offset = 0.0

        self.obstacles.clear()
        self.next_obstacle_x = self.WIDTH + 180
        obstacles.spawn_initial_obstacles(self)
        self.menu_open = False
        self.menu_screen = "main"

        self.last_time = time.perf_counter()
        self.status.set("Score: 0")

    def _approach(self, value: float, target: float, amount: float) -> float:
        # Move `value` toward `target` by at most `amount`.
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
        # Keep skyline/hills static to avoid distracting "floating buildings".
        self.hills_offset = 0.0
        self.grime_offset = (self.grime_offset + self.scroll_speed * 0.35 * dt) % 340

    def _check_collision(self) -> bool:
        # Slightly inset player rectangle for fairer collisions.
        px1 = self.PLAYER_X + 6
        py1 = self.player_y + 6
        px2 = self.PLAYER_X + self.PLAYER_W - 8
        py2 = self.player_y + self.PLAYER_H - 4

        for obstacle in self.obstacles:
            # Build obstacle bounds in world coordinates.
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
        # Measure real elapsed time since last frame.
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now
        # Clamp dt to keep physics stable on lag spikes.
        dt = max(1 / 120, min(1 / 20, dt))

        if self.running and not self.menu_open:
            # Update gameplay simulation first.
            self._update_speed(dt)
            player.update_player(self, dt)
            obstacles.update_obstacles(self, dt)
            self._update_background_motion(dt)
            if self._check_collision():
                self.running = False

        # Refresh text status even after crash.
        self.status.set(f"Score: {self.score}")

        # Full redraw each frame.
        self.canvas.delete("all")
        render.draw_background(self)
        render.draw_obstacles(self)
        render.draw_player(self)
        render.draw_hud(self)
        if self.menu_open:
            render.draw_menu(self)
        else:
            self.menu_hitboxes = []

        # Schedule next frame.
        self.root.after(cfg.FRAME_DELAY_MS, self._tick)
