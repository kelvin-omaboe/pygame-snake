from __future__ import annotations

from dataclasses import dataclass

from . import settings
from .utils import clamp


@dataclass(frozen=True)
class LevelConfig:
    """Difficulty modifiers for a level."""

    level: int
    tick_rate: float
    obstacles: int
    powerup_interval: float
    score_multiplier: float
    moving: int
    gates: int
    crumble: int
    boss: bool


class LevelManager:
    """Track and compute level progression."""

    def __init__(self) -> None:
        self.level = 1

    def compute_level(self, score: int, elapsed: float) -> int:
        """Compute level based on score and elapsed time."""
        score_level = 1 + score // settings.SCORE_PER_LEVEL
        time_level = 1 + int(elapsed // settings.TIME_PER_LEVEL)
        level = max(score_level, time_level)
        return int(clamp(level, 1, settings.MAX_LEVEL))

    @staticmethod
    def _hazard_count(level: int, start: int, every: int, maximum: int) -> int:
        if level < start:
            return 0
        steps = 1 + (level - start) // max(1, every)
        return int(clamp(steps, 0, maximum))

    @staticmethod
    def is_boss_level(level: int) -> bool:
        return settings.BOSS_EVERY_LEVEL > 0 and level % settings.BOSS_EVERY_LEVEL == 0

    def update(self, score: int, elapsed: float) -> bool:
        """Update level. Returns True if level changed."""
        new_level = self.compute_level(score, elapsed)
        if new_level != self.level:
            self.level = new_level
            return True
        return False

    def config(self) -> LevelConfig:
        """Return the current level's configuration."""
        boss = self.is_boss_level(self.level)
        tick_rate = min(settings.MAX_TICK_RATE, settings.BASE_TICK_RATE + (self.level - 1) * settings.TICK_RATE_INCREMENT)
        if boss:
            tick_rate = min(settings.MAX_TICK_RATE, tick_rate + settings.BOSS_TICK_BONUS)
        obstacles = max(0, settings.BASE_OBSTACLES + (self.level - 1) * settings.OBSTACLE_INCREMENT)
        if boss:
            obstacles += settings.BOSS_OBSTACLE_BONUS
        interval = max(
            settings.MIN_POWERUP_INTERVAL,
            settings.BASE_POWERUP_INTERVAL - (self.level - 1) * settings.POWERUP_INTERVAL_DECREMENT,
        )
        if boss:
            interval *= settings.BOSS_POWERUP_INTERVAL_MULT
        score_multiplier = 1.0 + (self.level - 1) * settings.LEVEL_SCORE_MULTIPLIER
        if boss:
            score_multiplier += settings.BOSS_SCORE_MULTIPLIER_BONUS

        moving = self._hazard_count(
            self.level,
            settings.MOVING_OBSTACLES_START_LEVEL,
            settings.MOVING_OBSTACLES_EVERY_LEVEL,
            settings.MOVING_OBSTACLES_MAX,
        )
        gates = self._hazard_count(
            self.level,
            settings.GATE_START_LEVEL,
            settings.GATE_EVERY_LEVEL,
            settings.GATE_MAX,
        )
        crumble = self._hazard_count(
            self.level,
            settings.CRUMBLE_START_LEVEL,
            settings.CRUMBLE_EVERY_LEVEL,
            settings.CRUMBLE_MAX,
        )

        if boss:
            moving += settings.BOSS_MOVING_BONUS
            gates += settings.BOSS_GATE_BONUS
            crumble += settings.BOSS_CRUMBLE_BONUS

        return LevelConfig(
            self.level,
            tick_rate,
            obstacles,
            interval,
            score_multiplier,
            moving,
            gates,
            crumble,
            boss,
        )
