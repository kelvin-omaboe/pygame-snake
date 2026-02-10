from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

Position = Tuple[int, int]


@dataclass(frozen=True)
class Food:
    """Food entity."""

    position: Position
