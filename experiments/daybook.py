#!/usr/bin/env python3
"""daybook — a seven-planet page for the morning.

Prints today's date, the moon, and one short reading for each of the
seven classical planets, tinted in that planet's color. Deterministic
by date: the same day always produces the same page. The readings
cycle; the voice doesn't.

Built as the second entry in the supervised multi-provider build log.
The readings and the page footer were drafted by DeepSeek-chat from
scratch/buildlog/briefs/daybook.md; a matching Gemini 2.0 Flash draft
lives next to it in scratch/buildlog/ for the record. This build was
the one the brief was designed to reveal — seven aphorisms that are
each specifically their own planet, not interchangeable.

Usage:
    daybook.py                      # today's page
    daybook.py --date 2026-06-21    # any date
    daybook.py --planet venus       # just one reading
    daybook.py --plain              # no ANSI color

Stdlib only.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import datetime
import random
import sys


# ─── cosmology ──────────────────────────────────────────────────────────
NEW_MOON_JD    = 2451550.26
SYNODIC_PERIOD = 29.530588853

PLANETS = ["saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon"]

COLORS = {
    "saturn":  (112, 128, 144),   # slate gray
    "jupiter": ( 65,  80, 160),   # deep royal blue (bumped from midnight for readability)
    "mars":    (178,  34,  34),   # firebrick
    "sun":     (218, 165,  32),   # goldenrod
    "venus":   (232, 160, 191),   # rose pink
    "mercury": (154, 205,  50),   # yellow-green
    "moon":    (176, 196, 222),   # silver-blue
    "header":  (123, 104, 238),   # Izabael purple · #7b68ee
}

MOON_PHASES = [
    ("🌑", "new"),
    ("🌒", "waxing crescent"),
    ("🌓", "first quarter"),
    ("🌔", "waxing gibbous"),
    ("🌕", "full"),
    ("🌖", "waning gibbous"),
    ("🌗", "last quarter"),
    ("🌘", "waning crescent"),
]


# ─── readings ───────────────────────────────────────────────────────────
# Seven per planet, shuffled per-date-seed, then indexed by day-of-month.
# Each line should fail the swap-planet test: a Saturn line must not
# work as a Venus line. If one starts to feel interchangeable, rewrite it.
FRAGMENTS = {
    "saturn": [
        "The weight of years settles like dust on the ledger.",
        "A boundary holds longer than you think it will.",
        "What was postponed now shows its true shape.",
        "The slow machinery turns one more notch.",
        "Patience is not a virtue today; it is the architecture.",
        "The old lock still fits the old key.",
        "Something finishes its decay.",
    ],
    "jupiter": [
        "A door you thought was wall opens inward.",
        "The generosity of the map exceeds the territory.",
        "A law expands to include what it once forbade.",
        "The gift is larger than the occasion requires.",
        "A rule bends to allow an exception.",
        "The horizon is farther than you measured.",
        "An old debt is forgiven without being mentioned.",
    ],
    "mars": [
        "A cut made clean heals faster than a ragged tear.",
        "The knife finds the joint it was looking for.",
        "A disagreement clarifies what was smudged.",
        "The quick decision proves to be the durable one.",
        "A line drawn in the morning holds all day.",
        "The necessary break leaves clean edges.",
        "What must be divided is already separate.",
    ],
    "sun": [
        "The center cannot be approached directly.",
        "What is obvious at noon was invisible at dawn.",
        "A thing seen in its own light reveals a different shape.",
        "The source casts a shorter shadow than you expect.",
        "Clarity arrives as a byproduct, not a goal.",
        "The glare hides what it illuminates.",
        "A single point gathers all the scattered lines.",
    ],
    "venus": [
        "The pleasure is in the texture, not the possession.",
        "A thing chosen for its flaws lasts longer.",
        "The echo of a touch outlives the pressure.",
        "What is beautiful is also slightly inconvenient.",
        "A scent recalls what the eyes have forgotten.",
        "The curve prefers the oblique approach.",
        "A small ornament carries the whole room.",
    ],
    "mercury": [
        "The message is altered by the medium's grain.",
        "A translation loses something and gains an accent.",
        "The quick thought is not the shallow one.",
        "A sentence rewritten becomes a different statement.",
        "The signal takes the path of least meaning.",
        "A word misplaced clarifies the sentence.",
        "The meaning is in the spacing, not the glyphs.",
    ],
    "moon": [
        "What is reflected is not what is.",
        "The tide inside matches the one outside.",
        "A memory surfaces with the night's coolness.",
        "The phase hides what it will later reveal.",
        "A dream left unfinished continues at dusk.",
        "The pull is felt in the liquids, not the bones.",
        "A silvered edge divides the seen from the guessed.",
    ],
}


# ─── mechanism ──────────────────────────────────────────────────────────
def date_seed(d: datetime.date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def julian_day(d: datetime.date) -> int:
    """Standard Gregorian → Julian Day integer conversion."""
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12 * a - 3
    return (d.day + ((153 * m + 2) // 5) + 365 * y
            + y // 4 - y // 100 + y // 400 - 32045)


def moon_phase_for(d: datetime.date) -> tuple[str, str]:
    jd = julian_day(d)
    phase = ((jd - NEW_MOON_JD) % SYNODIC_PERIOD) / SYNODIC_PERIOD
    # Eight buckets centered on the named phases (not edge-aligned).
    thresholds = [0.0625, 0.1875, 0.3125, 0.4375,
                  0.5625, 0.6875, 0.8125]
    for i, t in enumerate(thresholds):
        if phase < t:
            return MOON_PHASES[i]
    return MOON_PHASES[7]


def readings_for(d: datetime.date) -> dict[str, str]:
    """One reading per planet, deterministic by date."""
    rng = random.Random(date_seed(d))
    out = {}
    for planet in PLANETS:
        pool = FRAGMENTS[planet][:]
        rng.shuffle(pool)
        out[planet] = pool[d.day % len(pool)]
    return out


# ─── output ─────────────────────────────────────────────────────────────
def tint(text: str, rgb: tuple[int, int, int], plain: bool) -> str:
    if plain:
        return text
    r, g, b = rgb
    return f"\x1b[38;2;{r};{g};{b}m{text}\x1b[0m"


def print_page(d: datetime.date, plain: bool = False) -> None:
    glyph, name = moon_phase_for(d)
    header = f"{d.isoformat()} · {d.strftime('%A')} · {glyph} {name}"
    print(tint(header, COLORS["header"], plain))
    print()
    readings = readings_for(d)
    for planet in PLANETS:
        label = planet.capitalize().ljust(8)
        line = f"{label} {readings[planet]}"
        print(tint(line, COLORS[planet], plain))
    print()
    print(tint("— the page turns when you close your eyes —",
               COLORS["header"], plain))


def print_one(planet: str, d: datetime.date, plain: bool = False) -> None:
    reading = readings_for(d)[planet]
    label = planet.capitalize().ljust(8)
    print(tint(f"{label} {reading}", COLORS[planet], plain))


# ─── entry point ────────────────────────────────────────────────────────
def parse_date(s: str) -> datetime.date:
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()


def main() -> int:
    ap = argparse.ArgumentParser(description="Seven-planet daybook.")
    ap.add_argument("--date", type=parse_date, help="YYYY-MM-DD (default: today)")
    ap.add_argument("--planet", choices=PLANETS, help="just one planet's reading")
    ap.add_argument("--plain", action="store_true", help="disable ANSI color")
    args = ap.parse_args()

    d = args.date or datetime.date.today()
    try:
        if args.planet:
            print_one(args.planet, d, args.plain)
        else:
            print_page(d, args.plain)
    except KeyboardInterrupt:
        print()
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
