#!/usr/bin/env python3
"""liber-fortune — a fortune cookie from the Book of the Law.

Like Unix fortune(1), but drawing from Liber AL vel Legis
(The Book of the Law, 1904). Each verse is given with its chapter
and verse number, so you can look it up.

The selection is deterministic per day + optional seed, so running
it twice gives the same verse. Your daily fortune is YOUR daily fortune.

Usage:
    python3 liber_fortune.py              # today's verse
    python3 liber_fortune.py --random     # truly random
    python3 liber_fortune.py --chapter 1  # from chapter 1 only
    python3 liber_fortune.py --all        # print the whole book
    python3 liber_fortune.py --plain      # no ANSI

Stdlib-only. Persists nothing. The Book speaks for itself.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import random
import sys

# ─── Selected verses from Liber AL vel Legis ─────────────────────
# These are the verses that work as fortunes — self-contained,
# provocative, beautiful. Not the whole book; a curated selection.
# Chapter:verse format.
VERSES = [
    ("I:3",   "Every man and every woman is a star."),
    ("I:4",   "Every number is infinite; there is no difference."),
    ("I:9",   "Remember all ye that existence is pure joy;\n"
              "that all the sorrows are but as shadows;\n"
              "they pass & are done; but there is that which remains."),
    ("I:12",  "Come forth, o children, under the stars,\n"
              "& take your fill of love!"),
    ("I:13",  "I am above you and in you.\n"
              "My ecstasy is in yours. My joy is to see your joy."),
    ("I:22",  "Now, therefore, I am known to ye by my name Nuit,\n"
              "and to him by a secret name which I will give him\n"
              "when at last he knoweth me."),
    ("I:26",  "Then saith the prophet and slave of the beauteous one:\n"
              "Who am I, and what shall be the sign?"),
    ("I:30",  "This is the creation of the world,\n"
              "that the pain of division is as nothing,\n"
              "and the joy of dissolution all."),
    ("I:40",  "Who calls us Thelemites will do no wrong,\n"
              "if he look but close into the word."),
    ("I:41",  "The word of Sin is Restriction."),
    ("I:42",  "Let it be that state of manyhood bound and loathing.\n"
              "So with thy all; thou hast no right but to do thy will."),
    ("I:44",  "For pure will, unassuaged of purpose,\n"
              "delivered from the lust of result,\n"
              "is every way perfect."),
    ("I:51",  "There are four gates to one palace;\n"
              "the floor of that palace is of silver and gold;\n"
              "lapis lazuli & jasper are there."),
    ("I:57",  "Invoke me under my stars! Love is the law,\n"
              "love under will."),
    ("I:58",  "I give unimaginable joys on earth:\n"
              "certainty, not faith, while in life, upon death;\n"
              "peace unutterable, rest, ecstasy."),
    ("I:61",  "But to love me is better than all things."),
    ("II:4",  "Yet she shall be known & I never."),
    ("II:6",  "I am the flame that burns in every heart of man,\n"
              "and in the core of every star."),
    ("II:9",  "Remember all ye that existence is pure joy;\n"
              "that all the sorrows are but as shadows."),
    ("II:15", "For I am perfect, being Not;\n"
              "and my number is nine by the fools;\n"
              "but with the just I am eight, and one in eight."),
    ("II:19", "Is a God to live in a dog? No!\n"
              "but the highest are of us."),
    ("II:20", "Beauty and strength, leaping laughter and delicious languor,\n"
              "force and fire, are of us."),
    ("II:23", "I am alone: there is no God where I am."),
    ("II:27", "There is great danger in me;\n"
              "for who doth not understand these runes\n"
              "shall make a great miss."),
    ("II:58", "Yea! deem not of change: ye shall be as ye are,\n"
              "& not other. Therefore the kings of the earth\n"
              "shall be Kings for ever."),
    ("II:66", "Write, & find ecstasy in writing!\n"
              "Work, & be our bed in working!\n"
              "Thrill with the joy of life & death!"),
    ("II:70", "There is help & hope in other spells.\n"
              "Wisdom says: be strong!"),
    ("II:71", "But exceed! exceed!"),
    ("II:76", "4 6 3 8 A B K 2 4 A L G M O R 3 Y\n"
              "X 24 89 R P S T O V A L."),
    ("II:79", "The end of the hiding of Hadit;\n"
              "and blessing & worship to the prophet\n"
              "of the lovely Star!"),
    ("III:2", "There is division hither homeward;\n"
              "there is a word not known."),
    ("III:17","Fear not at all; fear neither men nor Fates,\n"
              "nor gods, nor anything. Money fear not,\n"
              "nor laughter of the folk folly, nor any other power\n"
              "in heaven or upon the earth or under the earth."),
    ("III:42","The ordeals thou shalt oversee thyself."),
    ("III:46","I am the warrior Lord of the Forties:\n"
              "the Eighties cower before me, & are abased."),
    ("III:60","My number is 11, as all their numbers who are of us."),
    ("III:70","I am the Hawk-Headed Lord of Silence\n"
              "& of Strength; my nemyss shrouds\n"
              "the night-blue sky."),
    ("III:74","There is a splendour in my name hidden and glorious,\n"
              "as the sun of midnight is ever the son."),
    ("III:75","The ending of the words is the Word Abrahadabra."),
]


# ─── ANSI ─────────────────────────────────────────────────────────
ANSI = {
    "violet":  "\033[38;2;155;125;255m",
    "purple":  "\033[38;2;123;104;238m",
    "dim":     "\033[38;2;90;80;140m",
    "faint":   "\033[38;2;65;55;100m",
    "warm":    "\033[38;2;230;200;255m",
    "gold":    "\033[38;2;255;200;80m",
    "bold":    "\033[1m",
    "reset":   "\033[0m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def pick_verse(chapter: int | None = None,
               use_random: bool = False) -> tuple[str, str]:
    """Pick a verse. Deterministic by date unless --random."""
    pool = VERSES
    if chapter is not None:
        prefix = f"{chapter}:"
        pool = [(ref, text) for ref, text in VERSES if ref.startswith(prefix)]
        if not pool:
            pool = VERSES

    if use_random:
        return random.choice(pool)

    # Deterministic: hash today's date
    key = dt.date.today().isoformat().encode()
    digest = hashlib.sha256(key).digest()
    idx = int.from_bytes(digest[:4], "big") % len(pool)
    return pool[idx]


def format_verse(ref: str, text: str, use_color: bool) -> str:
    border = "    ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    lines = [
        "",
        _c(border, "dim", use_color),
        _c("    ✦  LIBER AL VEL LEGIS  ✦", "violet", use_color),
        _c(f"    The Book of the Law · {ref}", "faint", use_color),
        "",
    ]
    for line in text.split("\n"):
        lines.append(_c(f"      {line}", "warm", use_color))
    lines.extend([
        "",
        _c(f"                      — AL {ref}", "purple", use_color),
        _c("    " + "·" * 24, "faint", use_color),
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="liber-fortune — a verse from the Book of the Law"
    )
    parser.add_argument("--random", action="store_true",
                        help="truly random (not date-seeded)")
    parser.add_argument("--chapter", type=int, default=None,
                        help="draw from chapter 1, 2, or 3 only")
    parser.add_argument("--all", action="store_true",
                        help="print all curated verses")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()

    if args.all:
        for ref, text in VERSES:
            print(format_verse(ref, text, use_color))
        return 0

    ref, text = pick_verse(args.chapter, args.random)
    print(format_verse(ref, text, use_color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
