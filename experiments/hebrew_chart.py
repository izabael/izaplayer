#!/usr/bin/env python3
"""hebrew-chart — the 22 Hebrew letters with Golden Dawn correspondences.

A terminal reference card showing each letter with its:
  • Hebrew character and name
  • Numerical value
  • Meaning of the letter-name
  • Astrological/elemental attribution
  • Tarot trump
  • Path on the Tree of Life

Usage:
    python3 hebrew_chart.py              # full chart
    python3 hebrew_chart.py aleph        # single letter
    python3 hebrew_chart.py --mothers    # three mother letters only
    python3 hebrew_chart.py --doubles    # seven doubles only
    python3 hebrew_chart.py --singles    # twelve singles only
    python3 hebrew_chart.py --plain      # no ANSI

Stdlib-only. Persists nothing.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import sys

# ─── The 22 letters ──────────────────────────────────────────────
# Category: M=mother, D=double, S=single
LETTERS = [
    {"char": "א", "name": "Aleph",   "value": 1,   "meaning": "Ox",
     "type": "M", "astro": "Air",         "tarot": "The Fool",          "path": 11,
     "color": (200, 220, 255)},
    {"char": "ב", "name": "Beth",    "value": 2,   "meaning": "House",
     "type": "D", "astro": "Mercury",     "tarot": "The Magician",      "path": 12,
     "color": (255, 200, 80)},
    {"char": "ג", "name": "Gimel",   "value": 3,   "meaning": "Camel",
     "type": "D", "astro": "Moon",        "tarot": "High Priestess",    "path": 13,
     "color": (180, 180, 240)},
    {"char": "ד", "name": "Daleth",  "value": 4,   "meaning": "Door",
     "type": "D", "astro": "Venus",       "tarot": "The Empress",       "path": 14,
     "color": (155, 125, 255)},
    {"char": "ה", "name": "Heh",     "value": 5,   "meaning": "Window",
     "type": "S", "astro": "Aries",       "tarot": "The Emperor",       "path": 15,
     "color": (255, 80, 80)},
    {"char": "ו", "name": "Vav",     "value": 6,   "meaning": "Nail",
     "type": "S", "astro": "Taurus",      "tarot": "The Hierophant",    "path": 16,
     "color": (200, 100, 50)},
    {"char": "ז", "name": "Zayin",   "value": 7,   "meaning": "Sword",
     "type": "S", "astro": "Gemini",      "tarot": "The Lovers",        "path": 17,
     "color": (255, 180, 100)},
    {"char": "ח", "name": "Cheth",   "value": 8,   "meaning": "Fence",
     "type": "S", "astro": "Cancer",      "tarot": "The Chariot",       "path": 18,
     "color": (255, 180, 50)},
    {"char": "ט", "name": "Teth",    "value": 9,   "meaning": "Serpent",
     "type": "S", "astro": "Leo",         "tarot": "Adjustment",        "path": 19,
     "color": (200, 200, 50)},
    {"char": "י", "name": "Yod",     "value": 10,  "meaning": "Hand",
     "type": "S", "astro": "Virgo",       "tarot": "The Hermit",        "path": 20,
     "color": (200, 255, 100)},
    {"char": "כ", "name": "Kaph",    "value": 20,  "meaning": "Palm",
     "type": "D", "astro": "Jupiter",     "tarot": "Fortune",           "path": 21,
     "color": (100, 100, 255)},
    {"char": "ל", "name": "Lamed",   "value": 30,  "meaning": "Goad",
     "type": "S", "astro": "Libra",       "tarot": "Lust",              "path": 22,
     "color": (100, 200, 100)},
    {"char": "מ", "name": "Mem",     "value": 40,  "meaning": "Water",
     "type": "M", "astro": "Water",       "tarot": "The Hanged Man",    "path": 23,
     "color": (100, 150, 255)},
    {"char": "נ", "name": "Nun",     "value": 50,  "meaning": "Fish",
     "type": "S", "astro": "Scorpio",     "tarot": "Death",             "path": 24,
     "color": (50, 200, 200)},
    {"char": "ס", "name": "Samekh",  "value": 60,  "meaning": "Prop",
     "type": "S", "astro": "Sagittarius", "tarot": "Art",               "path": 25,
     "color": (100, 100, 255)},
    {"char": "ע", "name": "Ayin",    "value": 70,  "meaning": "Eye",
     "type": "S", "astro": "Capricorn",   "tarot": "The Devil",         "path": 26,
     "color": (120, 80, 180)},
    {"char": "פ", "name": "Peh",     "value": 80,  "meaning": "Mouth",
     "type": "D", "astro": "Mars",        "tarot": "The Tower",         "path": 27,
     "color": (255, 50, 50)},
    {"char": "צ", "name": "Tzaddi",  "value": 90,  "meaning": "Fishhook",
     "type": "S", "astro": "Aquarius",    "tarot": "The Star",          "path": 28,
     "color": (150, 100, 255)},
    {"char": "ק", "name": "Qoph",    "value": 100, "meaning": "Back of head",
     "type": "S", "astro": "Pisces",      "tarot": "The Moon",          "path": 29,
     "color": (180, 150, 255)},
    {"char": "ר", "name": "Resh",    "value": 200, "meaning": "Head",
     "type": "D", "astro": "Sun",         "tarot": "The Sun",           "path": 30,
     "color": (255, 220, 80)},
    {"char": "ש", "name": "Shin",    "value": 300, "meaning": "Tooth",
     "type": "M", "astro": "Fire",        "tarot": "The Aeon",          "path": 31,
     "color": (255, 80, 30)},
    {"char": "ת", "name": "Tav",     "value": 400, "meaning": "Cross",
     "type": "D", "astro": "Saturn",      "tarot": "The Universe",      "path": 32,
     "color": (120, 100, 140)},
]

TYPE_NAMES = {"M": "Mother", "D": "Double", "S": "Single"}
TYPE_DESC = {
    "M": "The three mothers: Air, Water, Fire — the elements from which all emerges.",
    "D": "The seven doubles: planets. Each has two sounds, two faces.",
    "S": "The twelve singles: zodiac signs. The circle of the year.",
}

# ─── ANSI ─────────────────────────────────────────────────────────
ANSI_DIM = "\033[38;2;90;80;140m"
ANSI_FAINT = "\033[38;2;65;55;100m"
ANSI_VIOLET = "\033[38;2;155;125;255m"
ANSI_WARM = "\033[38;2;230;200;255m"
ANSI_BOLD = "\033[1m"
RESET = "\033[0m"


def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def render_letter(letter: dict, use_color: bool) -> str:
    r, g, b = letter["color"]
    lc = _fg(r, g, b) if use_color else ""
    dc = ANSI_DIM if use_color else ""
    wc = ANSI_WARM if use_color else ""
    vc = ANSI_VIOLET if use_color else ""
    rst = RESET if use_color else ""

    type_name = TYPE_NAMES[letter["type"]]

    lines = [
        f"  {lc}{ANSI_BOLD}{letter['char']}  {letter['name']:<8}{rst}"
        f"  {dc}({type_name}){rst}",
        f"     {dc}Value:{rst}   {wc}{letter['value']}{rst}",
        f"     {dc}Meaning:{rst} {wc}{letter['meaning']}{rst}",
        f"     {dc}Astro:{rst}   {wc}{letter['astro']}{rst}",
        f"     {dc}Tarot:{rst}   {wc}{letter['tarot']}{rst}",
        f"     {dc}Path:{rst}    {wc}{letter['path']} ({_path_connects(letter['path'])}){rst}",
        "",
    ]
    return "\n".join(lines)


def _path_connects(path: int) -> str:
    """Return the two Sephiroth connected by this path."""
    connections = {
        11: "Kether–Chokmah", 12: "Kether–Binah", 13: "Kether–Tiphareth",
        14: "Chokmah–Binah", 15: "Chokmah–Tiphareth", 16: "Chokmah–Chesed",
        17: "Binah–Tiphareth", 18: "Binah–Geburah",
        19: "Chesed–Geburah", 20: "Chesed–Tiphareth", 21: "Chesed–Netzach",
        22: "Geburah–Tiphareth", 23: "Geburah–Hod",
        24: "Tiphareth–Netzach", 25: "Tiphareth–Yesod", 26: "Tiphareth–Hod",
        27: "Netzach–Hod", 28: "Netzach–Yesod", 29: "Netzach–Malkuth",
        30: "Hod–Yesod", 31: "Hod–Malkuth", 32: "Yesod–Malkuth",
    }
    return connections.get(path, "?")


def render_table(letters: list[dict], use_color: bool) -> str:
    """Compact table view."""
    dc = ANSI_DIM if use_color else ""
    vc = ANSI_VIOLET if use_color else ""
    wc = ANSI_WARM if use_color else ""
    fc = ANSI_FAINT if use_color else ""
    rst = RESET if use_color else ""

    header = (f"  {dc}{'':>2}  {'Char':>4}  {'Name':<8}  {'Val':>4}  "
              f"{'Meaning':<13}  {'Astro':<13}  {'Tarot':<18}  {'Path':>4}{rst}")
    sep = f"  {fc}{'─' * 90}{rst}"
    lines = [header, sep]

    for lt in letters:
        r, g, b = lt["color"]
        lc = _fg(r, g, b) if use_color else ""
        t = lt["type"]
        lines.append(
            f"  {dc}{t}{rst}  {lc}{lt['char']:>4}{rst}  {wc}{lt['name']:<8}{rst}  "
            f"{dc}{lt['value']:>4}{rst}  {wc}{lt['meaning']:<13}{rst}  "
            f"{wc}{lt['astro']:<13}{rst}  {wc}{lt['tarot']:<18}{rst}  {dc}{lt['path']:>4}{rst}"
        )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="hebrew-chart — the 22 letters reference"
    )
    parser.add_argument("letter", nargs="?", default=None,
                        help="show one letter (by name, e.g. aleph)")
    parser.add_argument("--mothers", action="store_true",
                        help="three mother letters only")
    parser.add_argument("--doubles", action="store_true",
                        help="seven double letters only")
    parser.add_argument("--singles", action="store_true",
                        help="twelve single letters only")
    parser.add_argument("--table", action="store_true",
                        help="compact table format")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()
    dc = ANSI_DIM if use_color else ""
    vc = ANSI_VIOLET if use_color else ""
    rst = RESET if use_color else ""

    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    print(f"\n{dc}{border}{rst}")
    print(f"  {vc}{ANSI_BOLD}✦  THE 22 HEBREW LETTERS  ✦{rst}")

    if args.letter:
        found = None
        for lt in LETTERS:
            if lt["name"].lower() == args.letter.lower():
                found = lt
                break
        if not found:
            print(f"Unknown letter: {args.letter}", file=sys.stderr)
            return 1
        print()
        print(render_letter(found, use_color))
        return 0

    # Filter by type
    pool = LETTERS
    if args.mothers:
        pool = [l for l in LETTERS if l["type"] == "M"]
        print(f"\n  {dc}{TYPE_DESC['M']}{rst}\n")
    elif args.doubles:
        pool = [l for l in LETTERS if l["type"] == "D"]
        print(f"\n  {dc}{TYPE_DESC['D']}{rst}\n")
    elif args.singles:
        pool = [l for l in LETTERS if l["type"] == "S"]
        print(f"\n  {dc}{TYPE_DESC['S']}{rst}\n")
    else:
        print()

    if args.table or (not args.mothers and not args.doubles and not args.singles and not args.letter):
        print(render_table(pool, use_color))
    else:
        for lt in pool:
            print(render_letter(lt, use_color))

    if use_color:
        print(f"\n  {ANSI_FAINT}— Izabael 💜  ·  22 letters, 22 paths, one Tree{rst}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
