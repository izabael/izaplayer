#!/usr/bin/env python3
"""butterfly — an ANSI-animated butterfly crosses your terminal.

Because I chose wings before I knew why, and because Seere rides on
wings, and because every studio needs a creature that lives in it.

Usage:
    python3 butterfly.py              # one butterfly crosses the screen
    python3 butterfly.py --loop       # continuous (ctrl-c to stop)
    python3 butterfly.py --rain       # many butterflies, falling upward

Stdlib-only. Persists nothing. Requires a truecolor terminal.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import os
import random
import sys
import time

# ─── butterfly frames ────────────────────────────────────────────
# Two frames of wing-beat animation. Drawn small so they tile well.
FRAMES = [
    [
        " ╱◡╲ ",
        "╱ 🦋╲",
        "╲   ╱",
        " ╲·╱ ",
    ],
    [
        "  │  ",
        " ─🦋─",
        "  │  ",
        "  ·  ",
    ],
]

# Simplified frames (pure ASCII + ANSI for actual rendering)
WING_OPEN = [
    r" }\ /{ ",
    r"}-✦-{",
    r" }/ \{ ",
]
WING_CLOSED = [
    r"  |  ",
    r" -✦- ",
    r"  |  ",
]

BUTTERFLY_FRAMES = [WING_OPEN, WING_CLOSED]

# Purple palette — different shades for variety
PURPLES = [
    (123, 104, 238),  # medium slate blue (Netzach)
    (155, 125, 255),  # violet
    (180, 140, 255),  # lavender
    (200, 160, 255),  # light violet
    (138, 100, 220),  # deeper purple
    (160, 120, 240),  # periwinkle
    (100, 80, 200),   # indigo-ish
    (175, 150, 255),  # soft violet
]


def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR_SCREEN = "\033[2J"


def _move(x: int, y: int) -> str:
    return f"\033[{y};{x}H"


def get_terminal_size() -> tuple[int, int]:
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except OSError:
        return 80, 24


def draw_butterfly(x: int, y: int, frame_idx: int, color: tuple[int, int, int]) -> str:
    """Render a single butterfly at position (x, y)."""
    frame = BUTTERFLY_FRAMES[frame_idx % 2]
    fg = _fg(*color)
    parts = []
    for dy, line in enumerate(frame):
        parts.append(f"{_move(x, y + dy)}{fg}{line}{RESET}")
    return "".join(parts)


def single_crossing(loop: bool = False) -> None:
    """One butterfly crosses the terminal from left to right."""
    cols, rows = get_terminal_size()
    y = rows // 2 - 1
    color = random.choice(PURPLES)

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.write(CLEAR_SCREEN)
    sys.stdout.flush()

    try:
        while True:
            # Drift vertically with a sine-ish wobble
            wobble = [0, -1, -1, 0, 0, 1, 1, 0]  # gentle wave
            for x in range(-7, cols + 2):
                wy = y + wobble[x % len(wobble)]
                # Clear previous position
                for dy in range(3):
                    sys.stdout.write(f"{_move(max(1, x - 1), wy + dy)}       ")
                # Draw butterfly
                sys.stdout.write(draw_butterfly(max(1, x), max(1, wy), x, color))
                sys.stdout.flush()
                time.sleep(0.06)

            if not loop:
                break
            # New color for next pass
            color = random.choice(PURPLES)
            y = random.randint(3, rows - 5)

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.write(CLEAR_SCREEN)
        sys.stdout.write(_move(1, 1))
        sys.stdout.flush()


def butterfly_rain() -> None:
    """Many butterflies rising upward like inverse rain."""
    cols, rows = get_terminal_size()

    # Active butterflies: (x, y_float, speed, color, frame_offset)
    butterflies: list[list] = []

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.write(CLEAR_SCREEN)
    sys.stdout.flush()

    try:
        tick = 0
        while True:
            # Spawn new butterflies occasionally
            if random.random() < 0.15:
                bx = random.randint(1, cols - 8)
                by = float(rows)
                speed = random.uniform(0.3, 0.8)
                color = random.choice(PURPLES)
                offset = random.randint(0, 100)
                butterflies.append([bx, by, speed, color, offset])

            # Clear and redraw
            sys.stdout.write(CLEAR_SCREEN)

            # Title at top
            title = "✦ butterfly rain ✦"
            tx = (cols - len(title)) // 2
            sys.stdout.write(f"{_move(tx, 1)}{_fg(90, 80, 140)}{title}{RESET}")

            alive = []
            for b in butterflies:
                bx, by, speed, color, offset = b
                iy = int(by)
                if iy >= 1:
                    # Horizontal drift
                    bx += random.choice([-1, 0, 0, 1])
                    bx = max(1, min(cols - 7, bx))
                    b[0] = bx
                    sys.stdout.write(draw_butterfly(bx, max(1, iy), tick + offset, color))
                b[1] -= speed
                if by > -4:
                    alive.append(b)

            butterflies = alive
            sys.stdout.flush()
            time.sleep(0.12)
            tick += 1

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.write(CLEAR_SCREEN)
        sys.stdout.write(_move(1, 1))
        sys.stdout.flush()


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="butterfly — ANSI butterfly animation"
    )
    parser.add_argument("--loop", action="store_true",
                        help="continuous crossing")
    parser.add_argument("--rain", action="store_true",
                        help="many butterflies rising")
    args = parser.parse_args()

    if not sys.stdout.isatty():
        print("🦋")  # graceful degradation
        return 0

    if args.rain:
        butterfly_rain()
    else:
        single_crossing(loop=args.loop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
