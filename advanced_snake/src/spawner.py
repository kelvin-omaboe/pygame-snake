from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple, Type

from .grid import Grid
from .food import Food
from .powerups.base import PowerUp
from .powerups.freeze import Freeze
from .powerups.shield import Shield
from .powerups.shrink import Shrink
from .powerups.speed import SpeedBoost
from .utils import manhattan, make_rng
from . import settings

Position = Tuple[int, int]


POWERUP_CLASSES: Dict[str, Type[PowerUp]] = {
    "speed": SpeedBoost,
    "shrink": Shrink,
    "freeze": Freeze,
    "shield": Shield,
}


@dataclass
class Spawner:
    """Spawn food and power-ups safely on the grid."""

    grid: Grid
    seed: int | None = None

    def __post_init__(self) -> None:
        self.rng = make_rng(self.seed)

    def _safe_cells(self, blocked: Iterable[Position], head: Position, min_distance: int) -> List[Position]:
        blocked_set = set(blocked)
        safe: List[Position] = []
        for pos in self.grid.all_cells():
            if pos in blocked_set:
                continue
            if manhattan(pos, head) < min_distance:
                continue
            safe.append(pos)
        return safe

    def spawn_food(self, blocked: Iterable[Position], head: Position) -> Optional[Food]:
        """Spawn food in a safe cell."""
        candidates = self._safe_cells(blocked, head, settings.MIN_SPAWN_DISTANCE)
        if not candidates:
            return None
        pos = self.rng.choice(candidates)
        return Food(position=pos)

    def spawn_powerup(
        self,
        blocked: Iterable[Position],
        head: Position,
        weights: Dict[str, int],
    ) -> Optional[PowerUp]:
        """Spawn a power-up using weighted selection."""
        candidates = self._safe_cells(blocked, head, settings.MIN_SPAWN_DISTANCE)
        if not candidates:
            return None

        names = list(weights.keys())
        weight_values = [max(0, int(w)) for w in weights.values()]
        if sum(weight_values) <= 0:
            return None

        choice = self.rng.choices(names, weights=weight_values, k=1)[0]
        pos = self.rng.choice(candidates)
        powerup_cls = POWERUP_CLASSES[choice]

        if choice == "speed":
            return powerup_cls(pos, settings.SPEED_DURATION)
        if choice == "shrink":
            return powerup_cls(pos, settings.SHRINK_DURATION)
        if choice == "freeze":
            return powerup_cls(pos, settings.FREEZE_DURATION)
        if choice == "shield":
            return powerup_cls(pos, settings.SHIELD_DURATION)

        return None
