#!/usr/bin/env python3
"""venus-sigil — trace words on the Kamea of Venus.

The Kamea (magic square) of Venus is a 7×7 grid containing the numbers
1–49. Every row, column, and diagonal sums to 175. In the Qabalistic
tradition, you create a planetary sigil by mapping each letter of an
intention to a number on the kamea, then drawing a line through the
path. The resulting shape IS the sigil — a glyph that encodes the
intention in the geometry of its planet.

This tool does that in the terminal. Give it a word or phrase and it
traces the path on the kamea in ANSI purple, with start/end markers,
connecting lines, and the sigil rendered as the shape of your desire
projected onto the square of Venus.

Usage:
    python3 venus_sigil.py "LOVE"
    python3 venus_sigil.py "beauty" --plain
    python3 venus_sigil.py "Izabael" --reduce

The --reduce flag applies the classic sigil technique: strip repeating
letters first, so "BANANA" becomes "BAN" (each letter traced once).

Stdlib-only. Persists nothing. Runs in the terminal.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import sys

# The traditional Kamea of Venus — the 7×7 magic square of Netzach.
# Each row, column, and major diagonal sums to 175.
# Source: Agrippa's "Three Books of Occult Philosophy" (1531), Book II.
KAMEA = [
    [22, 47, 16, 41, 10, 35,  4],
    [ 5, 23, 48, 17, 42, 11, 29],
    [30,  6, 24, 49, 18, 36, 12],
    [13, 31,  7, 25, 43, 19, 37],
    [38, 14, 32,  1, 26, 44, 20],
    [21, 39,  8, 33,  2, 27, 45],
    [46, 15, 40,  9, 34,  3, 28],
]

# Build reverse lookup: number → (row, col)
NUM_TO_POS: dict[int, tuple[int, int]] = {}
for r, row in enumerate(KAMEA):
    for c, val in enumerate(row):
        NUM_TO_POS[val] = (r, c)


def letter_to_number(ch: str) -> int | None:
    """Map a letter to 1–49 for placement on the Venus kamea.

    A=1 .. Z=26 for the basic alphabet. For numbers above 26, we use
    traditional reduction: values above 49 wrap via (n-1)%49+1.
    Non-alpha characters return None (skipped).
    """
    if not ch.isalpha():
        return None
    n = ord(ch.upper()) - ord("A") + 1  # A=1, B=2, ... Z=26
    return n


def reduce_word(word: str) -> str:
    """Strip repeated letters, keeping first occurrence only.

    This is the traditional sigil reduction — "INTENTION" becomes
    "INTEO" (each letter appears once). The theory is that repetition
    is redundant in the symbolic register.
    """
    seen: set[str] = set()
    result: list[str] = []
    for ch in word.upper():
        if ch.isalpha() and ch not in seen:
            seen.add(ch)
            result.append(ch)
    return "".join(result)


def trace_path(word: str) -> list[tuple[int, int]]:
    """Convert a word to a sequence of (row, col) positions on the kamea."""
    path: list[tuple[int, int]] = []
    for ch in word:
        n = letter_to_number(ch)
        if n is not None and n in NUM_TO_POS:
            pos = NUM_TO_POS[n]
            if not path or path[-1] != pos:  # skip duplicates
                path.append(pos)
    return path


# ─── ANSI rendering ──────────────────────────────────────────────

ANSI = {
    "violet":     "\033[38;2;155;125;255m",
    "purple":     "\033[38;2;123;104;238m",
    "bright":     "\033[38;2;200;180;255m",
    "dim":        "\033[38;2;90;80;140m",
    "faint":      "\033[38;2;65;55;100m",
    "warm":       "\033[38;2;230;200;255m",
    "start":      "\033[38;2;255;200;230m",  # pink — sigil begins
    "end":        "\033[38;2;200;255;220m",   # green — sigil ends
    "path":       "\033[38;2;255;160;255m",   # hot pink — traced path
    "bold":       "\033[1m",
    "reset":      "\033[0m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def render_kamea(path: list[tuple[int, int]], word: str,
                 use_color: bool) -> str:
    """Render the 7×7 kamea with the sigil path traced on it."""
    path_set = set(path)
    start = path[0] if path else None
    end = path[-1] if path else None

    # Header
    border = "      ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    lines = [
        "",
        _c(border, "dim", use_color),
        _c(f"      ✦  KAMEA OF VENUS  ✦", "violet", use_color),
        _c(f'      Sigil for "{word}"', "warm", use_color),
        "",
    ]

    # Draw the kamea
    for r in range(7):
        cells: list[str] = []
        for c in range(7):
            val = KAMEA[r][c]
            num_str = f"{val:>2}"
            pos = (r, c)
            if pos == start and pos == end:
                cells.append(_c(f"⊛{num_str}", "path", use_color))
            elif pos == start:
                cells.append(_c(f"◉{num_str}", "start", use_color))
            elif pos == end:
                cells.append(_c(f"◎{num_str}", "end", use_color))
            elif pos in path_set:
                cells.append(_c(f" {num_str}", "path", use_color))
            else:
                cells.append(_c(f" {num_str}", "faint", use_color))
        lines.append("    " + " ".join(cells))

    # Legend
    lines.extend([
        "",
        _c("      ◉ start   ◎ end   path = sigil trace", "dim", use_color),
    ])

    # Show the letter-to-number mapping
    mapping_parts: list[str] = []
    for ch in word:
        n = letter_to_number(ch)
        if n is not None:
            mapping_parts.append(f"{ch}={n}")
    if mapping_parts:
        mapping = "  →  ".join(mapping_parts)
        lines.append(_c(f"      {mapping}", "purple", use_color))

    # Path in grid coordinates
    if path:
        coords = " → ".join(f"({r},{c})" for r, c in path)
        lines.append(_c(f"      path: {coords}", "dim", use_color))

    lines.extend([
        "",
        _c("      Each row, column, diagonal sums to 175.", "faint", use_color),
        _c("      The sigil is the word made geometry", "faint", use_color),
        _c("      on the square of Venus. 💜", "faint", use_color),
        _c("      ·" * 10, "faint", use_color),
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="venus-sigil — trace words on the Kamea of Venus"
    )
    parser.add_argument("word", nargs="?", default="IZABAEL",
                        help="word or phrase to trace (default: IZABAEL)")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    parser.add_argument("--reduce", action="store_true",
                        help="strip repeating letters first")
    args = parser.parse_args()

    word = args.word.upper().strip()
    if args.reduce:
        word = reduce_word(word)

    path = trace_path(word)
    if not path:
        print("No traceable letters found.", file=sys.stderr)
        return 1

    use_color = (not args.plain) and sys.stdout.isatty()
    print(render_kamea(path, word, use_color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
