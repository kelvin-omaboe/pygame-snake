from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class AudioPack:
    """Audio pack definition for SFX and music."""

    id: str
    name: str
    sfx: Dict[str, str]
    music: List[str]


PACK_ORDER: List[str] = ["chip", "drift"]

PACKS: Dict[str, AudioPack] = {
    "chip": AudioPack(
        id="chip",
        name="Chip Pulse",
        sfx={
            "eat": "eat.wav",
            "powerup": "powerup.wav",
            "level": "level.wav",
            "boss": "boss.wav",
            "death": "death.wav",
        },
        music=["game.wav"],
    ),
    "drift": AudioPack(
        id="drift",
        name="Night Drift",
        sfx={
            "eat": "eat.wav",
            "powerup": "powerup.wav",
            "level": "level.wav",
            "boss": "boss.wav",
            "death": "death.wav",
        },
        music=["game.wav"],
    ),
}

UNLOCK_RULES: Dict[str, Dict[str, int]] = {
    "drift": {"best_score": 400},
}


def default_pack_id() -> str:
    return "chip"


def get_pack(pack_id: str) -> AudioPack:
    return PACKS.get(pack_id, PACKS[default_pack_id()])


def ordered_unlocked(unlocked: List[str]) -> List[str]:
    order = [pack_id for pack_id in PACK_ORDER if pack_id in unlocked]
    if default_pack_id() not in order:
        order.insert(0, default_pack_id())
    return order


def unlock_packs(stats: Dict[str, int], unlocked: List[str]) -> List[str]:
    newly_unlocked: List[str] = []
    for pack_id, requirements in UNLOCK_RULES.items():
        if pack_id in unlocked:
            continue
        if all(int(stats.get(key, 0)) >= value for key, value in requirements.items()):
            unlocked.append(pack_id)
            newly_unlocked.append(pack_id)
    return newly_unlocked
