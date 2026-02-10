from __future__ import annotations

import sys
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pygame

from . import settings
from .audio_packs import get_pack, ordered_unlocked as ordered_audio
from .food import Food
from .grid import Grid
from .levels import LevelManager
from .obstacles import ObstacleManager
from .powerups.base import PowerUp
from .snake import DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP, Snake
from .spawner import Spawner
from .states import GameState
from .storage import Storage
from .ui import UI
from .skins import get_skin, ordered_unlocked as ordered_skins
from .utils import AudioManager, lerp, now_seconds

Position = Tuple[int, int]


@dataclass
class Game:
    """Main game controller and state machine."""

    seed: Optional[int] = None

    def __post_init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption("Advanced Snake")
        self.clock = pygame.time.Clock()
        self.running = True

        self.grid = Grid(settings.GRID_WIDTH, settings.GRID_HEIGHT, settings.CELL_SIZE, settings.HUD_HEIGHT)
        self.ui = UI(self.screen)
        self.storage = Storage(settings.DATA_DIR)
        self.profile = self.storage.load_profile()
        self.audio = AudioManager(self.profile.get("muted", settings.AUDIO_MUTED_DEFAULT))
        self.skin = get_skin(self.profile.get("selected_skin", settings.DEFAULT_SKIN_ID))
        self.ui.set_skin(self.skin)
        self.spawner = Spawner(self.grid, seed=self.seed)
        self.obstacles = ObstacleManager()
        self.levels = LevelManager()

        self.state = GameState.MENU
        self.menu_items = ["Start Game", "Customize", "View Stats", "Controls", "Quit"]
        self.pause_items = ["Resume", "Restart", "Menu"]
        self.game_over_items = ["Restart", "Menu", "Quit"]
        self.menu_index = 0
        self.pause_index = 0
        self.game_over_index = 0
        self.customize_items = ["Skin", "Audio Pack", "Mute", "Back"]
        self.customize_index = 0

        self.snake: Snake
        self.food: Optional[Food]
        self.powerup: Optional[PowerUp]
        self.effects_end: Dict[str, float] = {}
        self.shield_charge = 0
        self.tick_accumulator = 0.0
        self.level_intro_end = 0.0

        self.score = 0
        self.foods_eaten = 0
        self.powerups_collected: Dict[str, int] = {"speed": 0, "shrink": 0, "freeze": 0, "shield": 0}
        self.streak = 0
        self.last_food_time = 0.0
        self.run_start_time = 0.0
        self.max_length = settings.SNAKE_START_LENGTH
        self.last_run_data: Dict[str, str] = {}
        self.new_high_score = False
        self.new_unlocks: List[str] = []
        self.unlocked_skins: List[str] = []
        self.unlocked_audio: List[str] = []

        self.next_powerup_time = 0.0

        self.apply_profile()

        self.start_new_game()
        self.state = GameState.MENU

    def start_new_game(self) -> None:
        """Initialize a new run."""
        self.snake = Snake.create_centered(
            settings.GRID_WIDTH,
            settings.GRID_HEIGHT,
            settings.SNAKE_START_LENGTH,
            settings.SNAKE_MIN_LENGTH,
        )
        self.snake.reset_render_state()
        self.food = None
        self.powerup = None
        self.effects_end.clear()
        self.shield_charge = 0
        self.tick_accumulator = 0.0
        self.score = 0
        self.foods_eaten = 0
        self.powerups_collected = {"speed": 0, "shrink": 0, "freeze": 0, "shield": 0}
        self.streak = 0
        self.last_food_time = 0.0
        self.run_start_time = now_seconds()
        self.max_length = settings.SNAKE_START_LENGTH
        self.levels.level = 1
        self.level_intro_end = self.run_start_time + settings.LEVEL_INTRO_DURATION

        config = self.levels.config()
        self.obstacles.build_for_level(config, self.grid, set(self.snake.body()), self.snake.head(), seed=self.seed)
        self.food = self.spawner.spawn_food(self.blocked_cells(), self.snake.head())
        self.next_powerup_time = self.run_start_time + config.powerup_interval

    def apply_profile(self) -> None:
        """Apply profile settings for skin and audio."""
        profile = self.storage.load_profile()
        unlocked_skins = ordered_skins(profile.get("unlocked_skins", []))
        unlocked_audio = ordered_audio(profile.get("unlocked_audio", []))

        selected_skin = profile.get("selected_skin", settings.DEFAULT_SKIN_ID)
        if selected_skin not in unlocked_skins:
            selected_skin = unlocked_skins[0]
            profile["selected_skin"] = selected_skin

        selected_audio = profile.get("selected_audio", settings.DEFAULT_AUDIO_PACK_ID)
        if selected_audio not in unlocked_audio:
            selected_audio = unlocked_audio[0]
            profile["selected_audio"] = selected_audio

        self.profile = profile
        self.unlocked_skins = unlocked_skins
        self.unlocked_audio = unlocked_audio
        self.skin = get_skin(selected_skin)
        self.ui.set_skin(self.skin)

        self.audio.set_muted(bool(profile.get("muted", settings.AUDIO_MUTED_DEFAULT)))
        self.audio.set_volumes(
            float(profile.get("sfx_volume", settings.SFX_VOLUME_DEFAULT)),
            float(profile.get("music_volume", settings.MUSIC_VOLUME_DEFAULT)),
        )
        self.audio.load_pack(selected_audio)

        self.storage.save_profile(profile)

    def customize_display_items(self) -> List[str]:
        skin_label = f"Skin: {self.skin.name}"
        audio_pack = get_pack(self.profile.get("selected_audio", settings.DEFAULT_AUDIO_PACK_ID))
        audio_label = f"Audio Pack: {audio_pack.name}"
        mute_label = "Mute: On" if self.profile.get("muted", settings.AUDIO_MUTED_DEFAULT) else "Mute: Off"
        return [skin_label, audio_label, mute_label, "Back"]

    def blocked_cells(self) -> List[Position]:
        """Return all positions blocked for spawning."""
        blocked = list(self.snake.body())
        blocked.extend(list(self.obstacles.all_positions(include_inactive_gates=True)))
        if self.food is not None:
            blocked.append(self.food.position)
        if self.powerup is not None:
            blocked.append(self.powerup.position)
        return blocked

    def activate_effect(self, name: str, duration: float) -> None:
        """Activate or extend a timed effect."""
        now = now_seconds()
        current_end = self.effects_end.get(name, 0.0)
        self.effects_end[name] = max(current_end, now + duration)
        if name == "shield":
            self.shield_charge = 1

    def apply_shrink(self, duration: float) -> None:
        """Apply shrink and set timed indicator."""
        self.snake.shrink(settings.SHRINK_SEGMENTS)
        self.activate_effect("shrink", duration)

    def effect_active(self, name: str) -> bool:
        """Return True if an effect is currently active."""
        now = now_seconds()
        return self.effects_end.get(name, 0.0) > now

    def consume_shield(self) -> None:
        """Consume shield charge and end shield effect."""
        self.shield_charge = 0
        self.effects_end.pop("shield", None)

    def update_effects(self) -> None:
        """Clear expired effects."""
        now = now_seconds()
        expired = [name for name, end in self.effects_end.items() if end <= now]
        for name in expired:
            self.effects_end.pop(name, None)
            if name == "shield":
                self.shield_charge = 0

    def handle_events(self) -> None:
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type != pygame.KEYDOWN:
                continue

            if self.state == GameState.MENU:
                self.handle_menu_input(event.key)
            elif self.state == GameState.PLAYING:
                self.handle_game_input(event.key)
            elif self.state == GameState.PAUSED:
                self.handle_pause_input(event.key)
            elif self.state == GameState.GAME_OVER:
                self.handle_game_over_input(event.key)
            elif self.state == GameState.STATS:
                if event.key in (pygame.K_m, pygame.K_ESCAPE):
                    self.state = GameState.MENU
            elif self.state == GameState.CONTROLS:
                if event.key in (pygame.K_m, pygame.K_ESCAPE):
                    self.state = GameState.MENU
            elif self.state == GameState.CUSTOMIZE:
                self.handle_customize_input(event.key)

    def handle_menu_input(self, key: int) -> None:
        if key in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % len(self.menu_items)
        elif key in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % len(self.menu_items)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            choice = self.menu_items[self.menu_index]
            if choice == "Start Game":
                self.start_new_game()
                self.state = GameState.PLAYING
            elif choice == "Customize":
                self.state = GameState.CUSTOMIZE
            elif choice == "View Stats":
                self.state = GameState.STATS
            elif choice == "Controls":
                self.state = GameState.CONTROLS
            elif choice == "Quit":
                self.running = False

    def handle_game_input(self, key: int) -> None:
        if key in (pygame.K_ESCAPE,):
            self.state = GameState.PAUSED
            return
        if key in (pygame.K_r,):
            self.start_new_game()
            self.state = GameState.PLAYING
            return
        if key in (pygame.K_m,):
            self.state = GameState.MENU
            return

        if key in (pygame.K_UP, pygame.K_w):
            self.snake.queue_direction(DIR_UP)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.snake.queue_direction(DIR_DOWN)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.snake.queue_direction(DIR_LEFT)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.snake.queue_direction(DIR_RIGHT)

    def handle_pause_input(self, key: int) -> None:
        if key in (pygame.K_ESCAPE,):
            self.state = GameState.PLAYING
            return
        if key in (pygame.K_DOWN, pygame.K_s):
            self.pause_index = (self.pause_index + 1) % len(self.pause_items)
        elif key in (pygame.K_UP, pygame.K_w):
            self.pause_index = (self.pause_index - 1) % len(self.pause_items)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            choice = self.pause_items[self.pause_index]
            if choice == "Resume":
                self.state = GameState.PLAYING
            elif choice == "Restart":
                self.start_new_game()
                self.state = GameState.PLAYING
            elif choice == "Menu":
                self.state = GameState.MENU

    def handle_game_over_input(self, key: int) -> None:
        if key in (pygame.K_DOWN, pygame.K_s):
            self.game_over_index = (self.game_over_index + 1) % len(self.game_over_items)
        elif key in (pygame.K_UP, pygame.K_w):
            self.game_over_index = (self.game_over_index - 1) % len(self.game_over_items)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_r):
            choice = self.game_over_items[self.game_over_index]
            if key == pygame.K_r:
                choice = "Restart"
            if choice == "Restart":
                self.start_new_game()
                self.state = GameState.PLAYING
            elif choice == "Menu":
                self.state = GameState.MENU
            elif choice == "Quit":
                self.running = False
        elif key in (pygame.K_m,):
            self.state = GameState.MENU

    def handle_customize_input(self, key: int) -> None:
        if key in (pygame.K_m, pygame.K_ESCAPE):
            self.state = GameState.MENU
            return
        if key in (pygame.K_DOWN, pygame.K_s):
            self.customize_index = (self.customize_index + 1) % len(self.customize_items)
            return
        if key in (pygame.K_UP, pygame.K_w):
            self.customize_index = (self.customize_index - 1) % len(self.customize_items)
            return

        if key in (pygame.K_LEFT, pygame.K_a):
            self.adjust_customize(-1)
            return
        if key in (pygame.K_RIGHT, pygame.K_d):
            self.adjust_customize(1)
            return
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.customize_items[self.customize_index] == "Back":
                self.state = GameState.MENU

    def adjust_customize(self, direction: int) -> None:
        item = self.customize_items[self.customize_index]
        if item == "Skin":
            self.cycle_skin(direction)
        elif item == "Audio Pack":
            self.cycle_audio(direction)
        elif item == "Mute":
            self.profile["muted"] = not bool(self.profile.get("muted", settings.AUDIO_MUTED_DEFAULT))
            self.storage.save_profile(self.profile)
            self.apply_profile()

    def cycle_skin(self, direction: int) -> None:
        if not self.unlocked_skins:
            return
        current = self.profile.get("selected_skin", settings.DEFAULT_SKIN_ID)
        if current not in self.unlocked_skins:
            current = self.unlocked_skins[0]
        idx = self.unlocked_skins.index(current)
        idx = (idx + direction) % len(self.unlocked_skins)
        self.profile["selected_skin"] = self.unlocked_skins[idx]
        self.storage.save_profile(self.profile)
        self.apply_profile()

    def cycle_audio(self, direction: int) -> None:
        if not self.unlocked_audio:
            return
        current = self.profile.get("selected_audio", settings.DEFAULT_AUDIO_PACK_ID)
        if current not in self.unlocked_audio:
            current = self.unlocked_audio[0]
        idx = self.unlocked_audio.index(current)
        idx = (idx + direction) % len(self.unlocked_audio)
        self.profile["selected_audio"] = self.unlocked_audio[idx]
        self.storage.save_profile(self.profile)
        self.apply_profile()

    def update(self, dt: float) -> None:
        """Update the game logic."""
        if self.state != GameState.PLAYING:
            return

        self.update_effects()
        now = now_seconds()
        elapsed = now - self.run_start_time

        self.obstacles.update(dt, self.grid, set(self.snake.body()))
        if self.food and self.obstacles.blocks_spawn(self.food.position):
            self.food = None
        if self.powerup and self.obstacles.blocks_spawn(self.powerup.position):
            self.powerup = None

        if self.levels.update(self.score, elapsed):
            config = self.levels.config()
            self.obstacles.build_for_level(config, self.grid, set(self.snake.body()), self.snake.head(), seed=self.seed)
            self.level_intro_end = now + settings.LEVEL_INTRO_DURATION
            if self.food and self.obstacles.blocks_spawn(self.food.position):
                self.food = None
            if self.powerup and self.obstacles.blocks_spawn(self.powerup.position):
                self.powerup = None
            self.audio.play("boss" if config.boss else "level")

        config = self.levels.config()
        speed_multiplier = settings.SPEED_BOOST_MULTIPLIER if self.effect_active("speed") else 1.0
        effective_tick_rate = config.tick_rate * speed_multiplier
        tick_interval = 1.0 / max(1e-6, effective_tick_rate)

        if self.effect_active("freeze"):
            self.tick_accumulator = 0.0
        else:
            self.tick_accumulator += dt
            while self.tick_accumulator >= tick_interval:
                self.tick_accumulator -= tick_interval
                self.tick()

        if self.food is None:
            self.food = self.spawner.spawn_food(self.blocked_cells(), self.snake.head())

        if self.powerup is None and now >= self.next_powerup_time:
            self.powerup = self.spawner.spawn_powerup(self.blocked_cells(), self.snake.head(), settings.POWERUP_WEIGHTS)
            if self.powerup is not None:
                self.next_powerup_time = now + config.powerup_interval
            else:
                self.next_powerup_time = now + 1.0

    def tick(self) -> None:
        """Advance game by one tick."""
        if self.effect_active("freeze"):
            return

        new_head = self.snake.tick()
        if not self.grid.in_bounds(new_head) or self.obstacles.collides(new_head) or self.snake.will_collide_with_self(new_head):
            if self.effect_active("shield") and self.shield_charge > 0:
                self.consume_shield()
                self.snake.positions = deque(self.snake.last_positions)
                self.snake.reset_render_state()
                return
            self.audio.play("death")
            self.game_over()
            return

        if self.food and new_head == self.food.position:
            self.foods_eaten += 1
            self.snake.grow(settings.FOOD_GROWTH)
            self.food = None
            self.audio.play("eat")
            now = now_seconds()
            if now - self.last_food_time <= settings.STREAK_WINDOW:
                self.streak += 1
            else:
                self.streak = 1
            self.last_food_time = now

            bonus = (self.streak - 1) * settings.STREAK_BONUS
            level_multiplier = self.levels.config().score_multiplier
            speed_bonus = settings.SPEED_BONUS if self.effect_active("speed") else 0
            gained = int((settings.BASE_FOOD_SCORE + bonus + speed_bonus) * level_multiplier)
            self.score += gained

        if self.powerup and new_head == self.powerup.position:
            self.powerup.apply(self)
            name = self.powerup.name
            self.powerups_collected[name] = self.powerups_collected.get(name, 0) + 1
            self.powerup = None
            self.audio.play("powerup")

        self.max_length = max(self.max_length, len(self.snake.positions))

    def game_over(self) -> None:
        """Handle game over logic and persist stats."""
        self.state = GameState.GAME_OVER
        duration = now_seconds() - self.run_start_time
        run = {
            "score": self.score,
            "level": self.levels.level,
            "duration": round(duration, 2),
            "foods": self.foods_eaten,
            "powerups": self.powerups_collected,
            "max_length": self.max_length,
        }

        from datetime import datetime

        run["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.new_high_score = self.storage.record_run(run)
        unlock_report = self.storage.update_unlocks()
        self.new_unlocks = []
        for skin_id in unlock_report.get("skins", []):
            self.new_unlocks.append(f"Skin: {get_skin(skin_id).name}")
        for pack_id in unlock_report.get("audio", []):
            self.new_unlocks.append(f"Audio: {get_pack(pack_id).name}")
        if self.new_unlocks:
            self.apply_profile()
        self.last_run_data = {
            "Score": str(run["score"]),
            "Level": str(run["level"]),
            "Duration": f"{run['duration']}s",
            "Foods": str(run["foods"]),
            "Power-ups": ", ".join(f"{k}:{v}" for k, v in run["powerups"].items()),
            "Max Length": str(run["max_length"]),
        }
        if self.new_unlocks:
            self.last_run_data["Unlocked"] = ", ".join(self.new_unlocks)

    def draw_grid(self) -> None:
        """Draw the background grid."""
        for x in range(settings.GRID_WIDTH + 1):
            px = x * settings.CELL_SIZE
            pygame.draw.line(
                self.screen,
                self.skin.colors["grid"],
                (px, settings.HUD_HEIGHT),
                (px, settings.SCREEN_HEIGHT),
                1,
            )
        for y in range(settings.GRID_HEIGHT + 1):
            py = settings.HUD_HEIGHT + y * settings.CELL_SIZE
            pygame.draw.line(
                self.screen,
                self.skin.colors["grid"],
                (0, py),
                (settings.SCREEN_WIDTH, py),
                1,
            )

    def draw_playfield(self) -> None:
        """Draw the playfield elements."""
        self.screen.fill(self.skin.colors["bg"])
        self.draw_grid()

        for pos in self.obstacles.obstacles:
            px, py = self.grid.to_pixel(pos)
            rect = pygame.Rect(px, py, settings.CELL_SIZE, settings.CELL_SIZE)
            pygame.draw.rect(self.screen, self.skin.colors["obstacle"], rect)

        for pos in self.obstacles.boss_core:
            px, py = self.grid.to_pixel(pos)
            rect = pygame.Rect(px, py, settings.CELL_SIZE, settings.CELL_SIZE)
            pygame.draw.rect(self.screen, self.skin.colors["boss_core"], rect)

        for mover in self.obstacles.moving:
            px, py = self.grid.to_pixel(mover.position)
            rect = pygame.Rect(px + 2, py + 2, settings.CELL_SIZE - 4, settings.CELL_SIZE - 4)
            pygame.draw.rect(self.screen, self.skin.colors["hazard_moving"], rect)

        for gate in self.obstacles.gates:
            px, py = self.grid.to_pixel(gate.position)
            rect = pygame.Rect(px + 2, py + 2, settings.CELL_SIZE - 4, settings.CELL_SIZE - 4)
            color = self.skin.colors["hazard_gate_on"] if gate.active else self.skin.colors["hazard_gate_off"]
            pygame.draw.rect(self.screen, color, rect, 0 if gate.active else 2)

        if self.obstacles.crumbling:
            now = now_seconds()
            for pos, end in self.obstacles.crumbling.items():
                px, py = self.grid.to_pixel(pos)
                rect = pygame.Rect(px + 3, py + 3, settings.CELL_SIZE - 6, settings.CELL_SIZE - 6)
                fade = max(0.0, min(1.0, (end - now) / max(1e-6, settings.CRUMBLE_LIFETIME)))
                base = self.skin.colors["hazard_crumble"]
                bg = self.skin.colors["bg"]
                color = (
                    int(lerp(bg[0], base[0], fade)),
                    int(lerp(bg[1], base[1], fade)),
                    int(lerp(bg[2], base[2], fade)),
                )
                pygame.draw.rect(self.screen, color, rect)

        if self.food:
            px, py = self.grid.to_pixel(self.food.position)
            rect = pygame.Rect(px + 4, py + 4, settings.CELL_SIZE - 8, settings.CELL_SIZE - 8)
            pygame.draw.rect(self.screen, self.skin.colors["food"], rect)

        if self.powerup:
            px, py = self.grid.to_pixel(self.powerup.position)
            rect = pygame.Rect(px + 4, py + 4, settings.CELL_SIZE - 8, settings.CELL_SIZE - 8)
            pygame.draw.rect(self.screen, self.powerup.color, rect)
            icon = self.ui.font_small.render(self.powerup.icon, True, (0, 0, 0))
            icon_rect = icon.get_rect(center=rect.center)
            self.screen.blit(icon, icon_rect)

        config = self.levels.config()
        speed_multiplier = settings.SPEED_BOOST_MULTIPLIER if self.effect_active("speed") else 1.0
        effective_tick_rate = config.tick_rate * speed_multiplier
        tick_interval = 1.0 / max(1e-6, effective_tick_rate)
        alpha = min(1.0, self.tick_accumulator / tick_interval)
        positions = self.snake.render_positions(alpha)

        for idx, (x, y) in enumerate(positions):
            px = int(x * settings.CELL_SIZE)
            py = int(y * settings.CELL_SIZE + settings.HUD_HEIGHT)
            rect = pygame.Rect(px + 2, py + 2, settings.CELL_SIZE - 4, settings.CELL_SIZE - 4)
            color = self.skin.colors["snake_head"] if idx == 0 else self.skin.colors["snake_body"]
            pygame.draw.rect(self.screen, color, rect)

        effects_remaining = {name: max(0.0, end - now_seconds()) for name, end in self.effects_end.items()}
        self.ui.draw_hud(self.score, self.levels.level, effective_tick_rate, effects_remaining, config.boss)
        self.ui.draw_footer()

        if now_seconds() <= self.level_intro_end:
            self.ui.draw_level_intro(self.levels.config())

    def draw(self) -> None:
        """Render the current frame."""
        if self.state == GameState.MENU:
            self.ui.draw_menu("Advanced Snake", self.menu_items, self.menu_index)
        elif self.state == GameState.PLAYING:
            self.draw_playfield()
        elif self.state == GameState.PAUSED:
            self.draw_playfield()
            self.ui.draw_pause(self.pause_items, self.pause_index)
        elif self.state == GameState.GAME_OVER:
            self.ui.draw_game_over(self.last_run_data, self.new_high_score, self.game_over_items, self.game_over_index)
        elif self.state == GameState.STATS:
            stats = self.storage.get_stats()
            highscores = self.storage.get_highscores()
            pretty_stats = {
                "Total Runs": str(stats.get("total_runs", 0)),
                "Total Food": str(stats.get("total_food", 0)),
                "Total Time": f"{stats.get('total_time', 0.0):.1f}s",
                "Average Score": f"{stats.get('average_score', 0.0):.1f}",
                "Best Score": str(stats.get("best_score", 0)),
                "Longest Snake": str(stats.get("longest_snake", 0)),
                "Power-ups": ", ".join(f"{k}:{v}" for k, v in stats.get("powerups", {}).items()),
            }
            self.ui.draw_stats(pretty_stats, highscores)
        elif self.state == GameState.CONTROLS:
            self.ui.draw_controls()
        elif self.state == GameState.CUSTOMIZE:
            items = self.customize_display_items()
            self.ui.draw_customize(items, self.customize_index)

        pygame.display.flip()

    def run(self) -> None:
        """Main loop."""
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

        self.audio.stop_music()
        pygame.quit()
        sys.exit(0)
