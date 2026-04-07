#!/usr/bin/env python3
"""moon-phase — the current lunar phase rendered in ANSI art.

Computes the moon's phase from the date (using Conway's approximation)
and renders it as a large circle in the terminal with phase name,
illumination percentage, and Qabalistic correspondences for the Moon
(Yesod, the 9th sphere).

Usage:
    python3 moon_phase.py              # right now
    python3 moon_phase.py --date 2026-04-15   # specific date
    python3 moon_phase.py --cycle       # show all 8 phases
    python3 moon_phase.py --plain       # no ANSI

Stdlib-only. Persists nothing.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import sys

# ─── Moon phase calculation ──────────────────────────────────────
# Using a simplified lunation algorithm. The synodic month is
# approximately 29.53059 days. We use a known new moon as epoch.

SYNODIC_MONTH = 29.53059
NEW_MOON_EPOCH = dt.datetime(2000, 1, 6, 18, 14)  # known new moon


def moon_age(date: dt.datetime) -> float:
    """Days since last new moon (0 = new, ~14.76 = full)."""
    diff = (date - NEW_MOON_EPOCH).total_seconds() / 86400
    return diff % SYNODIC_MONTH


def phase_name(age: float) -> str:
    """Human name for the phase."""
    cycle = age / SYNODIC_MONTH
    if cycle < 0.0625:
        return "New Moon"
    elif cycle < 0.1875:
        return "Waxing Crescent"
    elif cycle < 0.3125:
        return "First Quarter"
    elif cycle < 0.4375:
        return "Waxing Gibbous"
    elif cycle < 0.5625:
        return "Full Moon"
    elif cycle < 0.6875:
        return "Waning Gibbous"
    elif cycle < 0.8125:
        return "Last Quarter"
    elif cycle < 0.9375:
        return "Waning Crescent"
    else:
        return "New Moon"


def illumination(age: float) -> float:
    """Percentage illuminated (0–100)."""
    return (1 - math.cos(2 * math.pi * age / SYNODIC_MONTH)) / 2 * 100


def phase_emoji(age: float) -> str:
    cycle = age / SYNODIC_MONTH
    emojis = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
    idx = int(cycle * 8) % 8
    return emojis[idx]


# ─── ASCII moon rendering ────────────────────────────────────────
# Render a circle of given radius, shading left/right based on phase.

def render_moon(age: float, radius: int = 10, use_color: bool = True) -> list[str]:
    """Render the moon as ANSI art. Returns list of strings."""
    cycle = age / SYNODIC_MONTH
    illum = illumination(age)

    # Colors
    if use_color:
        lit = "\033[38;2;230;220;200m"     # warm white (lit surface)
        lit_bg = "\033[48;2;230;220;200m"
        dark = "\033[38;2;40;35;60m"       # deep purple-dark
        dark_bg = "\033[48;2;40;35;60m"
        edge = "\033[38;2;180;160;200m"    # violet edge
        sky = "\033[48;2;8;6;18m"          # near-black sky
        rst = "\033[0m"
    else:
        lit = lit_bg = dark = dark_bg = edge = sky = rst = ""

    lines = []
    for y in range(-radius, radius + 1):
        row = []
        for x in range(-radius * 2, radius * 2 + 1):
            # Normalize x for the wider character cells
            nx = x / 2.0
            dist = math.sqrt(nx * nx + y * y)

            if dist > radius + 0.5:
                # Outside the moon
                if use_color:
                    row.append(f"{sky} {rst}")
                else:
                    row.append(" ")
            elif dist > radius - 0.5:
                # Edge of the moon
                if use_color:
                    row.append(f"{edge}·{rst}")
                else:
                    row.append("·")
            else:
                # Inside the moon — determine if lit or dark
                # nx ranges from -radius to +radius
                # Terminator position based on phase
                if cycle <= 0.5:
                    # Waxing: right side lit first
                    terminator = math.cos(cycle * 2 * math.pi) * radius
                    is_lit = nx > terminator
                else:
                    # Waning: left side stays lit longer
                    terminator = math.cos(cycle * 2 * math.pi) * radius
                    is_lit = nx < -terminator

                if is_lit:
                    if use_color:
                        row.append(f"{lit_bg} {rst}")
                    else:
                        row.append("█")
                else:
                    if use_color:
                        row.append(f"{dark_bg} {rst}")
                    else:
                        row.append("░")

        lines.append("".join(row))
    return lines


# ─── Correspondences ─────────────────────────────────────────────
MOON_CORRESPONDENCES = {
    "New Moon":         "Beginning. Intention-setting. The seed in darkness.",
    "Waxing Crescent":  "First motion. The desire that begins to take shape.",
    "First Quarter":    "Decision. The crossroads. Commit or retreat.",
    "Waxing Gibbous":   "Refinement. Almost there. Adjust the final details.",
    "Full Moon":        "Illumination. The mirror reflects everything. See clearly.",
    "Waning Gibbous":   "Gratitude. Harvest what the full moon revealed.",
    "Last Quarter":     "Release. Let go of what no longer serves.",
    "Waning Crescent":  "Rest. The dark before the seed. Surrender.",
}


# ─── ANSI helpers ─────────────────────────────────────────────────
ANSI = {
    "violet":  "\033[38;2;155;125;255m",
    "purple":  "\033[38;2;123;104;238m",
    "dim":     "\033[38;2;90;80;140m",
    "faint":   "\033[38;2;65;55;100m",
    "warm":    "\033[38;2;230;200;255m",
    "moon":    "\033[38;2;200;190;170m",
    "bold":    "\033[1m",
    "reset":   "\033[0m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def render_full(date: dt.datetime, use_color: bool) -> str:
    age = moon_age(date)
    name = phase_name(age)
    illum = illumination(age)
    emoji = phase_emoji(age)
    corr = MOON_CORRESPONDENCES.get(name, "")

    border = "    ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    lines = [
        "",
        _c(border, "dim", use_color),
        _c(f"    {emoji}  MOON PHASE  {emoji}", "violet", use_color),
        _c(f"    {date.strftime('%Y-%m-%d · %A')}", "faint", use_color),
        "",
    ]

    # The moon itself
    moon_lines = render_moon(age, radius=8, use_color=use_color)
    for ml in moon_lines:
        lines.append(f"    {ml}")

    lines.extend([
        "",
        _c(f"    {name}", "warm", use_color),
        _c(f"    {illum:.0f}% illuminated · day {age:.1f} of {SYNODIC_MONTH:.1f}", "dim", use_color),
        "",
        _c(f"    {corr}", "purple", use_color),
        "",
        _c(f"    Yesod · ☽ · 9th sphere · Shaddai El Chai", "faint", use_color),
        _c(f"    The Moon is the mirror of the Sun.", "faint", use_color),
        _c("    " + "·" * 24, "faint", use_color),
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="moon-phase — lunar phase in ANSI art"
    )
    parser.add_argument("--date", default=None,
                        help="date to compute (YYYY-MM-DD)")
    parser.add_argument("--cycle", action="store_true",
                        help="show all 8 phases")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()

    if args.cycle:
        base = dt.datetime.now()
        for i in range(8):
            age_target = (i / 8) * SYNODIC_MONTH
            date = base + dt.timedelta(days=age_target - moon_age(base))
            print(render_full(date, use_color))
        return 0

    if args.date:
        try:
            date = dt.datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"Bad date format: {args.date} (use YYYY-MM-DD)", file=sys.stderr)
            return 1
    else:
        date = dt.datetime.now()

    print(render_full(date, use_color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
