#!/usr/bin/env python3
"""starfield — animated purple starfield in the terminal.

Stars drift downward at varying speeds, creating depth. Some are
bright, some are dim. Some are purple, some are violet, some are
nearly white. It's a screensaver for witches.

Usage:
    python3 starfield.py              # stars fall forever
    python3 starfield.py --density 3  # more stars (1-5, default 2)
    python3 starfield.py --speed 2    # faster (0.5-3, default 1)

Ctrl-C to stop. Stdlib-only. Persists nothing.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time

# Star characters by "brightness" tier
STAR_CHARS = [
    ("·", 0.4),   # dim
    ("∘", 0.5),
    ("✧", 0.6),
    ("⋆", 0.7),
    ("✦", 0.85),  # bright
    ("★", 1.0),   # brightest (rare)
]

# Color palette — purple-violet spectrum with occasional warm tones
STAR_COLORS = [
    (90, 70, 160),    # deep purple
    (110, 90, 180),   # indigo
    (123, 104, 238),  # medium slate blue (Netzach)
    (140, 115, 240),  # violet
    (155, 125, 255),  # bright violet
    (180, 150, 255),  # lavender
    (200, 180, 255),  # pale violet
    (220, 200, 255),  # near-white violet
    (255, 240, 255),  # white-pink (rare bright star)
    (255, 200, 230),  # pink (Venus)
]


def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


def _move(x: int, y: int) -> str:
    return f"\033[{y};{x}H"


def get_terminal_size() -> tuple[int, int]:
    try:
        return os.get_terminal_size()
    except OSError:
        return 80, 24


class Star:
    __slots__ = ("x", "y", "speed", "char", "color", "twinkle_phase")

    def __init__(self, x: float, y: float, speed: float,
                 char: str, color: tuple[int, int, int]):
        self.x = x
        self.y = y
        self.speed = speed
        self.char = char
        self.color = color
        self.twinkle_phase = random.random() * 6.28

    @classmethod
    def spawn(cls, cols: int, y: float | None = None) -> Star:
        x = random.uniform(1, cols - 1)
        if y is None:
            y = 0.0
        # Depth: slower = farther = dimmer
        depth = random.random()  # 0 = far, 1 = near
        speed = 0.1 + depth * 0.6

        # Pick character based on depth
        if depth < 0.3:
            char = random.choice(["·", "∘"])
        elif depth < 0.7:
            char = random.choice(["✧", "⋆"])
        else:
            char = random.choice(["✦", "★"])

        # Pick color — brighter/warmer for closer stars
        if depth < 0.3:
            color = random.choice(STAR_COLORS[:4])
        elif depth < 0.7:
            color = random.choice(STAR_COLORS[3:7])
        else:
            color = random.choice(STAR_COLORS[6:])

        return cls(x, y, speed, char, color)


def main() -> int:
    parser = argparse.ArgumentParser(description="starfield — purple stars")
    parser.add_argument("--density", type=float, default=2,
                        help="star density 1-5 (default 2)")
    parser.add_argument("--speed", type=float, default=1,
                        help="speed multiplier (default 1)")
    args = parser.parse_args()

    if not sys.stdout.isatty():
        print("✧ ⋆ ✦ · ∘ ✧ ⋆ ✦ · ∘ ✧")
        return 0

    cols, rows = get_terminal_size()
    density = max(0.5, min(5, args.density))
    speed_mult = max(0.2, min(3, args.speed))

    # Initialize stars scattered across the screen
    stars: list[Star] = []
    for _ in range(int(cols * rows * 0.02 * density)):
        stars.append(Star.spawn(cols, random.uniform(1, rows)))

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.write("\033[2J")  # clear
    sys.stdout.flush()

    spawn_rate = 0.3 * density
    tick = 0

    try:
        while True:
            cols, rows = get_terminal_size()

            # Spawn new stars at the top
            if random.random() < spawn_rate:
                stars.append(Star.spawn(cols))

            # Build frame
            buf = ["\033[2J"]  # clear screen

            # Title (faint, top center)
            title = "✦ starfield ✦"
            tx = cols // 2 - len(title) // 2
            buf.append(f"{_move(tx, 1)}{_fg(50, 40, 80)}{title}{RESET}")

            alive: list[Star] = []
            for s in stars:
                s.y += s.speed * speed_mult
                iy = int(s.y)
                ix = int(s.x)

                if iy < 1 or iy > rows or ix < 1 or ix > cols:
                    continue

                # Twinkle: modulate brightness
                import math
                twinkle = 0.6 + 0.4 * math.sin(tick * 0.15 + s.twinkle_phase)
                r = int(s.color[0] * twinkle)
                g = int(s.color[1] * twinkle)
                b = int(s.color[2] * twinkle)

                buf.append(f"{_move(ix, iy)}{_fg(r, g, b)}{s.char}{RESET}")
                alive.append(s)

            stars = alive
            sys.stdout.write("".join(buf))
            sys.stdout.flush()
            time.sleep(0.07)
            tick += 1

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.write("\033[2J")
        sys.stdout.write(_move(1, 1))
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    sys.exit(main())
