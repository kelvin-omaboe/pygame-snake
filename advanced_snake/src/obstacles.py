from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from . import settings
from .grid import Grid
from .levels import LevelConfig
from .utils import make_rng, manhattan, now_seconds

Position = Tuple[int, int]
Direction = Tuple[int, int]


@dataclass
class MovingObstacle:
    position: Position
    direction: Direction


@dataclass
class Gate:
    position: Position
    active: bool
    next_toggle: float


@dataclass
class ObstacleManager:
    """Manages static obstacles and hazard variants."""

    obstacles: Set[Position] = field(default_factory=set)
    moving: List[MovingObstacle] = field(default_factory=list)
    gates: List[Gate] = field(default_factory=list)
    crumbling: Dict[Position, float] = field(default_factory=dict)
    boss_core: Set[Position] = field(default_factory=set)
    _move_accumulator: float = 0.0

    def clear(self) -> None:
        """Remove all obstacles and hazards."""
        self.obstacles.clear()
        self.moving.clear()
        self.gates.clear()
        self.crumbling.clear()
        self.boss_core.clear()
        self._move_accumulator = 0.0

    def all_positions(self, include_inactive_gates: bool = True) -> Set[Position]:
        """Return all occupied hazard positions."""
        positions = set(self.obstacles)
        positions.update(self.boss_core)
        positions.update(self.crumbling.keys())
        positions.update(moving.position for moving in self.moving)
        if include_inactive_gates:
            positions.update(gate.position for gate in self.gates)
        else:
            positions.update(gate.position for gate in self.gates if gate.active)
        return positions

    def blocks_spawn(self, pos: Position) -> bool:
        """Return True if a position is blocked for spawning."""
        return pos in self.all_positions(include_inactive_gates=True)

    def collides(self, pos: Position) -> bool:
        """Return True if position collides with an active hazard."""
        if pos in self.obstacles or pos in self.boss_core:
            return True
        if pos in self.crumbling:
            return True
        if any(moving.position == pos for moving in self.moving):
            return True
        if any(gate.position == pos and gate.active for gate in self.gates):
            return True
        return False

    def update(self, dt: float, grid: Grid, snake_positions: Set[Position]) -> None:
        """Update moving obstacles, gates, and crumble timers."""
        now = now_seconds()

        # Move hazards in fixed steps for a consistent feel.
        self._move_accumulator += dt
        while self._move_accumulator >= settings.MOVING_STEP_INTERVAL:
            self._move_accumulator -= settings.MOVING_STEP_INTERVAL
            self._step_moving(grid, snake_positions)

        # Toggle gates.
        for gate in self.gates:
            if now < gate.next_toggle:
                continue
            if gate.active:
                gate.active = False
                gate.next_toggle = now + settings.GATE_OFF_DURATION
                continue
            if gate.position in snake_positions:
                gate.next_toggle = now + 0.2
                continue
            gate.active = True
            gate.next_toggle = now + settings.GATE_ON_DURATION

        # Clear crumbling tiles that expired.
        expired = [pos for pos, end in self.crumbling.items() if end <= now]
        for pos in expired:
            self.crumbling.pop(pos, None)

    def build_for_level(
        self,
        config: LevelConfig,
        grid: Grid,
        snake_positions: Set[Position],
        snake_head: Position,
        seed: int | None = None,
    ) -> None:
        """Generate obstacles and hazards for the given level config."""
        self.clear()
        rng = make_rng(seed)
        occupied = set(snake_positions)

        if config.boss:
            block = self._place_boss_core(grid, occupied, snake_head, rng)
            if block:
                self.boss_core.update(block)
                occupied.update(block)

        self._build_static_obstacles(config.obstacles, grid, occupied, snake_head, rng)

        self._spawn_moving(config.moving, grid, occupied, snake_head, rng)
        self._spawn_gates(config.gates, grid, occupied, snake_head, rng)
        self._spawn_crumbling(config.crumble, grid, occupied, snake_head, rng)

    def _build_static_obstacles(
        self,
        count: int,
        grid: Grid,
        occupied: Set[Position],
        snake_head: Position,
        rng,
    ) -> None:
        """Generate clustered static obstacles."""
        attempts = 0
        while len(self.obstacles) < count and attempts < max(12, count * 12):
            attempts += 1
            block_size = rng.randint(1, settings.OBSTACLE_BLOCK_MAX)
            ox = rng.randint(0, max(0, grid.width - block_size))
            oy = rng.randint(0, max(0, grid.height - block_size))

            new_cells: List[Position] = []
            blocked = False
            for y in range(oy, oy + block_size):
                for x in range(ox, ox + block_size):
                    pos = (x, y)
                    if pos in occupied:
                        blocked = True
                        break
                    if manhattan(pos, snake_head) < settings.MIN_SPAWN_DISTANCE:
                        blocked = True
                        break
                    new_cells.append(pos)
                if blocked:
                    break

            if blocked:
                continue

            for pos in new_cells:
                self.obstacles.add(pos)
                occupied.add(pos)

    def _spawn_moving(
        self,
        count: int,
        grid: Grid,
        occupied: Set[Position],
        snake_head: Position,
        rng,
    ) -> None:
        """Spawn moving hazards."""
        directions: List[Direction] = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for _ in range(count):
            pos = self._find_open_cell(grid, occupied, snake_head, rng)
            if pos is None:
                break
            direction = rng.choice(directions)
            self.moving.append(MovingObstacle(position=pos, direction=direction))
            occupied.add(pos)

    def _spawn_gates(
        self,
        count: int,
        grid: Grid,
        occupied: Set[Position],
        snake_head: Position,
        rng,
    ) -> None:
        """Spawn timed gates."""
        now = now_seconds()
        for _ in range(count):
            pos = self._find_open_cell(grid, occupied, snake_head, rng)
            if pos is None:
                break
            active = rng.choice([True, False])
            offset = rng.random() * (settings.GATE_ON_DURATION + settings.GATE_OFF_DURATION)
            next_toggle = now + offset
            self.gates.append(Gate(position=pos, active=active, next_toggle=next_toggle))
            occupied.add(pos)

    def _spawn_crumbling(
        self,
        count: int,
        grid: Grid,
        occupied: Set[Position],
        snake_head: Position,
        rng,
    ) -> None:
        """Spawn crumbling obstacles that disappear after a duration."""
        now = now_seconds()
        for _ in range(count):
            pos = self._find_open_cell(grid, occupied, snake_head, rng)
            if pos is None:
                break
            self.crumbling[pos] = now + settings.CRUMBLE_LIFETIME
            occupied.add(pos)

    def _step_moving(self, grid: Grid, snake_positions: Set[Position]) -> None:
        """Advance moving obstacles one step."""
        blocked = self.all_positions(include_inactive_gates=True) | set(snake_positions)
        new_positions: Set[Position] = set()
        for mover in self.moving:
            blocked.discard(mover.position)
            nx = mover.position[0] + mover.direction[0]
            ny = mover.position[1] + mover.direction[1]
            candidate = (nx, ny)
            if not grid.in_bounds(candidate) or candidate in blocked or candidate in new_positions:
                mover.direction = (-mover.direction[0], -mover.direction[1])
                nx = mover.position[0] + mover.direction[0]
                ny = mover.position[1] + mover.direction[1]
                candidate = (nx, ny)
                if not grid.in_bounds(candidate) or candidate in blocked or candidate in new_positions:
                    candidate = mover.position
            mover.position = candidate
            new_positions.add(candidate)

    def _find_open_cell(
        self,
        grid: Grid,
        occupied: Set[Position],
        snake_head: Position,
        rng,
    ) -> Position | None:
        for _ in range(140):
            pos = (rng.randint(0, grid.width - 1), rng.randint(0, grid.height - 1))
            if pos in occupied:
                continue
            if manhattan(pos, snake_head) < settings.MIN_SPAWN_DISTANCE:
                continue
            return pos
        return None

    def _place_boss_core(
        self,
        grid: Grid,
        occupied: Set[Position],
        snake_head: Position,
        rng,
    ) -> Set[Position] | None:
        size = 3
        for _ in range(80):
            ox = rng.randint(1, max(1, grid.width - size - 1))
            oy = rng.randint(1, max(1, grid.height - size - 1))
            cells = {(x, y) for x in range(ox, ox + size) for y in range(oy, oy + size)}
            if any(pos in occupied for pos in cells):
                continue
            if any(manhattan(pos, snake_head) < settings.MIN_SPAWN_DISTANCE + 2 for pos in cells):
                continue
            return cells
        return None
