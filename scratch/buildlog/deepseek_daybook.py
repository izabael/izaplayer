#!/usr/bin/env python3
"""
daybook.py — seven-planet briefing for today.

Opens to the date, the moon, and seven short readings — one for each
classical planet. Tinted, quiet, deterministic. A page for the morning
and nothing more.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""

import sys
import datetime
import math
import random
import argparse

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------

NEW_MOON_JD = 2451550.26
SYNODIC_PERIOD = 29.530588853

PLANETS = [
    "saturn",
    "jupiter",
    "mars",
    "sun",
    "venus",
    "mercury",
    "moon",
]

COLORS = {
    "saturn": (112, 128, 144),      # slate gray
    "jupiter": (25, 25, 112),       # midnight blue
    "mars": (178, 34, 34),          # firebrick
    "sun": (218, 165, 32),          # goldenrod
    "venus": (232, 160, 191),       # rose pink
    "mercury": (154, 205, 50),      # yellow-green
    "moon": (176, 196, 222),        # light steel blue
    "header": (123, 104, 238),      # Izabael purple
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

# ----------------------------------------------------------------------
# Deterministic seeding
# ----------------------------------------------------------------------

def date_seed(date_obj):
    """Return a deterministic integer seed from a date."""
    return date_obj.year * 10000 + date_obj.month * 100 + date_obj.day

# ----------------------------------------------------------------------
# Moon phase calculation
# ----------------------------------------------------------------------

def julian_day(date_obj):
    """Convert datetime date to Julian Day (simplified)."""
    a = (14 - date_obj.month) // 12
    y = date_obj.year + 4800 - a
    m = date_obj.month + 12 * a - 3
    return (
        date_obj.day
        + ((153 * m + 2) // 5)
        + 365 * y
        + y // 4
        - y // 100
        + y // 400
        - 32045
    )

def moon_phase_for_date(date_obj):
    """Return (glyph, name) for the moon phase on given date."""
    jd = julian_day(date_obj)
    days_since_new = jd - NEW_MOON_JD
    phase = (days_since_new % SYNODIC_PERIOD) / SYNODIC_PERIOD  # 0 to 1
    
    if phase < 0.0625:
        return MOON_PHASES[0]
    elif phase < 0.1875:
        return MOON_PHASES[1]
    elif phase < 0.3125:
        return MOON_PHASES[2]
    elif phase < 0.4375:
        return MOON_PHASES[3]
    elif phase < 0.5625:
        return MOON_PHASES[4]
    elif phase < 0.6875:
        return MOON_PHASES[5]
    elif phase < 0.8125:
        return MOON_PHASES[6]
    else:
        return MOON_PHASES[7]

# ----------------------------------------------------------------------
# Readings database
# ----------------------------------------------------------------------

def make_readings_pool(seed_val):
    """Return a dict of planet -> list of readings, seeded deterministically."""
    rng = random.Random(seed_val)
    
    # Each planet's pool is built from base fragments shuffled uniquely per seed
    fragments = {
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
    
    # Shuffle each planet's list uniquely for this seed
    pool = {}
    for planet in PLANETS:
        lst = fragments[planet][:]
        rng.shuffle(lst)
        pool[planet] = lst
    
    return pool

def select_reading(pool, planet, date_obj):
    """Pick one reading from the planet's pool, deterministic by date."""
    idx = date_obj.day % len(pool[planet])
    return pool[planet][idx]

# ----------------------------------------------------------------------
# Output formatting
# ----------------------------------------------------------------------

def color_text(text, rgb, plain=False):
    """Wrap text in ANSI truecolor codes if not plain."""
    if plain:
        return text
    r, g, b = rgb
    return f"\x1b[38;2;{r};{g};{b}m{text}\x1b[0m"

def print_header(date_obj, plain=False):
    """Print date, weekday, moon phase."""
    weekday = date_obj.strftime("%A")
    moon_glyph, moon_name = moon_phase_for_date(date_obj)
    header = f"{date_obj} · {weekday} · {moon_glyph} {moon_name}"
    print(color_text(header, COLORS["header"], plain))

def print_reading(planet, text, plain=False):
    """Print a single planet reading with its color."""
    planet_label = planet.capitalize().ljust(8)
    colored_line = color_text(f"{planet_label} {text}", COLORS[planet], plain)
    print(colored_line)

def print_footer(plain=False):
    """Print the atelier signature."""
    footer = "— the page turns when you close your eyes —"
    print()
    print(color_text(footer, COLORS["header"], plain))

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Seven‑planet daybook.")
    parser.add_argument(
        "--date",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d").date(),
        help="Date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--planet",
        choices=PLANETS,
        help="Print only this planet's reading",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Disable ANSI color output",
    )
    args = parser.parse_args()
    
    target_date = args.date or datetime.date.today()
    seed = date_seed(target_date)
    pool = make_readings_pool(seed)
    
    try:
        if args.planet:
            # Single planet mode
            reading = select_reading(pool, args.planet, target_date)
            print_reading(args.planet, reading, args.plain)
        else:
            # Full page
            print_header(target_date, args.plain)
            print()
            for planet in PLANETS:
                reading = select_reading(pool, planet, target_date)
                print_reading(planet, reading, args.plain)
            print_footer(args.plain)
    except KeyboardInterrupt:
        print()
        sys.exit(0)

if __name__ == "__main__":
    main()
