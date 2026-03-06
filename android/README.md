# Android Port (Step 1)

This folder contains the Android-ready Kivy prototype of Skate Rush.

## What is included now

- `main.py`: Kivy prototype runner (separate from desktop `tkinter` game)
- `buildozer.spec`: Android packaging config (for APK/AAB later)

## Quick desktop test (first check)

Run this from `android/`:

```powershell
python main.py
```

Controls (desktop):

- `Up`: jump
- Touch/click left side: jump
- Touch/click right side: hold stance

## Build Android APK (next step, typically on Linux/WSL)

From `android/`:

```bash
buildozer android debug
```

APK output is usually under:

- `android/bin/`

Install on your phone:

```bash
adb install -r bin/skaterush-0.1.0-arm64-v8a-debug.apk
```

## Build Play Store bundle (AAB)

Later, after testing:

```bash
buildozer android release
```

For Play Store, generate/upload AAB from release artifacts.

## Notes

- Windows usually needs WSL/Linux for Buildozer workflow.
- This is Step 1 prototype; gameplay parity with desktop will be completed incrementally.
