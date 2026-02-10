from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


Number = float
Position = Tuple[int, int]


def now_seconds() -> float:
    """Return a monotonic time in seconds."""
    return time.monotonic()


def clamp(value: Number, low: Number, high: Number) -> Number:
    """Clamp a value between low and high."""
    return max(low, min(high, value))


def lerp(a: Number, b: Number, t: Number) -> Number:
    """Linear interpolation between a and b."""
    return a + (b - a) * t


def manhattan(a: Position, b: Position) -> int:
    """Return Manhattan distance between two grid positions."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def make_rng(seed: Optional[int] = None) -> random.Random:
    """Create a Random instance, optionally seeded."""
    rng = random.Random()
    if seed is not None:
        rng.seed(seed)
    return rng


@dataclass
class AudioManager:
    """Minimal audio manager scaffold (muted by default)."""

    muted: bool = True
    pack_id: str = ""
    sfx_volume: float = 0.6
    music_volume: float = 0.4
    _initialized: bool = False
    _sfx: Dict[str, "pygame.mixer.Sound"] = field(default_factory=dict)
    _music_tracks: List[str] = field(default_factory=list)

    def _ensure_init(self) -> None:
        if self._initialized:
            return
        try:
            import pygame

            pygame.mixer.init()
            self._initialized = True
        except Exception:
            self.muted = True
            self._initialized = False

    def set_muted(self, muted: bool) -> None:
        self.muted = muted
        if muted:
            self.stop_music()
        else:
            self.start_music()

    def set_volumes(self, sfx_volume: float, music_volume: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, sfx_volume))
        self.music_volume = max(0.0, min(1.0, music_volume))
        for sound in self._sfx.values():
            sound.set_volume(self.sfx_volume)
        try:
            import pygame

            pygame.mixer.music.set_volume(self.music_volume)
        except Exception:
            return

    def load_pack(self, pack_id: str) -> None:
        self._ensure_init()
        if not self._initialized:
            return
        from . import settings
        from .audio_packs import get_pack

        pack = get_pack(pack_id)
        self.pack_id = pack.id
        self._sfx.clear()
        self._music_tracks = []

        import pygame

        for name, filename in pack.sfx.items():
            path = settings.AUDIO_DIR / pack.id / "sfx" / filename
            if not path.exists():
                continue
            try:
                sound = pygame.mixer.Sound(str(path))
                sound.set_volume(self.sfx_volume)
                self._sfx[name] = sound
            except Exception:
                continue

        for filename in pack.music:
            path = settings.AUDIO_DIR / pack.id / "music" / filename
            if path.exists():
                self._music_tracks.append(str(path))

        self.start_music()

    def play(self, name: str) -> None:
        """Play a sound if not muted."""
        if self.muted:
            return
        if not self._initialized:
            self._ensure_init()
        if not self._initialized:
            return
        sound = self._sfx.get(name)
        if sound is None:
            return
        sound.set_volume(self.sfx_volume)
        sound.play()

    def start_music(self) -> None:
        if self.muted or not self._initialized:
            return
        if not self._music_tracks:
            return
        try:
            import pygame

            pygame.mixer.music.load(self._music_tracks[0])
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
        except Exception:
            return

    def stop_music(self) -> None:
        if not self._initialized:
            return
        try:
            import pygame

            pygame.mixer.music.stop()
        except Exception:
            return
