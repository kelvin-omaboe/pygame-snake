from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from . import settings
from .audio_packs import default_pack_id, unlock_packs
from .skins import default_skin_id, unlock_skins


@dataclass
class Storage:
    """JSON storage for highscores and lifetime stats."""

    data_dir: Path

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.highscores_path = self.data_dir / "highscores.json"
        self.stats_path = self.data_dir / "stats.json"
        self.profile_path = self.data_dir / "profile.json"
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not self.highscores_path.exists():
            self._write_json(self.highscores_path, {"runs": [], "best_run": None})
        if not self.stats_path.exists():
            self._write_json(
                self.stats_path,
                {
                    "total_runs": 0,
                    "total_deaths": 0,
                    "total_food": 0,
                    "total_time": 0.0,
                    "total_score": 0,
                    "powerups": {"speed": 0, "shrink": 0, "freeze": 0, "shield": 0},
                    "average_score": 0.0,
                    "best_score": 0,
                    "longest_snake": settings.SNAKE_START_LENGTH,
                },
            )
        if not self.profile_path.exists():
            self._write_json(
                self.profile_path,
                {
                    "selected_skin": settings.DEFAULT_SKIN_ID,
                    "selected_audio": settings.DEFAULT_AUDIO_PACK_ID,
                    "unlocked_skins": [settings.DEFAULT_SKIN_ID],
                    "unlocked_audio": [settings.DEFAULT_AUDIO_PACK_ID],
                    "muted": settings.AUDIO_MUTED_DEFAULT,
                    "sfx_volume": settings.SFX_VOLUME_DEFAULT,
                    "music_volume": settings.MUSIC_VOLUME_DEFAULT,
                },
            )

    def _read_json(self, path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def load_highscores(self) -> Dict[str, Any]:
        """Load highscores from disk."""
        return self._read_json(self.highscores_path)

    def load_stats(self) -> Dict[str, Any]:
        """Load stats from disk."""
        return self._read_json(self.stats_path)

    def load_profile(self) -> Dict[str, Any]:
        """Load profile settings from disk."""
        profile = self._read_json(self.profile_path)
        # Backfill missing keys for older profiles.
        profile.setdefault("selected_skin", settings.DEFAULT_SKIN_ID)
        profile.setdefault("selected_audio", settings.DEFAULT_AUDIO_PACK_ID)
        profile.setdefault("unlocked_skins", [settings.DEFAULT_SKIN_ID])
        profile.setdefault("unlocked_audio", [settings.DEFAULT_AUDIO_PACK_ID])
        profile.setdefault("muted", settings.AUDIO_MUTED_DEFAULT)
        profile.setdefault("sfx_volume", settings.SFX_VOLUME_DEFAULT)
        profile.setdefault("music_volume", settings.MUSIC_VOLUME_DEFAULT)
        return profile

    def save_highscores(self, data: Dict[str, Any]) -> None:
        """Save highscores to disk."""
        self._write_json(self.highscores_path, data)

    def save_stats(self, data: Dict[str, Any]) -> None:
        """Save stats to disk."""
        self._write_json(self.stats_path, data)

    def save_profile(self, data: Dict[str, Any]) -> None:
        """Save profile settings to disk."""
        self._write_json(self.profile_path, data)

    def record_run(self, run: Dict[str, Any]) -> bool:
        """Record a completed run. Returns True if new high score."""
        highscores = self.load_highscores()
        prev_best = 0
        if highscores.get("runs"):
            prev_best = highscores["runs"][0].get("score", 0)
        runs: List[Dict[str, Any]] = highscores.get("runs", [])
        runs.append(run)
        runs.sort(key=lambda r: r.get("score", 0), reverse=True)
        runs = runs[:10]
        highscores["runs"] = runs
        highscores["best_run"] = runs[0] if runs else None
        self.save_highscores(highscores)

        stats = self.load_stats()
        stats["total_runs"] = stats.get("total_runs", 0) + 1
        stats["total_deaths"] = stats.get("total_deaths", 0) + 1
        stats["total_food"] = stats.get("total_food", 0) + int(run.get("foods", 0))
        stats["total_time"] = stats.get("total_time", 0.0) + float(run.get("duration", 0.0))
        stats["total_score"] = stats.get("total_score", 0) + int(run.get("score", 0))
        stats["best_score"] = max(stats.get("best_score", 0), int(run.get("score", 0)))
        stats["longest_snake"] = max(stats.get("longest_snake", 0), int(run.get("max_length", 0)))

        powerups = stats.get("powerups", {})
        for key, value in run.get("powerups", {}).items():
            powerups[key] = powerups.get(key, 0) + int(value)
        stats["powerups"] = powerups

        total_runs = max(1, stats.get("total_runs", 1))
        stats["average_score"] = stats.get("total_score", 0) / total_runs
        self.save_stats(stats)

        best_run = highscores.get("best_run")
        return best_run is not None and int(best_run.get("score", 0)) > int(prev_best)

    def update_unlocks(self) -> Dict[str, List[str]]:
        """Update skin and audio unlocks from stats. Returns newly unlocked items."""
        stats = self.load_stats()
        profile = self.load_profile()

        unlocked_skins: List[str] = list(profile.get("unlocked_skins", []))
        unlocked_audio: List[str] = list(profile.get("unlocked_audio", []))

        new_skins = unlock_skins(stats, unlocked_skins)
        new_audio = unlock_packs(stats, unlocked_audio)

        if new_skins or new_audio:
            profile["unlocked_skins"] = unlocked_skins
            profile["unlocked_audio"] = unlocked_audio
            if profile.get("selected_skin") not in unlocked_skins:
                profile["selected_skin"] = default_skin_id()
            if profile.get("selected_audio") not in unlocked_audio:
                profile["selected_audio"] = default_pack_id()
            self.save_profile(profile)

        return {"skins": new_skins, "audio": new_audio}

    def get_highscores(self) -> List[Dict[str, Any]]:
        """Return a list of highscore runs."""
        return self.load_highscores().get("runs", [])

    def get_stats(self) -> Dict[str, Any]:
        """Return lifetime stats."""
        return self.load_stats()
