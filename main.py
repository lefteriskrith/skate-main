"""Project entrypoint.

Desktop runs Tkinter game (`game.main`).
Android/Buildozer runs Kivy runtime (`android_runtime` or `android.main`).
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any


def _is_android_runtime() -> bool:
    # Buildozer/P4A sets this env var inside Android app process.
    return "ANDROID_ARGUMENT" in os.environ


def _run_module_app(module_name: str, attr: str = "main") -> bool:
    try:
        mod = import_module(module_name)
    except Exception:
        return False
    fn: Any = getattr(mod, attr, None)
    if callable(fn):
        fn()
        return True
    return False


if __name__ == "__main__":
    errors: list[str] = []

    # Desktop-first: most local runs are from Windows/Linux/macOS.
    if not _is_android_runtime():
        if _run_module_app("game.main", "main"):
            raise SystemExit(0)
        errors.append("game.main: main() not available")

    # Android path (or desktop fallback if Tk is unavailable).
    for module_name, attr in (
        ("android_runtime", "SkateRushAndroidApp"),
        ("android.main", "SkateRushAndroidApp"),
    ):
        try:
            runtime = import_module(module_name)
            app_cls = getattr(runtime, attr)
            app_cls().run()
            raise SystemExit(0)
        except Exception as exc:  # pragma: no cover - startup fallback path
            errors.append(f"{module_name}: {exc!r}")

    raise ImportError("Could not launch game runtime. Tried: " + "; ".join(errors))
