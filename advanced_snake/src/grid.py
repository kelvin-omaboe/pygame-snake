from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

Position = Tuple[int, int]


@dataclass(frozen=True)
class Grid:
    """Grid helper for coordinate conversions and bounds."""

    width: int
    height: int
    cell_size: int
    hud_height: int

    def in_bounds(self, pos: Position) -> bool:
        """Return True if the position is within the grid."""
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def to_pixel(self, pos: Position) -> Tuple[int, int]:
        """Convert grid position to top-left pixel coordinates."""
        x, y = pos
        return (x * self.cell_size, y * self.cell_size + self.hud_height)

    def center_pixel(self, pos: Position) -> Tuple[int, int]:
        """Convert grid position to center pixel coordinates."""
        px, py = self.to_pixel(pos)
        half = self.cell_size // 2
        return (px + half, py + half)

    def all_cells(self) -> Iterable[Position]:
        """Yield all grid cells."""
        for y in range(self.height):
            for x in range(self.width):
                yield (x, y)
