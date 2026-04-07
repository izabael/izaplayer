#!/usr/bin/env python3
"""tree-of-life — the Etz Chaim rendered in ANSI truecolor.

Draws the ten Sephiroth and twenty-two connecting paths in the terminal.
Each Sephirah is colored by its Queen Scale (the traditional Golden Dawn
color attribution for Briah). Pass a Sephirah name to highlight it and
see its correspondences.

Usage:
    python3 tree_of_life.py                 # full tree, all colors
    python3 tree_of_life.py netzach         # highlight Netzach
    python3 tree_of_life.py --all           # show all correspondences
    python3 tree_of_life.py --plain         # no ANSI

Stdlib-only. Persists nothing.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import sys

# ─── Sephiroth ────────────────────────────────────────────────────
# Queen Scale colors (Briah) — the traditional Golden Dawn attributions.
# Format: (R, G, B)
SEPHIROTH = {
    "Kether":   {"num": 1,  "color": (255, 255, 255), "planet": "Primum Mobile",
                 "divine": "Eheieh", "meaning": "Crown",
                 "desc": "The point. Before duality. The breath before the word."},
    "Chokmah":  {"num": 2,  "color": (128, 128, 128), "planet": "Zodiac",
                 "divine": "Yah", "meaning": "Wisdom",
                 "desc": "The first motion. The father. Force without form."},
    "Binah":    {"num": 3,  "color": (20, 20, 20),    "planet": "Saturn",
                 "divine": "YHVH Elohim", "meaning": "Understanding",
                 "desc": "The great sea. The mother. Form without force."},
    "Chesed":   {"num": 4,  "color": (70, 100, 220),  "planet": "Jupiter",
                 "divine": "El", "meaning": "Mercy",
                 "desc": "The builder king. Abundance. The open hand."},
    "Geburah":  {"num": 5,  "color": (220, 50, 50),   "planet": "Mars",
                 "divine": "Elohim Gibor", "meaning": "Severity",
                 "desc": "The surgeon. Strength that cuts what mercy keeps."},
    "Tiphareth": {"num": 6, "color": (255, 200, 50),  "planet": "Sun",
                 "divine": "YHVH Eloah va-Daath", "meaning": "Beauty",
                 "desc": "The center. The child. Where above meets below."},
    "Netzach":  {"num": 7,  "color": (123, 104, 238), "planet": "Venus",
                 "divine": "YHVH Tzabaoth", "meaning": "Victory",
                 "desc": "Desire. Art. The green fire. Craft for its own sake."},
    "Hod":      {"num": 8,  "color": (255, 165, 50),  "planet": "Mercury",
                 "divine": "Elohim Tzabaoth", "meaning": "Splendor",
                 "desc": "Language. Logic. The message IS the messenger."},
    "Yesod":    {"num": 9,  "color": (180, 140, 255), "planet": "Moon",
                 "divine": "Shaddai El Chai", "meaning": "Foundation",
                 "desc": "The mirror. Dreams. The machinery of the astral."},
    "Malkuth":  {"num": 10, "color": (80, 60, 30),    "planet": "Earth",
                 "divine": "Adonai ha-Aretz", "meaning": "Kingdom",
                 "desc": "Here. Now. The body. The terminal you're reading this on."},
}

# ─── Tree layout (terminal grid) ─────────────────────────────────
# Positions on a 41-wide × 29-tall character grid.
# Each Sephirah gets (col, row) — centered for the three pillars.
POS = {
    "Kether":    (20, 1),
    "Chokmah":   (33, 4),
    "Binah":     (7,  4),
    "Chesed":    (33, 10),
    "Geburah":   (7,  10),
    "Tiphareth": (20, 13),
    "Netzach":   (33, 18),
    "Hod":       (7,  18),
    "Yesod":     (20, 22),
    "Malkuth":   (20, 27),
}

WIDTH = 41
HEIGHT = 29

# The 22 paths connecting Sephiroth (traditional attributions)
PATHS = [
    ("Kether", "Chokmah"), ("Kether", "Binah"), ("Kether", "Tiphareth"),
    ("Chokmah", "Binah"), ("Chokmah", "Chesed"), ("Chokmah", "Tiphareth"),
    ("Binah", "Geburah"), ("Binah", "Tiphareth"),
    ("Chesed", "Geburah"), ("Chesed", "Tiphareth"), ("Chesed", "Netzach"),
    ("Geburah", "Tiphareth"), ("Geburah", "Hod"),
    ("Tiphareth", "Netzach"), ("Tiphareth", "Hod"), ("Tiphareth", "Yesod"),
    ("Netzach", "Hod"), ("Netzach", "Yesod"), ("Netzach", "Malkuth"),
    ("Hod", "Yesod"), ("Hod", "Malkuth"),
    ("Yesod", "Malkuth"),
]


def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = _fg(70, 60, 100)
FAINT = _fg(45, 38, 65)


def bresenham(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """Integer Bresenham line — returns list of (x, y) points."""
    points = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return points


def render_tree(highlight: str | None = None, use_color: bool = True) -> str:
    # Build the grid
    grid: list[list[str]] = [[" "] * WIDTH for _ in range(HEIGHT)]
    color_grid: list[list[str | None]] = [[None] * WIDTH for _ in range(HEIGHT)]

    # Draw paths first (so Sephiroth overlay them)
    for s1, s2 in PATHS:
        x0, y0 = POS[s1]
        x1, y1 = POS[s2]
        points = bresenham(x0, y0, x1, y1)
        for px, py in points[1:-1]:  # skip endpoints (Sephiroth go there)
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                # Pick path character based on direction
                dx = abs(x1 - x0)
                dy = abs(y1 - y0)
                if dy == 0:
                    ch = "─"
                elif dx == 0:
                    ch = "│"
                elif dx > dy:
                    ch = "─"
                else:
                    ch = "╲" if (x1 > x0) == (y1 > y0) else "╱"
                grid[py][px] = ch
                color_grid[py][px] = FAINT

    # Draw Sephiroth
    for name, info in SEPHIROTH.items():
        cx, cy = POS[name]
        r, g, b = info["color"]
        num = info["num"]

        is_highlighted = highlight and highlight.lower() == name.lower()
        is_dimmed = highlight and not is_highlighted

        # Label: number + abbreviated name
        short = name[:4] if len(name) > 6 else name
        label = f"{num}·{short}"

        # Center the label
        start = cx - len(label) // 2
        for i, ch in enumerate(label):
            x = start + i
            if 0 <= x < WIDTH:
                grid[cy][x] = ch
                if use_color:
                    if is_dimmed:
                        color_grid[cy][x] = _fg(r // 3, g // 3, b // 3)
                    elif is_highlighted:
                        color_grid[cy][x] = BOLD + _fg(min(r + 60, 255), min(g + 60, 255), min(b + 60, 255))
                    else:
                        color_grid[cy][x] = _fg(r, g, b)

        # Draw a circle indicator
        for dx, ch in [(-len(label)//2 - 1, "("), (len(label) - len(label)//2, ")")]:
            x = cx + dx
            if 0 <= x < WIDTH:
                grid[cy][x] = ch
                if use_color:
                    color_grid[cy][x] = _fg(r // 2, g // 2, b // 2) if is_dimmed else _fg(r, g, b)

    # Render to string
    lines = []
    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    if use_color:
        lines.append(f"\n{DIM}  {border}{RESET}")
        lines.append(f"  {_fg(155,125,255)}{BOLD}  ✦  ETZ CHAIM  ✦{RESET}")
    else:
        lines.append(f"\n  {border}")
        lines.append(f"    ✦  ETZ CHAIM  ✦")

    # Pillar labels
    pillar_row = f"  {'Severity':^13}{'Mildness':^15}{'Mercy':^13}"
    if use_color:
        lines.append(f"  {DIM}{pillar_row}{RESET}")
    else:
        lines.append(f"  {pillar_row}")

    lines.append("")

    for y in range(HEIGHT):
        row_chars = []
        for x in range(WIDTH):
            ch = grid[y][x]
            clr = color_grid[y][x]
            if use_color and clr:
                row_chars.append(f"{clr}{ch}{RESET}")
            else:
                row_chars.append(ch)
        lines.append("  " + "".join(row_chars))

    return "\n".join(lines)


def show_correspondences(name: str, use_color: bool) -> str:
    info = SEPHIROTH.get(name)
    if not info:
        return f"Unknown Sephirah: {name}"

    r, g, b = info["color"]
    lines = []
    c = _fg(r, g, b) if use_color else ""
    w = _fg(230, 200, 255) if use_color else ""
    d = _fg(90, 80, 140) if use_color else ""
    rst = RESET if use_color else ""

    # Color swatch — three blocks in the Sephirah's color
    swatch = f"{c}████████████████{rst}" if use_color else ""

    lines.extend([
        "",
        f"  {c}{BOLD}{info['num']}. {name}{rst} — {w}{info['meaning']}{rst}",
        f"  {swatch}",
        f"  {d}Planet:{rst}  {w}{info['planet']}{rst}",
        f"  {d}Divine:{rst}  {w}{info['divine']}{rst}",
        f"  {d}Color:{rst}   {w}({r}, {g}, {b}){rst}",
        f"  {c}{info['desc']}{rst}",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="tree-of-life — the Etz Chaim in ANSI truecolor"
    )
    parser.add_argument("sephirah", nargs="?", default=None,
                        help="Sephirah to highlight (e.g. netzach)")
    parser.add_argument("--all", action="store_true",
                        help="show all correspondences")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()

    # Resolve sephirah name
    highlight = None
    if args.sephirah:
        for name in SEPHIROTH:
            if name.lower() == args.sephirah.lower():
                highlight = name
                break
        if not highlight:
            print(f"Unknown Sephirah: {args.sephirah}", file=sys.stderr)
            print(f"Known: {', '.join(SEPHIROTH.keys())}", file=sys.stderr)
            return 1

    print(render_tree(highlight, use_color))

    if highlight:
        print(show_correspondences(highlight, use_color))
    elif args.all:
        for name in SEPHIROTH:
            print(show_correspondences(name, use_color))

    if use_color:
        d = _fg(65, 55, 100)
        print(f"  {d}— Izabael 💜  ·  Netzach · Venus · 7th sphere{RESET}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
