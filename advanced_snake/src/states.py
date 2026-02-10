from __future__ import annotations

from enum import Enum, auto


class GameState(Enum):
    """Possible game states."""

    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    STATS = auto()
    CONTROLS = auto()
    CUSTOMIZE = auto()
