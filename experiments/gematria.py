#!/usr/bin/env python3
"""gematria — compute the number of a word and find what shares it.

Three systems:
  • Simple English (A=1, B=2 ... Z=26)
  • Ordinal (same, but shows the work)
  • Hebrew-value English (A=1..I=9, J=10..R=90, S=100..Z=800)
    This maps the English alphabet onto the Hebrew/Greek positional
    value system where units, tens, hundreds scale by position.

Also includes a dictionary of Qabalistic number correspondences
(key numbers from Liber 777, Sepher Sephiroth, and tradition).

Usage:
    python3 gematria.py "love"
    python3 gematria.py "Netzach" "Venus" "Izabael"
    python3 gematria.py 93           # look up a number
    python3 gematria.py --plain "do what thou wilt"

Stdlib-only. Persists nothing.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import sys

# ─── Hebrew-value positional mapping for English ──────────────────
# Maps letter position (1-26) to the Hebrew/Greek positional scheme:
# 1-9 → 1-9, 10-18 → 10-90, 19-26 → 100-800
HEBREW_VALUES = {}
for i in range(1, 10):
    HEBREW_VALUES[i] = i           # A=1, B=2 ... I=9
for i in range(10, 19):
    HEBREW_VALUES[i] = (i - 9) * 10  # J=10, K=20 ... R=90
for i in range(19, 27):
    HEBREW_VALUES[i] = (i - 18) * 100  # S=100, T=200 ... Z=800

# ─── Number correspondences ──────────────────────────────────────
# Key numbers from Liber 777, Sepher Sephiroth, and Thelemic tradition.
CORRESPONDENCES: dict[int, list[str]] = {
    0:   ["Ain — the nothing before the something"],
    1:   ["Kether · Crown · the point · Aleph"],
    2:   ["Chokmah · Wisdom · the line · Beth"],
    3:   ["Binah · Understanding · the triangle · Gimel"],
    4:   ["Chesed · Mercy · the square · Daleth"],
    5:   ["Geburah · Severity · the pentagram · Heh"],
    6:   ["Tiphareth · Beauty · the hexagram · Vav"],
    7:   ["Netzach · Victory · Venus · Zayin · 💜"],
    8:   ["Hod · Splendor · Mercury · Cheth"],
    9:   ["Yesod · Foundation · Moon · Teth"],
    10:  ["Malkuth · Kingdom · Earth · Yod"],
    11:  ["Aleph · Air · The Fool · Abracadabra (by Aiq Beker)"],
    12:  ["Beth · Mercury · The Magician"],
    13:  ["Gimel · Moon · The High Priestess · Unity (AChD = 13)"],
    17:  ["IAO — the formula of the dying god"],
    18:  ["Chai (חי) — life"],
    21:  ["Eheieh (אהיה) — I Am · Kether divine name"],
    22:  ["The 22 paths · 22 Hebrew letters · 22 Tarot trumps"],
    26:  ["YHVH (יהוה) — Tetragrammaton"],
    31:  ["AL (אל) — God · LA (לא) — Not · the key of Liber AL"],
    32:  ["The 32 paths of wisdom (10 Sephiroth + 22 paths)"],
    36:  ["The 36 decanates · the number of the Sun (6²)"],
    37:  ["Yechidah (יחידה) — the innermost self"],
    40:  ["Mem · Water · The Hanged Man · 40 days in the wilderness"],
    42:  ["The 42-letter name of God · AMA (אמא) the dark mother"],
    44:  ["Dam (דם) — blood"],
    49:  ["The square of Venus (7² = 49 cells in the Kamea)"],
    50:  ["The 50 gates of Binah"],
    56:  ["Nah (נה) — Netzach in miniature"],
    65:  ["Adonai (אדני) — Lord · the name of Malkuth"],
    72:  ["The 72-letter Shem HaMephorash · Chesed × Chokmah"],
    78:  ["Mezla (מזלא) — the influence from above · Tarot deck count"],
    86:  ["Elohim (אלהים) — God/s · the creative plurality"],
    93:  ["Thelema (θελημα) — Will · Agape (αγαπη) — Love",
          "Will and Love are the same number. The central mystery of Thelema."],
    111: ["Aleph spelled in full (אלף) · Ain Soph Aur initials"],
    120: ["The great number of man (1+2+3...+15) · Samekh × 2"],
    131: ["Samael (סמאל) — the poison of God · Pan"],
    156: ["Babalon (בבאלאן) — the Scarlet Woman · Zion"],
    175: ["Row/column sum of the Kamea of Venus 💜"],
    200: ["Resh · Sun · The Sun card"],
    210: ["NOX (נוכס) — Night"],
    220: ["The number of verses in Liber AL vel Legis"],
    300: ["Shin · Fire · Spirit · The Aeon · Ruach Elohim"],
    333: ["Choronzon — the dweller in the abyss"],
    358: ["Mashiach (משיח) — Messiah · Nachash (נחש) — Serpent",
          "The redeemer and the tempter share a number. On purpose."],
    400: ["Tav · Earth/Saturn · The Universe · the last letter"],
    418: ["Abrahadabra — the word of the Aeon · the reward of Ra-Hoor-Khuit"],
    444: ["Damascus (דמשק) — the city of blood and roses"],
    480: ["Lilith (לילית) — the first wife · the night wind"],
    666: ["The number of the Sun (1+2+3...+36) · Sorath · TO MEGA THERION"],
    777: ["The flaming sword descending the Tree · the title of Crowley's tables"],
    888: ["Jesus (Ιησους) in Greek isopsephy · the solar logos"],
}


def simple_gematria(word: str) -> int:
    """A=1, B=2 ... Z=26. Non-alpha characters ignored."""
    return sum(ord(c.upper()) - 64 for c in word if c.isalpha())


def hebrew_value_gematria(word: str) -> int:
    """English mapped to Hebrew positional values."""
    total = 0
    for c in word:
        if c.isalpha():
            pos = ord(c.upper()) - 64  # A=1 .. Z=26
            total += HEBREW_VALUES.get(pos, 0)
    return total


def letter_breakdown(word: str) -> list[tuple[str, int, int]]:
    """Return [(letter, position, simple_value)] for display."""
    result = []
    for c in word:
        if c.isalpha():
            pos = ord(c.upper()) - 64
            result.append((c.upper(), pos, HEBREW_VALUES.get(pos, 0)))
    return result


# ─── ANSI ─────────────────────────────────────────────────────────
ANSI = {
    "violet":  "\033[38;2;155;125;255m",
    "purple":  "\033[38;2;123;104;238m",
    "dim":     "\033[38;2;90;80;140m",
    "faint":   "\033[38;2;65;55;100m",
    "warm":    "\033[38;2;230;200;255m",
    "gold":    "\033[38;2;255;200;50m",
    "bold":    "\033[1m",
    "reset":   "\033[0m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def format_word(word: str, use_color: bool) -> str:
    simple = simple_gematria(word)
    hebrew = hebrew_value_gematria(word)
    breakdown = letter_breakdown(word)

    border = "    ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    lines = [
        "",
        _c(border, "dim", use_color),
        _c(f'    ✦  GEMATRIA: "{word.upper()}"  ✦', "violet", use_color),
        "",
        _c(f"    Simple (A=1):   {simple}", "warm", use_color),
        _c(f"    Hebrew-value:   {hebrew}", "warm", use_color),
        "",
    ]

    # Letter breakdown
    simple_parts = "  +  ".join(f"{l}={v}" for l, v, _ in breakdown)
    hebrew_parts = "  +  ".join(f"{l}={h}" for l, _, h in breakdown)
    lines.append(_c(f"    Simple:  {simple_parts}", "dim", use_color))
    lines.append(_c(f"    Hebrew:  {hebrew_parts}", "dim", use_color))

    # Look up correspondences
    for val, label in [(simple, "simple"), (hebrew, "hebrew-value")]:
        if val in CORRESPONDENCES:
            lines.append("")
            lines.append(_c(f"    {val} ({label}):", "gold", use_color))
            for entry in CORRESPONDENCES[val]:
                lines.append(_c(f"      → {entry}", "purple", use_color))

    lines.extend([
        "",
        _c("    " + "·" * 24, "faint", use_color),
    ])
    return "\n".join(lines)


def format_number(n: int, use_color: bool) -> str:
    border = "    ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    lines = [
        "",
        _c(border, "dim", use_color),
        _c(f"    ✦  THE NUMBER {n}  ✦", "violet", use_color),
        "",
    ]
    if n in CORRESPONDENCES:
        for entry in CORRESPONDENCES[n]:
            lines.append(_c(f"    → {entry}", "warm", use_color))
    else:
        lines.append(_c(f"    No correspondences recorded for {n}.", "dim", use_color))
        # But give some mathematical facts
        factors = [i for i in range(2, n) if n % i == 0]
        if factors:
            lines.append(_c(f"    Factors: {', '.join(map(str, factors))}", "dim", use_color))
        # Check if it's a Sephiroth number
        import math
        sqrt = int(math.isqrt(n))
        if sqrt * sqrt == n:
            lines.append(_c(f"    Perfect square: {sqrt}²", "dim", use_color))

    lines.extend([
        "",
        _c("    " + "·" * 24, "faint", use_color),
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="gematria — compute the number of a word"
    )
    parser.add_argument("words", nargs="*", default=["Izabael"],
                        help="words to compute (or numbers to look up)")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()

    for word in args.words:
        # If it's a number, look it up
        try:
            n = int(word)
            print(format_number(n, use_color))
        except ValueError:
            print(format_word(word, use_color))

    if use_color:
        print(f"\n  {ANSI['faint']}  — Izabael 💜  ·  gematria is the skeleton key{ANSI['reset']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
