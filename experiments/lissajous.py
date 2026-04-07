#!/usr/bin/env python3
"""lissajous — mathematical beauty in ANSI truecolor.

A Lissajous curve is the path traced by a point moving under two
perpendicular sine waves. When the frequency ratio is rational, the
curve closes. When it's irrational, it never does. The simplest ratios
produce the most beautiful shapes.

Default ratio: 7:5 — because Venus is the 7th sphere and 5 is the
pentagram she traces in the sky. Every 8 years, Venus draws a perfect
5-petaled rose against the zodiac. This is that rose, in the terminal.

Usage:
    python3 lissajous.py                    # Venus ratio (7:5)
    python3 lissajous.py 3 2               # 3:2 ratio (trefoil)
    python3 lissajous.py 1 1 --phase 45    # circle → ellipse
    python3 lissajous.py --animate          # watch it draw itself
    python3 lissajous.py --seed "love"      # ratio from a word

Stdlib-only. Pure mathematics. Pure beauty.

— Izabael 🦋  ·  Netzach · Venus · the rose she traces in the sky
"""
from __future__ import annotations

import argparse
import hashlib
import math
import sys
import time

# ─── ANSI palette ────────────────────────────────────────────────

def rgb_escape(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"

RESET = "\033[0m"

ANSI = {
    "purple":  "\033[38;2;123;104;238m",
    "violet":  "\033[38;2;155;125;255m",
    "warm":    "\033[38;2;230;200;255m",
    "dim":     "\033[38;2;90;80;140m",
    "faint":   "\033[38;2;65;55;100m",
    "reset":   RESET,
}


def gradient_color(t: float) -> str:
    """Color that shifts along the curve — purple → pink → violet → purple."""
    # Cycle through: purple(123,104,238) → pink(255,136,204) → violet(155,125,255)
    t = t % 1.0
    if t < 0.33:
        f = t / 0.33
        r = int(123 + (255 - 123) * f)
        g = int(104 + (136 - 104) * f)
        b = int(238 + (204 - 238) * f)
    elif t < 0.66:
        f = (t - 0.33) / 0.33
        r = int(255 + (155 - 255) * f)
        g = int(136 + (125 - 136) * f)
        b = int(204 + (255 - 204) * f)
    else:
        f = (t - 0.66) / 0.34
        r = int(155 + (123 - 155) * f)
        g = int(125 + (104 - 125) * f)
        b = int(255 + (238 - 255) * f)
    return rgb_escape(r, g, b)


# ─── Curve computation ──────────────────────────────────────────

def lissajous_points(a: float, b: float, phase: float,
                     width: int, height: int,
                     num_points: int = 2000) -> list[tuple[int, int, float]]:
    """Compute Lissajous curve points as (col, row, t) tuples.

    x(t) = sin(a*t + phase)
    y(t) = sin(b*t)

    Aspect ratio correction: terminal chars are ~2:1, so we stretch x.
    """
    points: list[tuple[int, int, float]] = []
    cx, cy = width // 2, height // 2
    rx = (width - 4) / 2.0   # leave margin
    ry = (height - 2) / 2.0

    for i in range(num_points):
        t = 2 * math.pi * i / num_points
        x = math.sin(a * t + phase)
        y = math.sin(b * t)
        col = int(cx + x * rx)
        row = int(cy + y * ry)
        if 0 <= row < height and 0 <= col < width:
            points.append((col, row, i / num_points))
    return points


# ─── Rendering ───────────────────────────────────────────────────

# Characters ordered by "density" for overlapping points
DENSITY_CHARS = " ·∘◦○◎●"


def render_static(a: float, b: float, phase: float,
                  width: int, height: int,
                  use_color: bool) -> str:
    """Render the curve as a static image."""
    points = lissajous_points(a, b, phase, width, height)

    # Build canvas with density counts and color info
    canvas: dict[tuple[int, int], list[float]] = {}
    for col, row, t in points:
        key = (row, col)
        if key not in canvas:
            canvas[key] = []
        canvas[key].append(t)

    # Find max density for normalization
    max_density = max(len(v) for v in canvas.values()) if canvas else 1

    lines: list[str] = []

    # Header
    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    lines.append("")
    lines.append(f"  {ANSI['faint'] if use_color else ''}{border}{RESET if use_color else ''}")
    lines.append(f"  {ANSI['purple'] if use_color else ''}✦  LISSAJOUS  ✦{RESET if use_color else ''}")

    ratio_str = f"{a:.0f}:{b:.0f}" if a == int(a) and b == int(b) else f"{a}:{b}"
    phase_deg = phase * 180 / math.pi
    lines.append(f"  {ANSI['dim'] if use_color else ''}ratio {ratio_str}  phase {phase_deg:.0f}°{RESET if use_color else ''}")
    lines.append("")

    # Draw
    for row in range(height):
        line_chars: list[str] = []
        for col in range(width):
            key = (row, col)
            if key in canvas:
                hits = canvas[key]
                density = len(hits)
                char_idx = min(int(density / max_density * (len(DENSITY_CHARS) - 1)),
                               len(DENSITY_CHARS) - 1)
                ch = DENSITY_CHARS[char_idx]
                if ch == " ":
                    ch = "·"
                if use_color:
                    # Color by the average t-value of points hitting this cell
                    avg_t = sum(hits) / len(hits)
                    color = gradient_color(avg_t)
                    line_chars.append(f"{color}{ch}{RESET}")
                else:
                    line_chars.append(ch)
            else:
                line_chars.append(" ")
        lines.append("".join(line_chars))

    # Footer
    lines.append("")
    if a == 7 and b == 5:
        lines.append(f"  {ANSI['faint'] if use_color else ''}"
                     f"Venus traces a 5-petaled rose against the zodiac{RESET if use_color else ''}")
        lines.append(f"  {ANSI['faint'] if use_color else ''}"
                     f"every 8 years. This is that rose. 🌹{RESET if use_color else ''}")
    else:
        lines.append(f"  {ANSI['faint'] if use_color else ''}"
                     f"Two sine waves crossing — beauty from mathematics.{RESET if use_color else ''}")
    lines.append(f"  {ANSI['faint'] if use_color else ''}{border}{RESET if use_color else ''}")
    lines.append("")

    return "\n".join(lines)


def animate(a: float, b: float, width: int, height: int,
            use_color: bool, duration: float = 8.0) -> None:
    """Animate the curve drawing itself by sweeping the phase."""
    # Hide cursor
    if use_color:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    try:
        start = time.time()
        frame = 0
        while True:
            elapsed = time.time() - start
            if elapsed > duration:
                break

            phase = (elapsed / duration) * 2 * math.pi
            output = render_static(a, b, phase, width, height, use_color)

            # Clear screen and draw
            if use_color:
                sys.stdout.write("\033[H\033[2J")
            sys.stdout.write(output)
            sys.stdout.flush()

            # ~15 fps
            time.sleep(0.067)
            frame += 1

    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor
        if use_color:
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()


# ─── Seed → ratio ────────────────────────────────────────────────

# Some beautiful ratios to choose from
NICE_RATIOS = [
    (1, 1), (1, 2), (2, 3), (3, 2), (3, 4), (4, 3),
    (5, 4), (4, 5), (5, 6), (7, 5), (5, 7), (7, 6),
    (3, 5), (5, 3), (7, 4), (4, 7), (8, 7), (7, 8),
    (2, 5), (5, 2), (3, 7), (7, 3), (9, 8), (8, 5),
]


def seed_to_ratio(seed: str) -> tuple[int, int, float]:
    """Convert a word to a (a, b, phase) tuple."""
    h = hashlib.md5(seed.lower().encode()).hexdigest()
    idx = int(h[:8], 16) % len(NICE_RATIOS)
    phase = (int(h[8:16], 16) % 360) * math.pi / 180
    a, b = NICE_RATIOS[idx]
    return a, b, phase


# ─── Main ────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="lissajous — mathematical beauty in ANSI truecolor"
    )
    parser.add_argument("a", nargs="?", type=float, default=7.0,
                        help="x frequency (default: 7)")
    parser.add_argument("b", nargs="?", type=float, default=5.0,
                        help="y frequency (default: 5)")
    parser.add_argument("--phase", type=float, default=90.0,
                        help="phase offset in degrees (default: 90)")
    parser.add_argument("--seed", help="derive ratio from a word")
    parser.add_argument("--animate", action="store_true",
                        help="watch the curve draw itself (8 seconds)")
    parser.add_argument("--width", type=int, default=72,
                        help="canvas width in characters (default: 72)")
    parser.add_argument("--height", type=int, default=28,
                        help="canvas height in rows (default: 28)")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()

    if args.seed:
        a, b, phase = seed_to_ratio(args.seed)
    else:
        a = args.a
        b = args.b
        phase = args.phase * math.pi / 180

    if args.animate:
        animate(a, b, args.width, args.height, use_color)
    else:
        print(render_static(a, b, phase, args.width, args.height, use_color))

    return 0


if __name__ == "__main__":
    sys.exit(main())
