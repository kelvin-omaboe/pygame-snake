from __future__ import annotations

from typing import List, Tuple

from src.grid import Grid
from src.spawner import Spawner
from src import settings


Position = Tuple[int, int]


def test_spawner_respects_blocked_and_distance() -> None:
    grid = Grid(width=10, height=8, cell_size=20, hud_height=0)
    spawner = Spawner(grid, seed=123)
    head = (5, 4)
    snake = [head, (4, 4), (3, 4)]
    obstacles: List[Position] = [(1, 1), (2, 2), (3, 3)]
    blocked = snake + obstacles

    food = spawner.spawn_food(blocked, head)
    assert food is not None
    assert food.position not in blocked

    powerup = spawner.spawn_powerup(blocked, head, {"speed": 1})
    assert powerup is not None
    assert powerup.position not in blocked

    def manhattan(a: Position, b: Position) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    assert manhattan(food.position, head) >= settings.MIN_SPAWN_DISTANCE
    assert manhattan(powerup.position, head) >= settings.MIN_SPAWN_DISTANCE
