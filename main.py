"""Android build entrypoint for Buildozer (project root source.dir)."""

from __future__ import annotations

from importlib import import_module


if __name__ == "__main__":
    # Import modules instead of loading .py file paths. In Android APK builds,
    # sources are often byte-compiled and only .pyc may be present.
    runtime = None
    errors: list[str] = []
    for module_name in ("android_runtime", "android.main"):
        try:
            runtime = import_module(module_name)
            break
        except Exception as exc:  # pragma: no cover - startup fallback path
            errors.append(f"{module_name}: {exc!r}")

    if runtime is None:
        raise ImportError(
            "Could not import Android runtime module. Tried: " + "; ".join(errors)
        )

    runtime.SkateRushAndroidApp().run()
