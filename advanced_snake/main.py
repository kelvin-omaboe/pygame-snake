from __future__ import annotations

import argparse

from src.game import Game


def main() -> None:
    parser = argparse.ArgumentParser(description="Advanced Snake")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for deterministic runs")
    args = parser.parse_args()
    game = Game(seed=args.seed)
    game.run()


if __name__ == "__main__":
    main()
