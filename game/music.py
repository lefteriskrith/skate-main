"""Simple built-in retro loop for background music (royalty-free)."""

from __future__ import annotations

import math
import os
import struct
import tempfile
import wave

try:
    import winsound
except ImportError:  # Non-Windows fallback.
    winsound = None


class MusicPlayer:
    """Generates and loops a tiny synth-rock style WAV track."""

    def __init__(self) -> None:
        self.sample_rate = 22050
        self.track_dir = tempfile.gettempdir()
        self.track_name = "skate_rush_theme"
        self.enabled = winsound is not None
        self.volume_level = 2  # 0=off, 1=low, 2=med, 3=high
        self.is_playing = False

    def start(self) -> None:
        if not self.enabled:
            return
        self.is_playing = True
        self._play_for_volume()

    def stop(self) -> None:
        if not self.enabled:
            return
        self.is_playing = False
        winsound.PlaySound(None, 0)

    def set_volume(self, level: int) -> None:
        self.volume_level = max(0, min(3, level))
        if self.enabled and self.is_playing:
            self._play_for_volume()

    def _play_for_volume(self) -> None:
        if self.volume_level == 0:
            winsound.PlaySound(None, 0)
            return
        track_path = self._track_path(self.volume_level)
        self._ensure_track(track_path, self.volume_level)
        winsound.PlaySound(track_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)

    def _track_path(self, volume_level: int) -> str:
        return os.path.join(self.track_dir, f"{self.track_name}_v{volume_level}.wav")

    def _ensure_track(self, track_path: str, volume_level: int) -> None:
        if os.path.exists(track_path):
            return

        beat = 0.5
        bars = 16
        total_seconds = bars * 4 * beat
        total_samples = int(total_seconds * self.sample_rate)
        volume_scale = {1: 0.35, 2: 0.65, 3: 0.95}.get(volume_level, 0.65)

        def midi_to_freq(note: int) -> float:
            return 440.0 * (2 ** ((note - 69) / 12))

        bass_pattern = [40, 40, 43, 40, 47, 45, 43, 40]
        lead_pattern = [64, 67, 71, 67, 64, 67, 72, 67]

        frames = bytearray()
        for i in range(total_samples):
            t = i / self.sample_rate
            bar_beat = int(t / beat)
            step = bar_beat % len(bass_pattern)

            bass_freq = midi_to_freq(bass_pattern[step])
            bass_square = 1.0 if math.sin(2 * math.pi * bass_freq * t) >= 0 else -1.0

            lead_step = (bar_beat * 2) % len(lead_pattern)
            lead_freq = midi_to_freq(lead_pattern[lead_step])
            lead_saw = 2.0 * ((lead_freq * t) % 1.0) - 1.0

            drum_gate = 1.0 if (t % beat) < 0.05 else 0.0
            kick = math.sin(2 * math.pi * (55 + 20 * drum_gate) * t) * drum_gate

            envelope = 0.85 - 0.35 * ((t % beat) / beat)
            sample = (0.38 * bass_square + 0.26 * lead_saw + 0.2 * kick) * envelope
            sample *= volume_scale
            sample = max(-1.0, min(1.0, sample))
            s16 = int(sample * 32767)
            frames.extend(struct.pack("<h", s16))

        with wave.open(track_path, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(frames)
