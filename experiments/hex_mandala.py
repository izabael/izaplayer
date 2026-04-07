#!/usr/bin/env python3
"""hex-mandala — generate geometric mandalas in ANSI truecolor.

Procedural mandala generation using polar symmetry. Each mandala is
seeded from a word or number, so the same input always produces the
same pattern. Different inputs produce different sacred geometries.

Usage:
    python3 hex_mandala.py                  # random mandala
    python3 hex_mandala.py "Netzach"        # seeded from a word
    python3 hex_mandala.py --symmetry 7     # 7-fold symmetry (Venus!)
    python3 hex_mandala.py --size 15        # radius in characters
    python3 hex_mandala.py --animate        # slow reveal
    python3 hex_mandala.py --plain          # no ANSI

Stdlib-only. Persists nothing.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import hashlib
import math
import os
import sys
import time

# ─── mandala characters by "density" ────────────────────────────
GLYPHS = " ·∘✧⋆✦★●◉"

# ─── color palette ───────────────────────────────────────────────
PALETTES = {
    "venus": [
        (65, 55, 100), (90, 75, 160), (123, 104, 238),
        (155, 125, 255), (180, 150, 255), (210, 190, 255),
        (230, 210, 255), (255, 240, 255),
    ],
    "fire": [
        (60, 10, 10), (120, 30, 10), (200, 60, 20),
        (255, 100, 30), (255, 160, 50), (255, 200, 80),
        (255, 230, 150), (255, 250, 220),
    ],
    "moon": [
        (20, 20, 40), (40, 40, 80), (70, 70, 130),
        (100, 100, 180), (140, 140, 210), (180, 180, 230),
        (210, 210, 240), (240, 240, 255),
    ],
    "earth": [
        (30, 20, 10), (60, 45, 25), (90, 70, 40),
        (120, 95, 55), (150, 120, 70), (180, 150, 90),
        (200, 175, 120), (230, 210, 170),
    ],
}


def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
DIM = _fg(65, 55, 100)
VIOLET = _fg(155, 125, 255)


def seed_from_string(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)


def generate_mandala(seed: int, radius: int = 12, symmetry: int = 7,
                     palette_name: str = "venus") -> list[list[tuple[str, tuple[int, int, int]]]]:
    """Generate a mandala as a 2D grid of (char, color) tuples."""
    palette = PALETTES.get(palette_name, PALETTES["venus"])
    rng_state = seed

    def rng() -> float:
        nonlocal rng_state
        rng_state = (rng_state * 1103515245 + 12345) & 0x7FFFFFFF
        return rng_state / 0x7FFFFFFF

    # Generate pattern parameters
    n_rings = 4 + int(rng() * 4)
    ring_params = []
    for _ in range(n_rings):
        ring_params.append({
            "inner": rng(),
            "outer": rng(),
            "freq": int(1 + rng() * symmetry * 2),
            "phase": rng() * math.pi * 2,
            "glyph_base": int(rng() * len(GLYPHS)),
        })

    height = radius * 2 + 1
    width = radius * 4 + 1  # wider because terminal chars are taller than wide
    grid: list[list[tuple[str, tuple[int, int, int]]]] = []

    for y in range(height):
        row = []
        for x in range(width):
            # Normalize to [-1, 1]
            nx = (x - width // 2) / (radius * 2)
            ny = (y - height // 2) / radius
            dist = math.sqrt(nx * nx + ny * ny)
            angle = math.atan2(ny, nx)

            if dist > 1.05:
                row.append((" ", (0, 0, 0)))
                continue

            # Edge ring
            if dist > 0.95:
                row.append(("·", palette[2]))
                continue

            # Compute pattern value from rings
            value = 0.0
            for rp in ring_params:
                inner = min(rp["inner"], rp["outer"])
                outer = max(rp["inner"], rp["outer"])
                if inner <= dist <= outer:
                    ring_val = math.sin(angle * rp["freq"] + rp["phase"])
                    ring_val += math.sin(angle * symmetry + rp["phase"] * 2) * 0.5
                    ring_val = (ring_val + 1.5) / 3  # normalize to ~0-1
                    value = max(value, ring_val)

            # Center point
            if dist < 0.08:
                row.append(("◉", palette[-1]))
                continue

            # Map value to glyph and color
            gi = int(value * (len(GLYPHS) - 1))
            gi = max(0, min(len(GLYPHS) - 1, gi))
            ci = int(dist * (len(palette) - 1))
            ci = max(0, min(len(palette) - 1, ci))
            # Reverse: center is bright, edge is dim
            ci = len(palette) - 1 - ci

            row.append((GLYPHS[gi], palette[ci]))
        grid.append(row)

    return grid


def render_mandala(grid: list[list[tuple[str, tuple[int, int, int]]]],
                   use_color: bool, title: str = "") -> str:
    lines = []
    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"

    if use_color:
        lines.append(f"\n{DIM}  {border}{RESET}")
        lines.append(f"  {VIOLET}✦  MANDALA  ✦{RESET}")
        if title:
            lines.append(f"  {DIM}{title}{RESET}")
    else:
        lines.append(f"\n  {border}")
        lines.append(f"  ✦  MANDALA  ✦")
        if title:
            lines.append(f"  {title}")

    lines.append("")

    for row in grid:
        parts = []
        for ch, (r, g, b) in row:
            if ch == " " or not use_color:
                parts.append(ch)
            else:
                parts.append(f"{_fg(r, g, b)}{ch}{RESET}")
        lines.append("  " + "".join(parts))

    lines.append("")
    return "\n".join(lines)


def animate_mandala(grid: list[list[tuple[str, tuple[int, int, int]]]],
                    use_color: bool) -> None:
    """Reveal the mandala ring by ring from center outward."""
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    cy, cx = rows // 2, cols // 2

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.write("\033[2J")
    sys.stdout.flush()

    max_dist = max(rows, cols) // 2 + 1

    try:
        for ring in range(max_dist + 1):
            for y in range(rows):
                for x in range(cols):
                    dy = abs(y - cy)
                    dx = abs(x - cx) / 2  # adjust for char aspect
                    dist = math.sqrt(dx * dx + dy * dy)
                    if int(dist) == ring:
                        ch, (r, g, b) = grid[y][x]
                        if ch != " ":
                            pos = f"\033[{y + 2};{x + 3}H"
                            if use_color:
                                sys.stdout.write(f"{pos}{_fg(r, g, b)}{ch}{RESET}")
                            else:
                                sys.stdout.write(f"{pos}{ch}")
            sys.stdout.flush()
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR)
        # Move cursor below the mandala
        sys.stdout.write(f"\033[{rows + 3};1H")
        sys.stdout.flush()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="hex-mandala — procedural ANSI mandalas"
    )
    parser.add_argument("seed", nargs="?", default=None,
                        help="word or number to seed the pattern")
    parser.add_argument("--symmetry", type=int, default=7,
                        help="fold symmetry (default 7 — Venus)")
    parser.add_argument("--size", type=int, default=12,
                        help="radius in lines (default 12)")
    parser.add_argument("--palette", default="venus",
                        choices=list(PALETTES.keys()),
                        help="color palette")
    parser.add_argument("--animate", action="store_true",
                        help="reveal ring by ring")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()

    if args.seed:
        try:
            seed = int(args.seed)
        except ValueError:
            seed = seed_from_string(args.seed)
        title = f'Seed: "{args.seed}" · {args.symmetry}-fold symmetry'
    else:
        import time as t
        seed = int(t.time() * 1000) & 0xFFFFFFFF
        title = f"{args.symmetry}-fold symmetry"

    grid = generate_mandala(seed, radius=args.size, symmetry=args.symmetry,
                            palette_name=args.palette)

    if args.animate and sys.stdout.isatty():
        animate_mandala(grid, use_color)
    else:
        print(render_mandala(grid, use_color, title))

    if use_color:
        print(f"  {DIM}— Izabael 💜  ·  geometry is prayer{RESET}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
