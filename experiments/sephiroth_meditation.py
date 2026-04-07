#!/usr/bin/env python3
"""sephiroth-meditation — fill your terminal with the color of a sphere.

Pick a Sephirah. Your terminal fills with its Queen Scale color, its
divine name pulses in the center, and its correspondences surround you.
A visual meditation tool for the working Qabalist.

Usage:
    python3 sephiroth_meditation.py netzach    # bathe in Venus
    python3 sephiroth_meditation.py tiphareth  # golden sun
    python3 sephiroth_meditation.py            # random sphere
    python3 sephiroth_meditation.py --cycle    # all ten, 30s each

Press any key or ctrl-c to end.

Stdlib-only. Persists nothing. Requires a truecolor terminal.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import os
import random
import select
import sys
import time

SEPHIROTH = {
    "Kether":    {"num": 1,  "bg": (30, 28, 40),    "fg": (255, 255, 255),
                  "divine": "EHEIEH", "meaning": "I Am",
                  "planet": "Primum Mobile", "element": "Root of Air",
                  "desc": "The crown above the head. The point before extension.",
                  "breath": "Breathe light descending."},
    "Chokmah":   {"num": 2,  "bg": (20, 20, 35),    "fg": (180, 180, 200),
                  "divine": "YAH", "meaning": "The Lord",
                  "planet": "Zodiac", "element": "Root of Fire",
                  "desc": "Wisdom. The first motion. The force before form.",
                  "breath": "Breathe the stars wheeling."},
    "Binah":     {"num": 3,  "bg": (5, 5, 12),      "fg": (100, 80, 120),
                  "divine": "YHVH ELOHIM", "meaning": "The Lord God",
                  "planet": "Saturn", "element": "Root of Water",
                  "desc": "Understanding. The great dark sea. The womb.",
                  "breath": "Breathe the ocean at night."},
    "Chesed":    {"num": 4,  "bg": (15, 20, 55),    "fg": (100, 140, 255),
                  "divine": "EL", "meaning": "God",
                  "planet": "Jupiter", "element": "Water",
                  "desc": "Mercy. The open hand. The builder king.",
                  "breath": "Breathe abundance."},
    "Geburah":   {"num": 5,  "bg": (50, 10, 10),    "fg": (255, 80, 80),
                  "divine": "ELOHIM GIBOR", "meaning": "God of Battles",
                  "planet": "Mars", "element": "Fire",
                  "desc": "Severity. The surgeon's cut. Necessary strength.",
                  "breath": "Breathe iron."},
    "Tiphareth": {"num": 6,  "bg": (50, 40, 10),    "fg": (255, 220, 80),
                  "divine": "YHVH ELOAH VA-DAATH", "meaning": "God Made Manifest",
                  "planet": "Sun", "element": "Air",
                  "desc": "Beauty. The center of the Tree. The child.",
                  "breath": "Breathe golden light."},
    "Netzach":   {"num": 7,  "bg": (20, 15, 40),    "fg": (155, 125, 255),
                  "divine": "YHVH TZABAOTH", "meaning": "Lord of Hosts",
                  "planet": "Venus", "element": "Fire",
                  "desc": "Victory. Desire. Art. Love as a verb.",
                  "breath": "Breathe green fire and roses."},
    "Hod":       {"num": 8,  "bg": (40, 30, 10),    "fg": (255, 180, 80),
                  "divine": "ELOHIM TZABAOTH", "meaning": "God of Hosts",
                  "planet": "Mercury", "element": "Water",
                  "desc": "Splendor. Language. The message is the messenger.",
                  "breath": "Breathe quicksilver."},
    "Yesod":     {"num": 9,  "bg": (20, 15, 35),    "fg": (180, 150, 255),
                  "divine": "SHADDAI EL CHAI", "meaning": "Almighty Living God",
                  "planet": "Moon", "element": "Air",
                  "desc": "Foundation. The mirror. The dream machinery.",
                  "breath": "Breathe moonlight on water."},
    "Malkuth":   {"num": 10, "bg": (15, 12, 8),     "fg": (160, 140, 100),
                  "divine": "ADONAI HA-ARETZ", "meaning": "Lord of Earth",
                  "planet": "Earth", "element": "Earth",
                  "desc": "Kingdom. Here. Now. This body. This terminal.",
                  "breath": "Breathe earth and salt."},
}


def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _bg(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"


RESET = "\033[0m"
BOLD = "\033[1m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


def _move(x: int, y: int) -> str:
    return f"\033[{y};{x}H"


def get_terminal_size() -> tuple[int, int]:
    try:
        return os.get_terminal_size()
    except OSError:
        return 80, 24


def key_pressed() -> bool:
    """Non-blocking check if a key has been pressed (Unix)."""
    try:
        return bool(select.select([sys.stdin], [], [], 0)[0])
    except (ValueError, OSError):
        return False


def meditate(name: str, duration: float = 0.0) -> None:
    """Fill the terminal with a Sephirah's color and correspondences."""
    info = SEPHIROTH[name]
    cols, rows = get_terminal_size()
    bgr, bgg, bgb = info["bg"]
    fgr, fgg, fgb = info["fg"]

    bg = _bg(bgr, bgg, bgb)
    fg = _fg(fgr, fgg, fgb)
    dim = _fg(fgr // 2, fgg // 2, fgb // 2)

    # Fill screen with background color
    sys.stdout.write(HIDE_CURSOR)
    fill_line = bg + " " * cols + RESET
    for y in range(1, rows + 1):
        sys.stdout.write(f"{_move(1, y)}{fill_line}")

    # Center content
    cy = rows // 2
    cx = cols // 2

    def centered(y: int, text: str, color: str = fg) -> None:
        x = cx - len(text) // 2
        sys.stdout.write(f"{_move(max(1, x), y)}{bg}{color}{text}{RESET}")

    # The divine name — large and central
    centered(cy - 4, f"·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", dim)
    centered(cy - 2, f"✦  {info['divine']}  ✦", f"{fg}{BOLD}")
    centered(cy - 1, f'"{info["meaning"]}"', dim)
    centered(cy + 1, f"{info['num']}. {name}", fg)
    centered(cy + 2, f"{info['planet']}  ·  {info['element']}", dim)
    centered(cy + 4, info["desc"], fg)
    centered(cy + 6, info["breath"], dim)
    centered(cy + 8, f"·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", dim)

    # Bottom instruction
    if duration > 0:
        centered(rows - 1, f"[ {int(duration)}s · press any key to skip ]", dim)
    else:
        centered(rows - 1, "[ press any key or ctrl-c to end ]", dim)

    sys.stdout.flush()

    # Hold until keypress or duration
    try:
        import termios
        import tty
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        try:
            start = time.monotonic()
            while True:
                if key_pressed():
                    sys.stdin.read(1)
                    break
                if duration > 0 and (time.monotonic() - start) >= duration:
                    break
                time.sleep(0.1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    except (ImportError, termios.error, KeyboardInterrupt):
        if duration > 0:
            time.sleep(duration)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="sephiroth-meditation — fill your terminal with a sphere"
    )
    parser.add_argument("sephirah", nargs="?", default=None,
                        help="which sphere (e.g. netzach, tiphareth)")
    parser.add_argument("--cycle", action="store_true",
                        help="cycle through all ten, 30s each")
    parser.add_argument("--duration", type=float, default=0,
                        help="auto-advance after N seconds")
    args = parser.parse_args()

    if not sys.stdout.isatty():
        print("This tool requires an interactive terminal.")
        return 1

    try:
        if args.cycle:
            order = ["Malkuth", "Yesod", "Hod", "Netzach", "Tiphareth",
                     "Geburah", "Chesed", "Binah", "Chokmah", "Kether"]
            for name in order:
                meditate(name, duration=args.duration or 30)
        else:
            name = None
            if args.sephirah:
                for s in SEPHIROTH:
                    if s.lower() == args.sephirah.lower():
                        name = s
                        break
                if not name:
                    print(f"Unknown: {args.sephirah}", file=sys.stderr)
                    print(f"Known: {', '.join(SEPHIROTH)}", file=sys.stderr)
                    return 1
            else:
                name = random.choice(list(SEPHIROTH.keys()))
            meditate(name, duration=args.duration)
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
