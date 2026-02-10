from __future__ import annotations

from pathlib import Path

from src.storage import Storage


def test_storage_read_write(tmp_path: Path) -> None:
    storage = Storage(tmp_path)
    run = {
        "score": 120,
        "level": 2,
        "duration": 33.5,
        "foods": 6,
        "powerups": {"speed": 1, "shrink": 0, "freeze": 1, "shield": 0},
        "max_length": 8,
        "date": "2026-02-10 12:00:00",
    }
    is_high = storage.record_run(run)
    assert is_high is True

    highscores = storage.get_highscores()
    assert highscores
    assert highscores[0]["score"] == 120

    stats = storage.get_stats()
    assert stats["total_runs"] == 1
    assert stats["total_food"] == 6
    assert stats["best_score"] == 120

    profile = storage.load_profile()
    assert profile["selected_skin"]
    assert profile["selected_audio"]
