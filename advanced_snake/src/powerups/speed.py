from __future__ import annotations

from typing import Tuple

from .base import PowerUp


class SpeedBoost(PowerUp):
    """Speed boost power-up."""

    def __init__(self, position: Tuple[int, int], duration: float) -> None:
        super().__init__(position, "speed", duration, (90, 180, 250), "S")

    def apply(self, game: "Game") -> None:  # type: ignore[name-defined]
        game.activate_effect("speed", self.duration)
