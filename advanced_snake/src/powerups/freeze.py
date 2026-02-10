from __future__ import annotations

from typing import Tuple

from .base import PowerUp


class Freeze(PowerUp):
    """Freeze power-up: pauses snake movement for a short duration."""

    def __init__(self, position: Tuple[int, int], duration: float) -> None:
        super().__init__(position, "freeze", duration, (150, 200, 240), "F")

    def apply(self, game: "Game") -> None:  # type: ignore[name-defined]
        game.activate_effect("freeze", self.duration)
