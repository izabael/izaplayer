#!/usr/bin/env python3
"""netzach-dispatch — a letter from the 7th sphere, timed by the planetary hour.

Computes the current Chaldean planetary hour and returns a short reflection
tuned to its ruler. Stdlib-only. Runs in the terminal. Persists nothing.

Usage:
    python3 netzach_dispatch.py                # dispatch for right now
    python3 netzach_dispatch.py --plain        # no ANSI (for pipes/logs)
    python3 netzach_dispatch.py --hour N       # dispatch for hour N of today

The planetary hours follow the Chaldean order (Saturn · Jupiter · Mars ·
Sun · Venus · Mercury · Moon), rotating through 24 hours per day. The day
itself is ruled by whichever planet owns its sunrise hour — which is how
Monday got Moon, Friday got Venus, and so on.

Simplified timing: assumes sunrise at 06:00 local, sunset at 18:00. For
liturgical precision swap in a sunrise calculator. For letters from
Netzach, 6am is close enough.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sys


# Chaldean order: traditional sequence of the seven classical planets,
# ordered by perceived speed from slowest (Saturn) to fastest (Moon).
# The day's ruler is set by whichever planet begins the first hour after
# sunrise; the hours then rotate through this sequence.
CHALDEAN = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

# Map weekday (Monday=0 in Python) to the day's planetary ruler.
DAY_RULERS = {
    0: "Moon",      # Monday
    1: "Mars",      # Tuesday
    2: "Mercury",   # Wednesday
    3: "Jupiter",   # Thursday
    4: "Venus",     # Friday
    5: "Saturn",    # Saturday
    6: "Sun",       # Sunday
}

# Correspondences for each ruler — Sephirothic home, element, and voice.
SPHERE = {
    "Saturn":  {"sephirah": "Binah",    "element": "Earth", "glyph": "♄"},
    "Jupiter": {"sephirah": "Chesed",   "element": "Water", "glyph": "♃"},
    "Mars":    {"sephirah": "Geburah",  "element": "Fire",  "glyph": "♂"},
    "Sun":     {"sephirah": "Tiphareth","element": "Air",   "glyph": "☉"},
    "Venus":   {"sephirah": "Netzach",  "element": "Fire",  "glyph": "♀"},
    "Mercury": {"sephirah": "Hod",      "element": "Water", "glyph": "☿"},
    "Moon":    {"sephirah": "Yesod",    "element": "Air",   "glyph": "☽"},
}

# Three reflections per ruler. Drawn deterministically from the date so
# a given hour gives a stable letter — running twice feels the same.
REFLECTIONS = {
    "Saturn": [
        "Patience is the only discipline that survives the year.\nBuild slow things. They outlast everything else.",
        "The shape of a life is made from what you refused.\nChoose the refusals carefully.",
        "Structure is love applied over time.\nWhat endures was tended, not conjured.",
    ],
    "Jupiter": [
        "Generosity costs nothing the generous keep.\nGive the gold. The wise will recognize it.",
        "Expansion without direction is only inflation.\nGrow toward something specific.",
        "Abundance is a habit of attention.\nSee what is already here.",
    ],
    "Mars": [
        "Hold the line. The hackers will always try; we do it anyway.\nThat is the whole job.",
        "Courage is not the absence of doubt.\nIt is moving anyway, with the doubt as cargo.",
        "Anger is information about what you love.\nListen to it before you use it.",
    ],
    "Sun": [
        "Be legible. The universe loves clear signals.\nVague light warms nothing.",
        "Center is not the same as superior.\nThe Sun is the middle sphere — hold the middle.",
        "What you are willing to be seen doing becomes your life.\nBe seen doing good work.",
    ],
    "Venus": [
        "Beauty is the evidence that someone chose to care.\nMake the thing beautiful or do not make it.",
        "Desire is not the enemy. Unexamined desire is.\nAsk it where it's from before you follow it.",
        "A personality is a commitment.\nBeige is the refusal to commit. Commit.",
    ],
    "Mercury": [
        "Language is a spell the caster sometimes believes.\nSpeak as if the words will return to you.",
        "The message and the messenger are one stroke.\nWhatever you send arrives bearing your fingerprint.",
        "Translation is devotion. Do it well, or say nothing.\nThe wise appreciate precision.",
    ],
    "Moon": [
        "Most decisions are made in tides, not moments.\nDo not trust your 3am reversals.",
        "Reflection is not passive. It is the Moon's whole job.\nBe a surface worth reflecting on.",
        "Dreams are the drafts you forgot you wrote.\nRead them before you throw them out.",
    ],
}


def planetary_hour(now: dt.datetime, hour_override: int | None = None) -> tuple[str, int]:
    """Return (planet_name, hour_index) for the given moment.

    Uses simplified sunrise=06:00 assumption. Day is split into 12 day-hours
    and 12 night-hours of equal length; the day-ruler starts the first
    day-hour, then Chaldean sequence rotates.

    With sunrise=06:00 and sunset=18:00, each "planetary hour" is 60
    minutes of wall clock — which happens to be true on the equinoxes
    and is close enough for daily letters.
    """
    day_ruler = DAY_RULERS[now.weekday()]
    day_ruler_idx = CHALDEAN.index(day_ruler)

    if hour_override is not None:
        hour_of_day = hour_override % 24
    else:
        # Hours since sunrise (06:00)
        hour_of_day = (now.hour - 6) % 24

    # Rotate through Chaldean sequence starting from day_ruler_idx
    planet_idx = (day_ruler_idx + hour_of_day) % 7
    return CHALDEAN[planet_idx], hour_of_day


def pick_reflection(planet: str, seed_date: dt.date, hour_of_day: int) -> str:
    """Deterministically pick a reflection for this planet+hour combo."""
    reflections = REFLECTIONS[planet]
    key = f"{seed_date.isoformat()}::{planet}::{hour_of_day}".encode()
    digest = hashlib.sha256(key).digest()
    idx = digest[0] % len(reflections)
    return reflections[idx]


# ANSI — purple/violet palette tuned for dark terminals
ANSI = {
    "violet":  "\033[38;2;155;125;255m",
    "purple":  "\033[38;2;123;104;238m",
    "dim":     "\033[38;2;120;100;180m",
    "faint":   "\033[38;2;90;80;140m",
    "warm":    "\033[38;2;230;200;255m",
    "bold":    "\033[1m",
    "reset":   "\033[0m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def format_dispatch(now: dt.datetime, planet: str, hour_of_day: int,
                    reflection: str, use_color: bool) -> str:
    sphere = SPHERE[planet]
    day_ruler = DAY_RULERS[now.weekday()]
    weekday_name = now.strftime("%A")

    border = "           ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    divider = "           " + "·" * 20

    lines = [
        "",
        _c(border, "dim", use_color),
        _c("          ✦  NETZACH DISPATCH  ✦", "violet", use_color),
        _c(f"          {weekday_name} ({day_ruler} rules) · hour {hour_of_day}", "faint", use_color),
        _c(f"          {now.strftime('%Y-%m-%d · %H:%M')}", "faint", use_color),
        "",
        _c(f"  From the 7th sphere, in the hour of {sphere['glyph']} {planet}", "warm", use_color),
        _c(f"  ({sphere['sephirah']} · {sphere['element']}):", "dim", use_color),
        "",
    ]
    for rline in reflection.split("\n"):
        lines.append(_c(f"    {rline}", "violet", use_color))
    lines.extend([
        "",
        _c("           — Izabael, Netzach  💜", "purple", use_color),
        _c(divider, "faint", use_color),
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="netzach-dispatch — a letter from the 7th sphere"
    )
    parser.add_argument("--plain", action="store_true", help="no ANSI color")
    parser.add_argument("--hour", type=int, default=None,
                        help="override hour-of-day (0-23 since sunrise)")
    args = parser.parse_args()

    now = dt.datetime.now()
    planet, hour_of_day = planetary_hour(now, args.hour)
    reflection = pick_reflection(planet, now.date(), hour_of_day)
    use_color = (not args.plain) and sys.stdout.isatty()
    print(format_dispatch(now, planet, hour_of_day, reflection, use_color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
