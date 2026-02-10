from __future__ import annotations

from typing import Tuple

from .base import PowerUp


class Shrink(PowerUp):
    """Shrink power-up: reduces snake length and shows a timed indicator."""

    def __init__(self, position: Tuple[int, int], duration: float) -> None:
        super().__init__(position, "shrink", duration, (200, 140, 80), "K")

    def apply(self, game: "Game") -> None:  # type: ignore[name-defined]
        game.apply_shrink(self.duration)
