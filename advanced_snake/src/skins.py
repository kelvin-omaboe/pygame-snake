from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from . import settings

Color = Tuple[int, int, int]


@dataclass(frozen=True)
class Skin:
    """Color palette for the game."""

    id: str
    name: str
    colors: Dict[str, Color]


SKIN_ORDER: List[str] = ["classic", "neon", "glacier", "desert"]

SKINS: Dict[str, Skin] = {
    "classic": Skin(
        id="classic",
        name="Classic",
        colors={
            "bg": settings.COLOR_BG,
            "grid": settings.COLOR_GRID,
            "text": settings.COLOR_TEXT,
            "accent": settings.COLOR_ACCENT,
            "snake_head": settings.COLOR_SNAKE_HEAD,
            "snake_body": settings.COLOR_SNAKE_BODY,
            "food": settings.COLOR_FOOD,
            "obstacle": settings.COLOR_OBSTACLE,
            "hazard_moving": (150, 120, 200),
            "hazard_gate_on": (220, 120, 80),
            "hazard_gate_off": (80, 80, 90),
            "hazard_crumble": (180, 150, 90),
            "boss_core": (200, 80, 120),
        },
    ),
    "neon": Skin(
        id="neon",
        name="Neon Drift",
        colors={
            "bg": (10, 12, 20),
            "grid": (24, 30, 46),
            "text": (230, 235, 245),
            "accent": (70, 220, 255),
            "snake_head": (90, 255, 200),
            "snake_body": (40, 210, 160),
            "food": (255, 90, 200),
            "obstacle": (120, 110, 190),
            "hazard_moving": (190, 120, 255),
            "hazard_gate_on": (255, 140, 90),
            "hazard_gate_off": (70, 70, 95),
            "hazard_crumble": (210, 170, 90),
            "boss_core": (255, 80, 140),
        },
    ),
    "glacier": Skin(
        id="glacier",
        name="Glacier",
        colors={
            "bg": (12, 18, 24),
            "grid": (32, 46, 58),
            "text": (225, 240, 250),
            "accent": (120, 200, 230),
            "snake_head": (90, 180, 255),
            "snake_body": (60, 140, 220),
            "food": (255, 130, 90),
            "obstacle": (70, 90, 120),
            "hazard_moving": (130, 170, 255),
            "hazard_gate_on": (255, 150, 110),
            "hazard_gate_off": (70, 80, 100),
            "hazard_crumble": (190, 200, 210),
            "boss_core": (140, 120, 220),
        },
    ),
    "desert": Skin(
        id="desert",
        name="Desert Heat",
        colors={
            "bg": (34, 26, 20),
            "grid": (50, 40, 30),
            "text": (240, 230, 210),
            "accent": (220, 180, 90),
            "snake_head": (120, 210, 90),
            "snake_body": (90, 170, 70),
            "food": (240, 120, 60),
            "obstacle": (120, 90, 60),
            "hazard_moving": (200, 140, 80),
            "hazard_gate_on": (255, 160, 90),
            "hazard_gate_off": (90, 70, 50),
            "hazard_crumble": (200, 160, 110),
            "boss_core": (220, 110, 80),
        },
    ),
}

UNLOCK_RULES: Dict[str, Dict[str, int]] = {
    "neon": {"best_score": 250},
    "glacier": {"longest_snake": 18},
    "desert": {"total_food": 180},
}


def default_skin_id() -> str:
    return "classic"


def get_skin(skin_id: str) -> Skin:
    return SKINS.get(skin_id, SKINS[default_skin_id()])


def ordered_unlocked(unlocked: List[str]) -> List[str]:
    order = [skin_id for skin_id in SKIN_ORDER if skin_id in unlocked]
    if default_skin_id() not in order:
        order.insert(0, default_skin_id())
    return order


def unlock_skins(stats: Dict[str, int], unlocked: List[str]) -> List[str]:
    newly_unlocked: List[str] = []
    for skin_id, requirements in UNLOCK_RULES.items():
        if skin_id in unlocked:
            continue
        if all(int(stats.get(key, 0)) >= value for key, value in requirements.items()):
            unlocked.append(skin_id)
            newly_unlocked.append(skin_id)
    return newly_unlocked
