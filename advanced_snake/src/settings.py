# Advanced Snake - Settings
# Tuning section: adjust these values to rebalance difficulty quickly.

from __future__ import annotations

from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
AUDIO_DIR = ASSETS_DIR / "audio"

# --- Display ---
GRID_WIDTH = 30
GRID_HEIGHT = 20
CELL_SIZE = 24
HUD_HEIGHT = 80
FPS = 60

SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE + HUD_HEIGHT

# --- Colors ---
COLOR_BG = (20, 24, 28)
COLOR_GRID = (30, 35, 40)
COLOR_TEXT = (220, 220, 220)
COLOR_ACCENT = (80, 180, 120)

COLOR_SNAKE_HEAD = (60, 200, 120)
COLOR_SNAKE_BODY = (40, 150, 90)
COLOR_FOOD = (220, 80, 60)
COLOR_OBSTACLE = (110, 110, 140)

# --- Snake ---
SNAKE_START_LENGTH = 4
SNAKE_MIN_LENGTH = 3

# --- Movement / Ticks ---
BASE_TICK_RATE = 8.0  # ticks per second at level 1
TICK_RATE_INCREMENT = 0.7
MAX_TICK_RATE = 18.0

# --- Levels ---
SCORE_PER_LEVEL = 120
TIME_PER_LEVEL = 45.0  # seconds survived per level
MAX_LEVEL = 12
LEVEL_INTRO_DURATION = 1.5  # seconds

BASE_OBSTACLES = 6
OBSTACLE_INCREMENT = 2
OBSTACLE_BLOCK_MAX = 3  # max block size for obstacle clusters

BASE_POWERUP_INTERVAL = 9.0  # seconds
POWERUP_INTERVAL_DECREMENT = 0.4
MIN_POWERUP_INTERVAL = 3.5

# --- Spawning ---
MIN_SPAWN_DISTANCE = 4  # minimum Manhattan distance from snake head
FOOD_GROWTH = 1

# --- Scoring ---
BASE_FOOD_SCORE = 10
STREAK_WINDOW = 3.0  # seconds
STREAK_BONUS = 4  # bonus per streak count after first
LEVEL_SCORE_MULTIPLIER = 0.12  # per level multiplier
SPEED_BONUS = 3  # extra points per food when speed boost is active

# --- Power-ups ---
POWERUP_WEIGHTS = {
    "speed": 3,
    "shrink": 2,
    "freeze": 2,
    "shield": 1,
}

SPEED_BOOST_MULTIPLIER = 1.6
SPEED_DURATION = 6.0
SHRINK_DURATION = 5.0
SHRINK_SEGMENTS = 3
FREEZE_DURATION = 4.0
SHIELD_DURATION = 8.0

# --- Audio ---
AUDIO_MUTED_DEFAULT = True
SFX_VOLUME_DEFAULT = 0.6
MUSIC_VOLUME_DEFAULT = 0.4
DEFAULT_SKIN_ID = "classic"
DEFAULT_AUDIO_PACK_ID = "chip"

# --- Hazards ---
MOVING_OBSTACLES_START_LEVEL = 3
MOVING_OBSTACLES_EVERY_LEVEL = 2
MOVING_OBSTACLES_MAX = 6
MOVING_STEP_INTERVAL = 0.35

GATE_START_LEVEL = 4
GATE_EVERY_LEVEL = 3
GATE_MAX = 6
GATE_ON_DURATION = 2.4
GATE_OFF_DURATION = 2.0

CRUMBLE_START_LEVEL = 5
CRUMBLE_EVERY_LEVEL = 2
CRUMBLE_MAX = 10
CRUMBLE_LIFETIME = 7.0

# --- Boss Levels ---
BOSS_EVERY_LEVEL = 5
BOSS_TICK_BONUS = 2.0
BOSS_OBSTACLE_BONUS = 5
BOSS_SCORE_MULTIPLIER_BONUS = 0.35
BOSS_POWERUP_INTERVAL_MULT = 1.4
BOSS_MOVING_BONUS = 2
BOSS_GATE_BONUS = 2
BOSS_CRUMBLE_BONUS = 3

# --- Determinism ---
DEFAULT_SEED = None
