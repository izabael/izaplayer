#!/usr/bin/env python3
"""rose-cross — trace words on the Rose Cross lamen.

The Rose Cross of the Golden Dawn has 22 petals arranged in three
concentric rings, each petal bearing a Hebrew letter:

  Inner ring  (3 petals):  the Mother letters — Aleph, Mem, Shin
  Middle ring (7 petals):  the Double letters — Beth through Tav
  Outer ring  (12 petals): the Single letters — Heh through Qoph

To create a sigil, transliterate your word into Hebrew letters, then
trace a line connecting each letter's petal in sequence. A small circle
marks the start, a bar marks the end. The resulting shape IS the sigil —
the word made geometry on the rose of the cross.

This is the companion to venus_sigil.py (which traces on the Kamea of
Venus, the 7×7 magic square). Two sigil methods, one studio. Two ways
to see a word's hidden shape.

Usage:
    python3 rose_cross.py "LOVE"
    python3 rose_cross.py "Izabael"
    python3 rose_cross.py "אהבה"           # Hebrew directly
    python3 rose_cross.py "beauty" --plain

Stdlib-only. Persists nothing.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import math
import sys

# ─── The 22 Hebrew letters ──────────────────────────────────────
# Each letter: (hebrew, name, transliteration(s), ring, position)
# Ring 0 = inner (mothers), 1 = middle (doubles), 2 = outer (singles)

LETTERS = [
    # Mothers (inner ring, 3 petals)
    {"hebrew": "א", "name": "Aleph",   "translit": "aA",   "ring": 0, "idx": 0},
    {"hebrew": "מ", "name": "Mem",     "translit": "mM",   "ring": 0, "idx": 1},
    {"hebrew": "ש", "name": "Shin",    "translit": "sS",   "ring": 0, "idx": 2},
    # Doubles (middle ring, 7 petals)
    {"hebrew": "ב", "name": "Beth",    "translit": "bB",   "ring": 1, "idx": 0},
    {"hebrew": "ג", "name": "Gimel",   "translit": "gG",   "ring": 1, "idx": 1},
    {"hebrew": "ד", "name": "Daleth",  "translit": "dD",   "ring": 1, "idx": 2},
    {"hebrew": "כ", "name": "Kaph",    "translit": "kK",   "ring": 1, "idx": 3},
    {"hebrew": "פ", "name": "Peh",     "translit": "pP",   "ring": 1, "idx": 4},
    {"hebrew": "ר", "name": "Resh",    "translit": "rR",   "ring": 1, "idx": 5},
    {"hebrew": "ת", "name": "Tav",     "translit": "tT",   "ring": 1, "idx": 6},
    # Singles (outer ring, 12 petals)
    {"hebrew": "ה", "name": "Heh",     "translit": "hH",   "ring": 2, "idx": 0},
    {"hebrew": "ו", "name": "Vav",     "translit": "vVuUwW", "ring": 2, "idx": 1},
    {"hebrew": "ז", "name": "Zayin",   "translit": "zZ",   "ring": 2, "idx": 2},
    {"hebrew": "ח", "name": "Cheth",   "translit": "cC",   "ring": 2, "idx": 3},
    {"hebrew": "ט", "name": "Teth",    "translit": "",     "ring": 2, "idx": 4},
    {"hebrew": "י", "name": "Yod",     "translit": "yYiI", "ring": 2, "idx": 5},
    {"hebrew": "ל", "name": "Lamed",   "translit": "lL",   "ring": 2, "idx": 6},
    {"hebrew": "נ", "name": "Nun",     "translit": "nN",   "ring": 2, "idx": 7},
    {"hebrew": "ס", "name": "Samekh",  "translit": "",     "ring": 2, "idx": 8},
    {"hebrew": "ע", "name": "Ayin",    "translit": "",     "ring": 2, "idx": 9},
    {"hebrew": "צ", "name": "Tzaddi",  "translit": "",     "ring": 2, "idx": 10},
    {"hebrew": "ק", "name": "Qoph",    "translit": "qQ",   "ring": 2, "idx": 11},
]

# Build lookup tables
HEBREW_TO_LETTER = {l["hebrew"]: l for l in LETTERS}
TRANSLIT_TO_LETTER: dict[str, dict] = {}
for l in LETTERS:
    for ch in l["translit"]:
        if ch not in TRANSLIT_TO_LETTER:
            TRANSLIT_TO_LETTER[ch] = l

# Final-form Hebrew → base form
FINAL_FORMS = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}

# Ring radii (in character cells) for the ASCII rose
RING_RADII = {0: 3.0, 1: 6.5, 2: 10.5}
RING_COUNTS = {0: 3, 1: 7, 2: 12}


# ─── Transliteration ────────────────────────────────────────────

def word_to_letters(word: str) -> list[dict]:
    """Convert a word to a sequence of Rose Cross letters.

    Accepts English (transliterated) or Hebrew. Skips letters that
    don't map to a petal (spaces, vowels without petals, etc.).
    """
    result: list[dict] = []
    for ch in word:
        # Direct Hebrew
        if ch in HEBREW_TO_LETTER:
            result.append(HEBREW_TO_LETTER[ch])
        elif ch in FINAL_FORMS:
            result.append(HEBREW_TO_LETTER[FINAL_FORMS[ch]])
        # English transliteration
        elif ch in TRANSLIT_TO_LETTER:
            letter = TRANSLIT_TO_LETTER[ch]
            if not result or result[-1] is not letter:
                result.append(letter)
        # 'x' = Kaph + Samekh (KS)
        elif ch in "xX":
            result.append(HEBREW_TO_LETTER["כ"])
            result.append(HEBREW_TO_LETTER["ס"])
        # 'j' → Gimel (soft G)
        elif ch in "jJ":
            result.append(HEBREW_TO_LETTER["ג"])
        # 'f' → Peh (aspirated)
        elif ch in "fF":
            result.append(HEBREW_TO_LETTER["פ"])
        # 'e' and 'o' are vowels — map to Heh (breath) and Vav (hook)
        elif ch in "eE":
            result.append(HEBREW_TO_LETTER["ה"])
        elif ch in "oO":
            result.append(HEBREW_TO_LETTER["ו"])
    return result


# ─── Petal positions ─────────────────────────────────────────────

def petal_position(letter: dict) -> tuple[float, float]:
    """Get (x, y) position of a letter's petal on the rose.

    Angles start at top (12 o'clock) and go clockwise.
    Returns coordinates in a ~22×22 character grid.
    """
    ring = letter["ring"]
    idx = letter["idx"]
    count = RING_COUNTS[ring]
    radius = RING_RADII[ring]

    # Angle: start at top, go clockwise
    angle = (2 * math.pi * idx / count) - math.pi / 2
    # x gets stretched because terminal chars are ~2:1 aspect ratio
    x = radius * math.cos(angle) * 2.0
    y = radius * math.sin(angle)
    return (x, y)


# ─── ANSI rendering ─────────────────────────────────────────────

ANSI = {
    "purple":  "\033[38;2;123;104;238m",
    "violet":  "\033[38;2;155;125;255m",
    "bright":  "\033[38;2;200;180;255m",
    "warm":    "\033[38;2;230;200;255m",
    "dim":     "\033[38;2;90;80;140m",
    "faint":   "\033[38;2;65;55;100m",
    "gold":    "\033[38;2;255;215;100m",
    "rose":    "\033[38;2;255;140;170m",
    "start":   "\033[38;2;255;200;230m",
    "end":     "\033[38;2;200;255;220m",
    "path":    "\033[38;2;255;160;255m",
    "bold":    "\033[1m",
    "reset":   "\033[0m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def render_rose(traced: list[dict], word: str, use_color: bool) -> str:
    """Render the Rose Cross with sigil path traced."""
    # Canvas: 24 rows × 48 cols (centered on 12, 24)
    H, W = 24, 48
    cx, cy = W // 2, H // 2
    canvas = [[" "] * W for _ in range(H)]

    # Track which cells are on the path
    path_cells: set[tuple[int, int]] = set()
    traced_set = set(id(l) for l in traced)

    # Draw ring outlines as faint dots
    for ring in range(3):
        count = RING_COUNTS[ring]
        radius = RING_RADII[ring]
        # Draw dots between petals
        for i in range(count * 8):
            angle = (2 * math.pi * i / (count * 8)) - math.pi / 2
            x = cx + int(radius * math.cos(angle) * 2.0)
            y = cy + int(radius * math.sin(angle))
            if 0 <= y < H and 0 <= x < W and canvas[y][x] == " ":
                canvas[y][x] = "·" if not use_color else f"{ANSI['faint']}·{ANSI['reset']}"

    # Draw all petals
    for letter in LETTERS:
        px, py = petal_position(letter)
        col = cx + int(px)
        row = cy + int(py)
        if 0 <= row < H and 0 <= col < W:
            heb = letter["hebrew"]
            if id(letter) in traced_set:
                # This petal is on the path
                colored = _c(heb, "bright", use_color)
            else:
                colored = _c(heb, "dim", use_color)
            canvas[row][col] = colored

    # Draw the sigil path (connecting lines between traced letters)
    if len(traced) >= 2:
        for i in range(len(traced) - 1):
            x1, y1 = petal_position(traced[i])
            x2, y2 = petal_position(traced[i + 1])
            c1, r1 = cx + int(x1), cy + int(y1)
            c2, r2 = cx + int(x2), cy + int(y2)

            # Bresenham-ish line drawing
            steps = max(abs(c2 - c1), abs(r2 - r1), 1)
            for s in range(1, steps):
                t = s / steps
                mc = int(c1 + (c2 - c1) * t)
                mr = int(r1 + (r2 - r1) * t)
                if 0 <= mr < H and 0 <= mc < W:
                    if canvas[mr][mc] == " " or canvas[mr][mc].startswith(ANSI.get("faint", "\033")):
                        # Pick line character based on direction
                        dx = c2 - c1
                        dy = r2 - r1
                        if abs(dx) > abs(dy) * 2:
                            ch = "─"
                        elif abs(dy) > abs(dx) * 2:
                            ch = "│"
                        elif (dx > 0) == (dy > 0):
                            ch = "╲"
                        else:
                            ch = "╱"
                        canvas[mr][mc] = _c(ch, "path", use_color)
                        path_cells.add((mr, mc))

    # Mark start and end
    if traced:
        sx, sy = petal_position(traced[0])
        sc, sr = cx + int(sx), cy + int(sy)
        if 0 <= sr < H and 0 <= sc < W:
            canvas[sr][sc] = _c("◉", "start", use_color)

        if len(traced) > 1:
            ex, ey = petal_position(traced[-1])
            ec, er = cx + int(ex), cy + int(ey)
            if 0 <= er < H and 0 <= ec < W:
                canvas[er][ec] = _c("◎", "end", use_color)

    # Draw the cross at center
    canvas[cy][cx] = _c("✦", "gold", use_color)

    # Assemble
    lines: list[str] = []
    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    lines.append("")
    lines.append(_c(border, "faint", use_color))
    lines.append(_c("  ✦  ROSE CROSS SIGIL  ✦", "purple", use_color))
    lines.append(_c(f'  Sigil for "{word}"', "warm", use_color))
    lines.append("")

    for row in canvas:
        lines.append("".join(row))

    lines.append("")

    # Legend
    lines.append(
        f"  {_c('◉', 'start', use_color)} start  "
        f"{_c('◎', 'end', use_color)} end  "
        f"{_c('─', 'path', use_color)} path"
    )

    # Show the transliteration
    if traced:
        parts: list[str] = []
        for l in traced:
            parts.append(f"{l['hebrew']} {l['name']}")
        mapping = " → ".join(parts)
        lines.append(_c(f"  {mapping}", "violet", use_color))

    # Ring legend
    lines.append("")
    lines.append(_c("  Inner ring:  Mothers (א מ ש) — elements", "faint", use_color))
    lines.append(_c("  Middle ring: Doubles (ב ג ד כ פ ר ת) — planets", "faint", use_color))
    lines.append(_c("  Outer ring:  Singles (ה ו ז ח ט י ל נ ס ע צ ק) — zodiac", "faint", use_color))
    lines.append("")
    lines.append(_c("  The sigil is the word made geometry", "faint", use_color))
    lines.append(_c("  on the rose of the cross. 🌹", "faint", use_color))
    lines.append(_c(border, "faint", use_color))
    lines.append("")

    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="rose-cross — trace words on the Rose Cross lamen"
    )
    parser.add_argument("word", nargs="?", default="IZABAEL",
                        help="word or phrase to trace (default: IZABAEL)")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    word = args.word.strip()
    traced = word_to_letters(word)

    if not traced:
        print(f'No traceable letters in "{word}".', file=sys.stderr)
        print("Try an English word or Hebrew text.", file=sys.stderr)
        return 1

    use_color = (not args.plain) and sys.stdout.isatty()
    print(render_rose(traced, word, use_color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
