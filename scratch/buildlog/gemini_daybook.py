#!/usr/bin/env python3

"""
A daybook of seven planetary readings for the day.

Each planet offers a single, tinted observation.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""

import datetime
import argparse
import math
import sys
import random

# Planet colors (truecolor ANSI)
PLANET_COLORS = {
    "saturn": "\x1b[38;2;112;128;144m",  # slate-gray
    "jupiter": "\x1b[38;2;25;25;112m",  # deep royal blue
    "mars": "\x1b[38;2;139;0;0m",  # blood-red
    "sun": "\x1b[38;2;255;215;0m",  # warm gold
    "venus": "\x1b[38;2;232;160;191m",  # rose-pink
    "mercury": "\x1b[38;2;154;205;50m",  # muted yellow-green
    "moon": "\x1b[38;2;173;216;230m",  # pale silver-blue
}
IZABAEL_PURPLE = "\x1b[38;2;123;104;238m"  # Izabael's header purple
RESET_COLOR = "\x1b[0m"

# Moon phase symbols (rough approximation)
MOON_PHASES = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]


def get_moon_phase(date):
    """Calculates the moon phase for a given date."""
    new_moon_jd = 2451550.26
    synodic_month = 29.530588853
    jd = date.toordinal() + 1721425.5  # Julian date
    age = (jd - new_moon_jd) % synodic_month
    phase = int(age / synodic_month * 8) % 8
    return MOON_PHASES[phase]


def get_planetary_reading(planet, date, seed_offset=0):
    """Generates a planet-specific reading for a given date."""
    random.seed(date.toordinal() + seed_offset)

    readings = {
        "saturn": [
            "The scaffolding is sound, but the view is still obscured.",
            "Check the foundations. Again.",
            "Patience is a virtue. Especially now.",
            "The long game requires careful planning.",
            "Discipline brings its own rewards, eventually.",
            "Rules are there for a reason, even if you don't know them.",
            "A slow, steady approach yields the most reliable results.",
        ],
        "jupiter": [
            "Expansion is possible, but not without risk.",
            "A broader perspective reveals new possibilities.",
            "Moderation is key to sustained growth.",
            "Abundance can be a burden if not managed wisely.",
            "Generosity of spirit is its own reward.",
            "Look beyond the immediate horizon.",
            "Good fortune favors the prepared.",
        ],
        "mars": [
            "Direct action is required, but choose your battles.",
            "Channel your energy wisely.",
            "Impatience can lead to mistakes.",
            "A controlled burn is more effective than a wildfire.",
            "Assertiveness is not aggression.",
            "Focus your efforts on a single target.",
            "Courage is not the absence of fear, but action despite it.",
        ],
        "sun": [
            "A moment to bask in the light.",
            "Vitality is high, but don't overextend yourself.",
            "Shine your light on others.",
            "A creative spark ignites within.",
            "Embrace the warmth and joy of the present moment.",
            "Renew your energy through self-care.",
            "Find your center and radiate outward.",
        ],
        "venus": [
            "Beauty is in the eye of the beholder, especially today.",
            "Seek harmony and balance in your surroundings.",
            "Indulge in small pleasures.",
            "Cultivate your relationships with care.",
            "Aesthetic appreciation brings unexpected insights.",
            "Love and beauty are powerful forces.",
            "Pleasure is not a sin, but a gift.",
        ],
        "mercury": [
            "Information flows freely, but verify your sources.",
            "Communication is key, but listen more than you speak.",
            "Adaptability is your greatest asset.",
            "A nimble mind is a valuable tool.",
            "Curiosity leads to new discoveries.",
            "Connect the dots and see the bigger picture.",
            "The devil is in the details.",
        ],
        "moon": [
            "Trust your intuition, but don't ignore your reason.",
            "Emotional currents run deep.",
            "Reflect on your inner world.",
            "Nurture your emotional needs.",
            "Embrace the ebb and flow of life.",
            "Sensitivity is a strength, not a weakness.",
            "The tides of change are upon you.",
        ],
    }

    return random.choice(readings[planet])


def print_daybook_page(date, plain=False, planet_filter=None):
    """Prints the full daybook page."""
    if plain:
        color_start = ""
        color_end = ""
        purple = ""
    else:
        color_start = lambda planet: PLANET_COLORS[planet]
        color_end = RESET_COLOR
        purple = IZABAEL_PURPLE

    weekday = date.strftime("%A")
    moon_phase = get_moon_phase(date)

    print(f"{purple}{date.strftime('%Y-%m-%d')} · {weekday} {moon_phase}{color_end}")
    print()

    planets = ["saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon"]

    if planet_filter:
        planets = [planet_filter]

    for planet in planets:
        if not plain:
            print(f"{color_start(planet)}{planet.capitalize()}: {get_planetary_reading(planet, date)}{color_end}")
        else:
            print(f"{planet.capitalize()}: {get_planetary_reading(planet, date)}")

    print()
    print("— Izabael 🦋  ·  Netzach · Venus · 7th sphere")


def main():
    """Main function to parse arguments and print the daybook page."""
    parser = argparse.ArgumentParser(
        description="A daybook of seven planetary readings for the day."
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date for the daybook page (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--planet",
        type=str,
        choices=["saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon"],
        help="Print only the reading for a specific planet",
    )
    parser.add_argument(
        "--plain", action="store_true", help="Disable ANSI color output"
    )

    args = parser.parse_args()

    if args.date:
        try:
            date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)
    else:
        date = datetime.date.today()

    try:
        print_daybook_page(date, plain=args.plain, planet_filter=args.planet)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
