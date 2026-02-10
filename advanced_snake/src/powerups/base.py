from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

Position = Tuple[int, int]


@dataclass
class PowerUp:
    """Base class for power-ups."""

    position: Position
    name: str
    duration: float
    color: Tuple[int, int, int]
    icon: str

    def apply(self, game: "Game") -> None:  # type: ignore[name-defined]
        """Apply the power-up effect to the game."""
        raise NotImplementedError

    def expire(self, game: "Game") -> None:  # type: ignore[name-defined]
        """Expire the power-up effect from the game."""
        pass
