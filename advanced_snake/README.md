# Advanced Snake

A production-quality Pygame Snake variant with power-ups, dynamic levels, obstacles, and persistent stats.

**How to run**
1. `pip install -r requirements.txt`
2. `python main.py`

Optional deterministic run:
`python main.py --seed 1234`

**Controls**
- `Arrow Keys` or `WASD`: Move
- `Esc`: Pause
- `R`: Restart
- `M`: Menu
- `Enter`: Select
- `Left/Right`: Adjust options in Customize

**Power-ups**
- Speed Boost (`S`): Increases tick rate for a short duration. Also grants extra points per food while active.
- Shrink (`K`): Instantly removes a few tail segments and shows a timed indicator.
- Freeze (`F`): Freezes snake movement for a short duration. Timers keep running while frozen.
- Shield (`D`): Blocks one collision while active.

Power-up stacking: collecting the same power-up refreshes its timer. Different power-ups can overlap.

**Level progression rules**
- Level increases based on score and time survived.
- Every level increases tick rate and obstacle count.
- Power-up spawn interval decreases as levels rise.
- A brief level intro overlay shows the new modifiers.
- Boss levels occur every few levels and add extra hazard pressure.

**Hazards**
- Moving blocks: drift across the grid and bounce off walls.
- Timed gates: toggle between solid and passable.
- Crumbling tiles: disappear after a short time, opening new routes.

**Skins + Audio Packs**
- Unlock skins and audio packs by hitting score and run milestones.
- Choose them from the `Customize` menu.
- Audio is muted by default; toggle it in `Customize`.

**Scoring**
- Base points per food plus streak bonuses for quick consecutive eats.
- Level multiplier applies to each food.
- Speed Boost adds a small extra bonus per food.

**Persistence files**
Stored in `data/`.

`highscores.json`
- `runs`: top 10 runs, each with `score`, `level`, `duration`, `foods`, `powerups`, `max_length`, `date`.
- `best_run`: highest scoring run.

`stats.json`
- `total_runs`, `total_deaths`, `total_food`, `total_time`, `total_score`
- `powerups` usage counts
- `average_score`, `best_score`, `longest_snake`

**Freeze mechanic**
Freeze stops snake movement only. Obstacles and timers continue. The effect ends after its duration.
