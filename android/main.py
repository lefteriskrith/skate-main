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
from kivy.graphics import Color, Ellipse, Line, Mesh, Rectangle
from kivy.uix.widget import Widget

# Allow importing the original desktop modules from project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from game import config as cfg  # noqa: E402
from game import obstacles, player, render  # noqa: E402


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
        sw = self.widget.sw(right - left)
        sh = self.widget.sh(bottom - top)

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
        sw = self.widget.sw(right - left)
        sh = self.widget.sh(bottom - top)

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
            vertices: list[float] = []
            for i in range(0, len(mapped), 2):
                vertices.extend((mapped[i], mapped[i + 1], 0.0, 0.0))
            indices = list(range(len(mapped) // 2))
            Color(*self._color(fill))
            Mesh(vertices=vertices, indices=indices, mode="triangle_fan")

        if outline != "" and width > 0 and len(mapped) >= 4:
            Color(*self._color(outline))
            loop = mapped + mapped[:2]
            Line(points=loop, width=max(1.0, self.widget.sw(width)))

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
    GROUND_Y = cfg.GROUND_Y
    PLAYER_X = cfg.PLAYER_X
    PLAYER_W = cfg.PLAYER_W
    PLAYER_H = cfg.PLAYER_H
    GRAVITY = cfg.GRAVITY
    JUMP_VELOCITY = cfg.JUMP_VELOCITY
    BASE_SCROLL_SPEED = cfg.BASE_SCROLL_SPEED
    MIN_SCROLL_SPEED = cfg.MIN_SCROLL_SPEED
    MAX_SCROLL_SPEED = cfg.MAX_SCROLL_SPEED
    RETURN_ACCEL = cfg.RETURN_ACCEL
    OBSTACLE_MIN_GAP = cfg.OBSTACLE_MIN_GAP
    OBSTACLE_MAX_GAP = cfg.OBSTACLE_MAX_GAP
    KICKFLIP_RATE = cfg.KICKFLIP_RATE
    TURN180_RATE = cfg.TURN180_RATE
    BACKFLIP_RATE = cfg.BACKFLIP_RATE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._on_resize)

        self.menu_open = True
        self.menu_screen = "main"
        self.menu_index = 0
        self.menu_items = ["start", "sound", "tricks"]
        self.sound_focus = 0
        self.volume_level = 2
        self.menu_hitboxes: list[dict[str, object]] = []

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

        self.obstacles: list[dict[str, float | str | int]] = []
        self.next_obstacle_x = self.WIDTH + 180

        self.canvas_api = CanvasAdapter(self)
        self.proxy = GameProxy(self)

        obstacles.spawn_initial_obstacles(self.proxy)

        self.keyboard = Window.request_keyboard(self._keyboard_closed, self)
        if self.keyboard:
            self.keyboard.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)

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
        if self.keyboard:
            self.keyboard.unbind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
            self.keyboard = None

    def _on_key_down(self, _keyboard, keycode, _text, _mods):
        key = keycode[1]
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

    def _on_key_up(self, _keyboard, keycode):
        key = keycode[1]
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

        dx = touch.x / max(1.0, self.width)
        if dx < 0.34:
            player.on_jump(self.proxy, None)
        elif dx < 0.66:
            player.on_down_press(self.proxy, None)
        else:
            player.on_right_press(self.proxy, None)
        return True

    def on_touch_up(self, _touch):
        player.on_right_release(self.proxy, None)
        return True

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
        self.canvas_api.create_rectangle(0, self.HEIGHT - 28, self.WIDTH, self.HEIGHT, fill="#f2f7fb", width=0)
        self.canvas_api.create_text(12, self.HEIGHT - 8, text=f"Score: {self.score}", fill="#23313f", font=("Segoe UI", 12, "bold"), anchor="nw")

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

        self.canvas_api.delete("all")
        with self.canvas:
            render.draw_background(self.proxy)
            render.draw_obstacles(self.proxy)
            render.draw_player(self.proxy)
            render.draw_hud(self.proxy)
            self._draw_status_bar()
            if self.menu_open:
                render.draw_menu(self.proxy)
            else:
                self.menu_hitboxes = []


class SkateRushAndroidApp(App):
    def build(self):
        self.title = "Skate Rush"
        return AndroidSkateGame()


if __name__ == "__main__":
    SkateRushAndroidApp().run()
