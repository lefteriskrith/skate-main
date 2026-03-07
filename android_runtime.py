"""Android Kivy runtime that reuses the same gameplay modules and visuals."""

from __future__ import annotations

import os
import sys
import time
from typing import Any

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle
from kivy.uix.widget import Widget
from kivy.utils import platform

# Allow importing the original desktop modules from project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from game import config as cfg  # noqa: E402
from game import music, obstacles, player, render  # noqa: E402


def approach(value: float, target: float, amount: float) -> float:
    if value < target:
        return min(target, value + amount)
    return max(target, value - amount)


class CanvasAdapter:
    """Tkinter-like canvas API backed by Kivy instructions."""

    def __init__(self, widget: "AndroidSkateGame") -> None:
        self.widget = widget

    def delete(self, _tag: str = "all") -> None:
        self.widget.canvas.clear()

    def _color(self, value: str | None, default: str = "#000000") -> tuple[float, float, float, float]:
        if not value or value == "":
            value = default
        value = value.strip()
        if value.startswith("#") and len(value) == 7:
            r = int(value[1:3], 16) / 255.0
            g = int(value[3:5], 16) / 255.0
            b = int(value[5:7], 16) / 255.0
            return (r, g, b, 1.0)
        return (0.0, 0.0, 0.0, 1.0)

    def _map_xy(self, x: float, y_top: float) -> tuple[float, float]:
        return self.widget.sx(x), self.widget.sy(y_top)

    def create_rectangle(self, x1: float, y1: float, x2: float, y2: float, **kwargs: Any) -> None:
        fill = kwargs.get("fill", "")
        outline = kwargs.get("outline", "")
        width = float(kwargs.get("width", 1))

        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)

        sx = self.widget.sx(left)
        sy = self.widget.sy(bottom)
        sw = max(1.0, round(self.widget.sw(right - left)))
        sh = max(1.0, round(self.widget.sh(bottom - top)))

        if fill != "":
            Color(*self._color(fill))
            Rectangle(pos=(sx, sy), size=(sw, sh))
        if outline != "" and width > 0:
            Color(*self._color(outline))
            Line(rectangle=(sx, sy, sw, sh), width=max(1.0, self.widget.sw(width)))

    def create_oval(self, x1: float, y1: float, x2: float, y2: float, **kwargs: Any) -> None:
        fill = kwargs.get("fill", "")
        outline = kwargs.get("outline", "")
        width = float(kwargs.get("width", 1))

        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)

        sx = self.widget.sx(left)
        sy = self.widget.sy(bottom)
        sw = max(1.0, round(self.widget.sw(right - left)))
        sh = max(1.0, round(self.widget.sh(bottom - top)))

        if fill != "":
            Color(*self._color(fill))
            Ellipse(pos=(sx, sy), size=(sw, sh))
        if outline != "" and width > 0:
            Color(*self._color(outline))
            Line(ellipse=(sx, sy, sw, sh), width=max(1.0, self.widget.sw(width)))

    def create_polygon(self, *coords: Any, **kwargs: Any) -> None:
        fill = kwargs.get("fill", "")
        outline = kwargs.get("outline", "")
        width = float(kwargs.get("width", 1))

        if len(coords) == 1 and isinstance(coords[0], (list, tuple)):
            pts = list(coords[0])
        else:
            pts = list(coords)

        mapped: list[float] = []
        for i in range(0, len(pts), 2):
            x, y = self._map_xy(float(pts[i]), float(pts[i + 1]))
            mapped.extend((x, y))

        if fill != "" and len(mapped) >= 6:
            pts_xy = [(mapped[i], mapped[i + 1]) for i in range(0, len(mapped), 2)]
            triangles = self._ear_clip_triangulate(pts_xy)
            if triangles:
                Color(*self._color(fill))
                for a, b, c in triangles:
                    x1, y1 = pts_xy[a]
                    x2, y2 = pts_xy[b]
                    x3, y3 = pts_xy[c]
                    Triangle(points=(x1, y1, x2, y2, x3, y3))
            else:
                # Fallback fan only if triangulation unexpectedly fails.
                cx = sum(p[0] for p in pts_xy) / len(pts_xy)
                cy = sum(p[1] for p in pts_xy) / len(pts_xy)
                Color(*self._color(fill))
                for i in range(len(pts_xy)):
                    x1, y1 = pts_xy[i]
                    x2, y2 = pts_xy[(i + 1) % len(pts_xy)]
                    Triangle(points=(cx, cy, x1, y1, x2, y2))

        if outline != "" and width > 0 and len(mapped) >= 4:
            Color(*self._color(outline))
            loop = mapped + mapped[:2]
            Line(points=loop, width=max(1.0, self.widget.sw(width)))

    def _ear_clip_triangulate(self, pts: list[tuple[float, float]]) -> list[tuple[int, int, int]]:
        n = len(pts)
        if n < 3:
            return []

        def area2(poly: list[tuple[float, float]]) -> float:
            s = 0.0
            for i in range(len(poly)):
                x1, y1 = poly[i]
                x2, y2 = poly[(i + 1) % len(poly)]
                s += (x1 * y2) - (x2 * y1)
            return s

        def cross(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
            return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

        def point_in_tri(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
            c1 = cross(a, b, p)
            c2 = cross(b, c, p)
            c3 = cross(c, a, p)
            has_neg = (c1 < 0) or (c2 < 0) or (c3 < 0)
            has_pos = (c1 > 0) or (c2 > 0) or (c3 > 0)
            return not (has_neg and has_pos)

        indices = list(range(n))
        is_ccw = area2(pts) > 0
        triangles: list[tuple[int, int, int]] = []

        guard = 0
        while len(indices) > 3 and guard < n * n:
            guard += 1
            ear_found = False
            m = len(indices)
            for i in range(m):
                i0 = indices[(i - 1) % m]
                i1 = indices[i]
                i2 = indices[(i + 1) % m]
                a, b, c = pts[i0], pts[i1], pts[i2]

                cr = cross(a, b, c)
                if (is_ccw and cr <= 0) or ((not is_ccw) and cr >= 0):
                    continue

                blocked = False
                for j in indices:
                    if j in (i0, i1, i2):
                        continue
                    if point_in_tri(pts[j], a, b, c):
                        blocked = True
                        break
                if blocked:
                    continue

                triangles.append((i0, i1, i2))
                del indices[i]
                ear_found = True
                break

            if not ear_found:
                return []

        if len(indices) == 3:
            triangles.append((indices[0], indices[1], indices[2]))
        return triangles

    def create_line(self, *coords: float, **kwargs: Any) -> None:
        fill = kwargs.get("fill", "#000000")
        width = float(kwargs.get("width", 1))
        mapped: list[float] = []
        for i in range(0, len(coords), 2):
            x, y = self._map_xy(float(coords[i]), float(coords[i + 1]))
            mapped.extend((x, y))
        Color(*self._color(fill))
        Line(points=mapped, width=max(1.0, self.widget.sw(width)))

    def create_text(self, x: float, y: float, **kwargs: Any) -> None:
        text = str(kwargs.get("text", ""))
        fill = kwargs.get("fill", "#000000")
        font = kwargs.get("font", ("Segoe UI", 12))
        anchor = kwargs.get("anchor", "center")

        size = 12
        if isinstance(font, (list, tuple)) and len(font) >= 2:
            try:
                size = int(font[1])
            except (ValueError, TypeError):
                size = 12

        label = CoreLabel(text=text, font_size=max(8, int(self.widget.sh(size * 0.9))), color=self._color(fill))
        label.refresh()
        tex = label.texture
        tw, th = tex.size

        sx, sy = self._map_xy(float(x), float(y))
        if anchor == "ne":
            px = sx - tw
            py = sy - th
        elif anchor == "nw":
            px = sx
            py = sy - th
        elif anchor == "w":
            px = sx
            py = sy - th * 0.5
        elif anchor == "n":
            px = sx - tw * 0.5
            py = sy - th
        else:
            px = sx - tw * 0.5
            py = sy - th * 0.5

        Color(1, 1, 1, 1)
        Rectangle(texture=tex, pos=(px, py), size=(tw, th))


class GameProxy:
    """Expose game state with a `canvas` field expected by render/player modules."""

    def __init__(self, game: "AndroidSkateGame") -> None:
        self._game = game

    @property
    def canvas(self) -> CanvasAdapter:
        return self._game.canvas_api

    def __getattr__(self, item: str) -> Any:
        return getattr(self._game, item)

    def __setattr__(self, key: str, value: Any) -> None:
        if key == "_game":
            super().__setattr__(key, value)
        else:
            setattr(self._game, key, value)


class AndroidSkateGame(Widget):
    WIDTH = cfg.WIDTH
    HEIGHT = cfg.HEIGHT
    # Slightly lower floor on Android so road reads larger on phone screens.
    GROUND_Y = cfg.GROUND_Y - 24
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
    OBSTACLE_MIN_GAP = cfg.OBSTACLE_MIN_GAP
    OBSTACLE_MAX_GAP = cfg.OBSTACLE_MAX_GAP
    KICKFLIP_RATE = cfg.KICKFLIP_RATE
    TURN180_RATE = cfg.TURN180_RATE
    BACKFLIP_RATE = cfg.BACKFLIP_RATE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._on_resize)
        self.keyboard = None

        if platform == "android":
            try:
                from jnius import autoclass

                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                LayoutParams = autoclass("android.view.WindowManager$LayoutParams")
                PythonActivity.mActivity.getWindow().setSoftInputMode(
                    LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN
                )
            except Exception:
                pass

        self.menu_open = True
        self.menu_screen = "main"
        self.menu_index = 0
        self.menu_items = ["start", "sound", "tricks"]
        self.sound_focus = 0
        self.volume_level = 2
        self.menu_hitboxes: list[dict[str, object]] = []
        self.control_hitboxes: list[dict[str, object]] = []
        self.active_touch_actions: dict[object, str] = {}

        self.running = True
        self.score = 0
        self.gameplay_time = 0.0
        self.speed_multiplier = 1.0
        self.next_speedup_at = 20.0

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
        self.trick_label_timer = 0.0
        self.manual_score_timer = 0.0

        self.left_pressed = False
        self.right_pressed = False

        self.road_offset = 0.0
        self.hills_offset = 0.0
        self.grime_offset = 0.0

        self.obstacles: list[dict[str, float | str | int]] = []
        self.next_obstacle_x = self.WIDTH + 180
        self.music = music.MusicPlayer()
        self.music.set_volume(self.volume_level)
        self.music.start()

        self.canvas_api = CanvasAdapter(self)
        self.proxy = GameProxy(self)

        obstacles.spawn_initial_obstacles(self.proxy)

        Window.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)

        self.last_time = time.perf_counter()
        Clock.schedule_interval(self._tick, 1.0 / 120.0)

    def _on_resize(self, *_args):
        pass

    def sx(self, x: float) -> float:
        return x * (self.width / self.WIDTH)

    def sy(self, y_top: float) -> float:
        return self.height - y_top * (self.height / self.HEIGHT)

    def sw(self, w: float) -> float:
        return w * (self.width / self.WIDTH)

    def sh(self, h: float) -> float:
        return h * (self.height / self.HEIGHT)

    def _keyboard_closed(self):
        self.keyboard = None

    def _extract_key_name(self, keycode: Any, codepoint: Any = "") -> str:
        """Normalize Kivy key callback data to a stable lowercase name."""
        if isinstance(keycode, (list, tuple)) and len(keycode) > 1:
            return str(keycode[1]).lower()
        if isinstance(codepoint, str) and codepoint:
            if codepoint == "\r":
                return "enter"
            return codepoint.lower()
        if isinstance(keycode, str):
            return keycode.lower()
        return str(keycode).lower()

    def _on_key_down(self, _window, keycode, _scancode=None, codepoint="", _mods=None):
        key = self._extract_key_name(keycode, codepoint)
        if key == "escape":
            self.menu_open = not self.menu_open
            if self.menu_open:
                self.menu_screen = "main"
                self.left_pressed = False
                self.right_pressed = False
            return True

        if self.menu_open:
            if key == "up":
                self._menu_move(-1)
            elif key == "down":
                self._menu_move(1)
            elif key == "left":
                self._adjust_volume(-1)
            elif key == "right":
                self._adjust_volume(1)
            elif key in ("enter", "numpadenter"):
                self._menu_activate()
            return True

        if key == "up":
            player.on_jump(self.proxy, None)
        elif key == "down":
            player.on_down_press(self.proxy, None)
        elif key == "left":
            player.on_left_press(self.proxy, None)
        elif key == "right":
            player.on_right_press(self.proxy, None)
        elif key == "r":
            self._reset()
        return True

    def _on_key_up(self, _window, keycode, *_args):
        key = self._extract_key_name(keycode)
        if key == "left":
            player.on_left_release(self.proxy, None)
        elif key == "right":
            player.on_right_release(self.proxy, None)
        return True

    def on_touch_down(self, touch):
        if self.menu_open:
            dx = touch.x * (self.WIDTH / max(1.0, self.width))
            dy = (self.height - touch.y) * (self.HEIGHT / max(1.0, self.height))
            self._menu_click(dx, dy)
            return True

        dx = touch.x * (self.WIDTH / max(1.0, self.width))
        dy = (self.height - touch.y) * (self.HEIGHT / max(1.0, self.height))
        for hit in self.control_hitboxes:
            x1, y1, x2, y2 = hit["rect"]
            if x1 <= dx <= x2 and y1 <= dy <= y2:
                action = str(hit["action"])
                self._press_action(action)
                self.active_touch_actions[touch.uid] = action
                return True

        # Fallback touch zones if user taps outside button circles.
        nx = touch.x / max(1.0, self.width)
        if nx < 0.34:
            player.on_jump(self.proxy, None)
        elif nx < 0.66:
            player.on_down_press(self.proxy, None)
        else:
            player.on_right_press(self.proxy, None)
            self.active_touch_actions[touch.uid] = "right"
        return True

    def on_touch_up(self, touch):
        action = self.active_touch_actions.pop(touch.uid, "")
        if action:
            self._release_action(action)
        return True

    def _press_action(self, action: str) -> None:
        if action == "left":
            player.on_left_press(self.proxy, None)
        elif action == "right":
            player.on_right_press(self.proxy, None)
        elif action == "up":
            player.on_jump(self.proxy, None)
        elif action == "down":
            player.on_down_press(self.proxy, None)
        elif action == "restart":
            self._reset()
        elif action == "pause":
            self.left_pressed = False
            self.right_pressed = False
            self.menu_screen = "main"
            self.menu_open = True

    def _release_action(self, action: str) -> None:
        if action == "left":
            player.on_left_release(self.proxy, None)
        elif action == "right":
            player.on_right_release(self.proxy, None)

    def _menu_move(self, step: int) -> None:
        if self.menu_screen == "main":
            self.menu_index = (self.menu_index + step) % len(self.menu_items)
        elif self.menu_screen == "sound":
            self.sound_focus = (self.sound_focus + step) % 2

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
        self.volume_level = int(max(0, min(3, self.volume_level + delta)))
        self.music.set_volume(self.volume_level)

    def _menu_click(self, x: float, y: float) -> None:
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

    def _reset(self) -> None:
        self.running = True
        self.score = 0
        self.gameplay_time = 0.0
        self.speed_multiplier = 1.0
        self.next_speedup_at = 20.0
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
        self.trick_label_timer = 0.0
        self.manual_score_timer = 0.0

        self.left_pressed = False
        self.right_pressed = False
        self.road_offset = 0.0
        self.hills_offset = 0.0
        self.grime_offset = 0.0

        self.obstacles.clear()
        self.next_obstacle_x = self.WIDTH + 180
        obstacles.spawn_initial_obstacles(self.proxy)
        self.menu_open = False
        self.menu_screen = "main"

    def _update_speed(self, dt: float) -> None:
        target_speed = self.BASE_SCROLL_SPEED * self.speed_multiplier
        self.scroll_speed = approach(self.scroll_speed, target_speed, self.RETURN_ACCEL * dt)
        max_speed = self.MAX_SCROLL_SPEED * self.speed_multiplier
        self.scroll_speed = max(self.MIN_SCROLL_SPEED, min(max_speed, self.scroll_speed))

    def _update_background_motion(self, dt: float) -> None:
        self.road_offset = (self.road_offset + self.scroll_speed * dt) % 88
        self.hills_offset = 0.0
        self.grime_offset = 0.0

    def _check_collision(self) -> bool:
        px1 = self.PLAYER_X + 6
        py1 = self.player_y + 6
        px2 = self.PLAYER_X + self.PLAYER_W - 8
        py2 = self.player_y + self.PLAYER_H - 4

        for obstacle in self.obstacles:
            ox1 = float(obstacle["x"])
            oy1 = self.GROUND_Y - float(obstacle["h"])
            ox2 = float(obstacle["x"]) + float(obstacle["w"])
            oy2 = self.GROUND_Y

            if not (px1 < ox2 and px2 > ox1):
                continue

            if obstacle.get("kind") == "stairs":
                contact_x = max(ox1, min(ox2, (px1 + px2) * 0.5))
                t = (contact_x - ox1) / max(1.0, (ox2 - ox1))
                stair_top = self.GROUND_Y - float(obstacle["h"]) * (1.0 - 0.8 * t)
                if py2 > stair_top and py1 < oy2:
                    return True
                continue

            if py1 < oy2 and py2 > oy1:
                return True
        return False

    def _draw_status_bar(self) -> None:
        bar_h = 34
        self.canvas_api.create_rectangle(0, self.HEIGHT - bar_h, self.WIDTH, self.HEIGHT, fill="#f2f7fb", width=0)
        self.canvas_api.create_line(0, self.HEIGHT - bar_h, self.WIDTH, self.HEIGHT - bar_h, fill="#cfd7df", width=1)
        self.canvas_api.create_text(
            self.WIDTH * 0.5,
            self.HEIGHT - (bar_h * 0.5),
            text=f"Score: {self.score}",
            fill="#1f2f3f",
            font=("Segoe UI", 15, "bold"),
            anchor="center",
        )

    def _draw_touch_controls(self) -> None:
        # Mobile controls (visual + functional hitboxes).
        self.control_hitboxes = []
        base_y = self.HEIGHT - 156

        # Left side: smaller steering buttons (left/right).
        l_size = 56
        l_gap = 14
        lx1 = 20
        lx2 = lx1 + l_size + l_gap
        for bx, label, action in ((lx1, "Left", "left"), (lx2, "Right", "right")):
            self.canvas_api.create_oval(bx, base_y, bx + l_size, base_y + l_size, fill="#eaf0f7", outline="#879cb0", width=2)
            self.canvas_api.create_text(
                bx + l_size * 0.5,
                base_y + l_size * 0.52,
                text=label,
                fill="#33485e",
                font=("Segoe UI", 11, "bold"),
                anchor="center",
            )
            self.control_hitboxes.append({"rect": (bx, base_y, bx + l_size, base_y + l_size), "action": action})

        # Left top: pause button back to menu.
        p_size = 52
        px = 18
        py = 18
        self.canvas_api.create_oval(px, py, px + p_size, py + p_size, fill="#f0ece4", outline="#9e8f78", width=2)
        self.canvas_api.create_text(
            px + p_size * 0.5,
            py + p_size * 0.52,
            text="Pause",
            fill="#4a4032",
            font=("Segoe UI", 10, "bold"),
            anchor="center",
        )
        self.control_hitboxes.append({"rect": (px, py, px + p_size, py + p_size), "action": "pause"})

        # Right side: up/down plus R.
        up_size = 78
        r_size = 62
        rx = self.WIDTH - 20 - up_size
        up_y = base_y - 6
        dn_y = up_y + up_size + 2
        self.canvas_api.create_oval(rx, up_y, rx + up_size, up_y + up_size, fill="#eaf0f7", outline="#879cb0", width=2)
        self.canvas_api.create_text(
            rx + up_size * 0.5,
            up_y + up_size * 0.52,
            text="Up",
            fill="#33485e",
            font=("Segoe UI", 16, "bold"),
            anchor="center",
        )
        self.control_hitboxes.append({"rect": (rx, up_y, rx + up_size, up_y + up_size), "action": "up"})
        dn_x = rx + (up_size - r_size) * 0.5
        self.canvas_api.create_oval(dn_x, dn_y, dn_x + r_size, dn_y + r_size, fill="#eaf0f7", outline="#879cb0", width=2)
        self.canvas_api.create_text(
            dn_x + r_size * 0.5,
            dn_y + r_size * 0.52,
            text="Down",
            fill="#33485e",
            font=("Segoe UI", 11, "bold"),
            anchor="center",
        )
        self.control_hitboxes.append({"rect": (dn_x, dn_y, dn_x + r_size, dn_y + r_size), "action": "down"})

        rr_x1 = dn_x
        rr_y1 = up_y - 70
        self.canvas_api.create_oval(rr_x1, rr_y1, rr_x1 + r_size, rr_y1 + r_size, fill="#f5e9e9", outline="#b68f8f", width=2)
        self.canvas_api.create_text(
            rr_x1 + r_size * 0.5,
            rr_y1 + r_size * 0.52,
            text="R",
            fill="#6a3f3f",
            font=("Segoe UI", 18, "bold"),
            anchor="center",
        )
        self.control_hitboxes.append({"rect": (rr_x1, rr_y1, rr_x1 + r_size, rr_y1 + r_size), "action": "restart"})

    def _draw_road_cleanup(self) -> None:
        # Remove dark asphalt blobs from shared desktop render for cleaner mobile look.
        self.canvas_api.create_rectangle(0, self.GROUND_Y + 8, self.WIDTH, self.HEIGHT - 34, fill="#40464d", width=0)
        self.canvas_api.create_rectangle(0, self.GROUND_Y, self.WIDTH, self.GROUND_Y + 7, fill="#596269", width=0)
        self.canvas_api.create_rectangle(0, self.GROUND_Y + 36, self.WIDTH, self.GROUND_Y + 44, fill="#2f353a", width=0)
        dash_x = -self.road_offset
        while dash_x < self.WIDTH + 50:
            self.canvas_api.create_rectangle(
                dash_x,
                self.GROUND_Y + 20,
                dash_x + 42,
                self.GROUND_Y + 26,
                fill="#ddd6a8",
                width=0,
            )
            dash_x += 88

    def _tick(self, _dt: float) -> None:
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now
        dt = max(1 / 120, min(1 / 20, dt))

        if self.running and not self.menu_open:
            self.gameplay_time += dt
            while self.gameplay_time >= self.next_speedup_at:
                self.speed_multiplier *= 1.5
                self.next_speedup_at += 20.0

            self._update_speed(dt)
            player.update_player(self.proxy, dt)
            obstacles.update_obstacles(self.proxy, dt)
            self._update_background_motion(dt)
            if self._check_collision():
                self.running = False

        if self.trick_label_timer > 0:
            self.trick_label_timer = max(0.0, self.trick_label_timer - dt)
            if self.trick_label_timer == 0.0:
                self.trick_label = ""

        self.canvas_api.delete("all")
        with self.canvas:
            render.draw_background(self.proxy)
            self._draw_road_cleanup()
            render.draw_obstacles(self.proxy)
            render.draw_player(self.proxy)
            render.draw_hud(self.proxy)
            self._draw_status_bar()
            if not self.menu_open:
                self._draw_touch_controls()
            if self.menu_open:
                render.draw_menu(self.proxy)
            else:
                self.menu_hitboxes = []


class SkateRushAndroidApp(App):
    def build(self):
        self.title = "Skate Rush"
        return AndroidSkateGame()

    def on_stop(self):
        root = self.root
        if root is not None and hasattr(root, "music"):
            root.music.stop()


if __name__ == "__main__":
    SkateRushAndroidApp().run()
