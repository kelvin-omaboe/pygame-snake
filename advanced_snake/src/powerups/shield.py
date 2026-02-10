from __future__ import annotations

from typing import Tuple

from .base import PowerUp


class Shield(PowerUp):
    """Shield power-up: blocks one collision while active."""

    def __init__(self, position: Tuple[int, int], duration: float) -> None:
        super().__init__(position, "shield", duration, (220, 220, 120), "D")

    def apply(self, game: "Game") -> None:  # type: ignore[name-defined]
        game.activate_effect("shield", self.duration)
