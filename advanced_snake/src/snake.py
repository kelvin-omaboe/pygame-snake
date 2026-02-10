from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Iterable, List, Optional, Tuple

from .utils import lerp

Position = Tuple[int, int]
Direction = Tuple[int, int]


DIR_UP: Direction = (0, -1)
DIR_DOWN: Direction = (0, 1)
DIR_LEFT: Direction = (-1, 0)
DIR_RIGHT: Direction = (1, 0)


@dataclass
class Snake:
    """Snake model with grid-based movement and smooth rendering support."""

    positions: Deque[Position]
    direction: Direction
    min_length: int
    pending_direction: Optional[Direction] = None
    grow_by: int = 0
    last_positions: List[Position] = field(default_factory=list)
    direction_locked: bool = False

    @classmethod
    def create_centered(cls, grid_width: int, grid_height: int, length: int, min_length: int) -> "Snake":
        """Create a snake centered on the grid."""
        cx = grid_width // 2
        cy = grid_height // 2
        positions = deque([(cx - i, cy) for i in range(length)])
        return cls(positions=positions, direction=DIR_RIGHT, min_length=min_length)

    def queue_direction(self, new_dir: Direction) -> None:
        """Queue a direction change (one per tick) and prevent 180-degree turns."""
        if self.direction_locked:
            return
        if self._is_opposite(new_dir, self.direction):
            return
        self.pending_direction = new_dir
        self.direction_locked = True

    def _is_opposite(self, a: Direction, b: Direction) -> bool:
        return a[0] == -b[0] and a[1] == -b[1]

    def head(self) -> Position:
        """Return current head position."""
        return self.positions[0]

    def body(self) -> Iterable[Position]:
        """Return iterable of all snake positions."""
        return list(self.positions)

    def occupies(self, pos: Position) -> bool:
        """Return True if the snake occupies the given position."""
        return pos in self.positions

    def tick(self) -> Position:
        """Advance the snake by one grid step. Returns new head position."""
        self.last_positions = list(self.positions)

        if self.pending_direction is not None:
            self.direction = self.pending_direction
        self.pending_direction = None
        self.direction_locked = False

        head_x, head_y = self.positions[0]
        dir_x, dir_y = self.direction
        new_head = (head_x + dir_x, head_y + dir_y)

        self.positions.appendleft(new_head)
        if self.grow_by > 0:
            self.grow_by -= 1
        else:
            self.positions.pop()

        return new_head

    def grow(self, amount: int) -> None:
        """Increase snake length by the given amount."""
        self.grow_by += max(0, amount)

    def shrink(self, amount: int) -> int:
        """Shrink the snake by amount, respecting minimum length."""
        removed = 0
        while removed < amount and len(self.positions) > self.min_length:
            self.positions.pop()
            removed += 1
        self.last_positions = list(self.positions)
        return removed

    def reset_render_state(self) -> None:
        """Reset render interpolation baseline."""
        self.last_positions = list(self.positions)

    def render_positions(self, alpha: float) -> List[Tuple[float, float]]:
        """Return interpolated positions for smooth rendering."""
        if not self.last_positions or len(self.last_positions) != len(self.positions):
            return [(float(x), float(y)) for x, y in self.positions]

        interpolated: List[Tuple[float, float]] = []
        for (lx, ly), (cx, cy) in zip(self.last_positions, self.positions):
            ix = lerp(lx, cx, alpha)
            iy = lerp(ly, cy, alpha)
            interpolated.append((ix, iy))
        return interpolated

    def will_collide_with_self(self, pos: Position) -> bool:
        """Return True if the position collides with the snake body."""
        return pos in list(self.positions)[1:]
