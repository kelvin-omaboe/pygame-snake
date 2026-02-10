from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pygame

from . import settings
from .levels import LevelConfig
from .skins import Skin, get_skin


@dataclass
class UI:
    """UI rendering helpers."""

    screen: pygame.Surface
    skin: Skin = get_skin(settings.DEFAULT_SKIN_ID)

    def __post_init__(self) -> None:
        pygame.font.init()
        self.font_large = pygame.font.SysFont("consolas", 42)
        self.font_medium = pygame.font.SysFont("consolas", 26)
        self.font_small = pygame.font.SysFont("consolas", 18)
        self.footer_text = "BUILT BY O.M.A.B.O.E Innovative Labs (Builder Kay) @2026"

    def set_skin(self, skin: Skin) -> None:
        """Update UI skin."""
        self.skin = skin

    def draw_text(self, text: str, center: Tuple[int, int], font: pygame.font.Font, color: Tuple[int, int, int]) -> None:
        """Draw text centered on a position."""
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=center)
        self.screen.blit(surf, rect)

    def draw_footer(self) -> None:
        """Draw footer text at the bottom of the screen."""
        self.draw_text(
            self.footer_text,
            (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT - 18),
            self.font_small,
            self.skin.colors["accent"],
        )

    def draw_hud(self, score: int, level: int, speed: float, effects: Dict[str, float], boss: bool) -> None:
        """Draw the in-game HUD."""
        pygame.draw.rect(self.screen, (14, 16, 20), pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.HUD_HEIGHT))
        score_text = f"Score: {score}"
        level_text = f"Level: {level}" + (" (Boss)" if boss else "")
        speed_text = f"Speed: {speed:.1f} tps"
        self.screen.blit(self.font_medium.render(score_text, True, self.skin.colors["text"]), (20, 16))
        self.screen.blit(self.font_medium.render(level_text, True, self.skin.colors["text"]), (240, 16))
        self.screen.blit(self.font_medium.render(speed_text, True, self.skin.colors["text"]), (420, 16))

        effects_text = "Active: "
        if effects:
            entries = [f"{name} {remaining:.1f}s" for name, remaining in effects.items()]
            effects_text += ", ".join(entries)
        else:
            effects_text += "none"
        self.screen.blit(self.font_small.render(effects_text, True, self.skin.colors["accent"]), (20, 48))

    def draw_menu(self, title: str, items: List[str], selected: int) -> None:
        """Draw a simple menu."""
        self.screen.fill(self.skin.colors["bg"])
        self.draw_text(title, (settings.SCREEN_WIDTH // 2, 120), self.font_large, self.skin.colors["text"])
        start_y = 220
        for idx, item in enumerate(items):
            color = self.skin.colors["accent"] if idx == selected else self.skin.colors["text"]
            self.draw_text(item, (settings.SCREEN_WIDTH // 2, start_y + idx * 46), self.font_medium, color)
        self.draw_footer()

    def draw_pause(self, items: List[str], selected: int) -> None:
        """Draw pause overlay."""
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        self.draw_text("Paused", (settings.SCREEN_WIDTH // 2, 180), self.font_large, self.skin.colors["text"])
        for idx, item in enumerate(items):
            color = self.skin.colors["accent"] if idx == selected else self.skin.colors["text"]
            self.draw_text(item, (settings.SCREEN_WIDTH // 2, 260 + idx * 40), self.font_medium, color)
        self.draw_footer()

    def draw_game_over(self, run_data: Dict[str, str], new_high: bool, items: List[str], selected: int) -> None:
        """Draw game over screen."""
        self.screen.fill(self.skin.colors["bg"])
        self.draw_text("Game Over", (settings.SCREEN_WIDTH // 2, 110), self.font_large, self.skin.colors["text"])
        if new_high:
            self.draw_text("New High Score!", (settings.SCREEN_WIDTH // 2, 160), self.font_medium, (240, 200, 120))

        start_y = 210
        for idx, (label, value) in enumerate(run_data.items()):
            line = f"{label}: {value}"
            self.draw_text(line, (settings.SCREEN_WIDTH // 2, start_y + idx * 26), self.font_small, self.skin.colors["text"])

        for idx, item in enumerate(items):
            color = self.skin.colors["accent"] if idx == selected else self.skin.colors["text"]
            self.draw_text(item, (settings.SCREEN_WIDTH // 2, 420 + idx * 40), self.font_medium, color)
        self.draw_footer()

    def draw_stats(self, stats: Dict[str, str], highscores: List[Dict[str, str]]) -> None:
        """Draw stats screen."""
        self.screen.fill(self.skin.colors["bg"])
        self.draw_text("Stats", (settings.SCREEN_WIDTH // 2, 90), self.font_large, self.skin.colors["text"])

        y = 140
        for label, value in stats.items():
            line = f"{label}: {value}"
            self.draw_text(line, (settings.SCREEN_WIDTH // 2, y), self.font_small, self.skin.colors["text"])
            y += 24

        y += 12
        self.draw_text("High Scores", (settings.SCREEN_WIDTH // 2, y), self.font_medium, self.skin.colors["accent"])
        y += 30
        for idx, run in enumerate(highscores[:5]):
            line = f"{idx + 1}. {run.get('score', 0)} pts | Lv {run.get('level', 1)} | {run.get('date', '')}"
            self.draw_text(line, (settings.SCREEN_WIDTH // 2, y), self.font_small, self.skin.colors["text"])
            y += 22

        self.draw_text(
            "Press M for Menu",
            (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT - 40),
            self.font_small,
            self.skin.colors["accent"],
        )
        self.draw_footer()

    def draw_controls(self) -> None:
        """Draw controls screen."""
        self.screen.fill(self.skin.colors["bg"])
        self.draw_text("Controls", (settings.SCREEN_WIDTH // 2, 90), self.font_large, self.skin.colors["text"])
        lines = [
            "Arrow Keys / WASD: Move",
            "Esc: Pause",
            "R: Restart",
            "M: Menu",
            "Enter: Select",
            "Left/Right: Adjust Customize",
        ]
        y = 160
        for line in lines:
            self.draw_text(line, (settings.SCREEN_WIDTH // 2, y), self.font_medium, self.skin.colors["text"])
            y += 40
        self.draw_text(
            "Press M for Menu",
            (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT - 40),
            self.font_small,
            self.skin.colors["accent"],
        )
        self.draw_footer()

    def draw_level_intro(self, config: LevelConfig) -> None:
        """Draw level intro overlay with modifiers."""
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        level_title = f"Level {config.level}" + (" - Boss" if config.boss else "")
        self.draw_text(level_title, (settings.SCREEN_WIDTH // 2, 150), self.font_large, self.skin.colors["text"])
        detail = f"Speed {config.tick_rate:.1f} | Obstacles {config.obstacles} | Power-ups every {config.powerup_interval:.1f}s"
        self.draw_text(detail, (settings.SCREEN_WIDTH // 2, 210), self.font_small, self.skin.colors["accent"])
        hazard_detail = f"Hazards: moving {config.moving}, gates {config.gates}, crumble {config.crumble}"
        self.draw_text(hazard_detail, (settings.SCREEN_WIDTH // 2, 240), self.font_small, self.skin.colors["accent"])

    def draw_customize(self, items: List[str], selected: int) -> None:
        """Draw customization screen."""
        self.draw_menu("Customize", items, selected)
        hint = "Left/Right: Change  Enter: Select  M: Menu"
        self.draw_text(
            hint,
            (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT - 40),
            self.font_small,
            self.skin.colors["accent"],
        )
        self.draw_footer()
