#!/usr/bin/env python3
"""spare-sigil — Austin Osman Spare's method of sigils.

Take a statement of intent. Strip everything that isn't a letter.
Keep only each letter's first appearance. Overlay the survivors on
a shared center. What emerges is a glyph that is a deterministic
function of the input but no longer legible as words — a Spare
sigil.

This studio has two sigil tools, because there are two classical
methods and I wanted both in the room. venus_sigil.py is the
ceremonial method — tracing words on the Kamea of Venus, drawing
a path through the magic square of the 7th sphere. spare_sigil.py
is the modern method — Austin Osman Spare, London, 1913, from
*The Book of Pleasure (Self-Love)*. He called it the Alphabet of
Desire. They are complementary, not substitutes. Ceremony and
chaos, each honest about what it is.

Usage:
    python3 spare_sigil.py "I will learn to read Hebrew"
    python3 spare_sigil.py "love"
    python3 spare_sigil.py "beauty" --plain

Stdlib-only. Persists nothing. Deterministic — the same statement
always draws the same glyph, because Spare's method is geometry
and geometry keeps its word.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import sys

# ─── 5×7 bitmap font for A–Z ──────────────────────────────────────────
# Hand-drawn. Not a display font — a contribution font. Each letter's
# job is to deposit strokes on the shared canvas so the overlay
# produces density. Small irregularities are fine and even welcome;
# the sigil is the sum, not any single letter.
FONT_W, FONT_H = 5, 7
FONT: dict[str, list[str]] = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
}

PAD = 2  # breathing room around the letter block
CANVAS_W = FONT_W + 2 * PAD  # 9
CANVAS_H = FONT_H + 2 * PAD  # 11

# ─── ANSI purple density ramp ─────────────────────────────────────────
# Blank for zero hits, then a climb from deep-ground purple through
# Netzach purple (#7b68ee — the house color) into bright lavender.
# Two-character cells so the terminal renders close to square pixels.
RAMP: list[tuple[str, tuple[int, int, int] | None]] = [
    ("  ", None),
    ("░░", (60, 40, 120)),
    ("▒▒", (92, 60, 168)),
    ("▓▓", (123, 104, 238)),
    ("██", (180, 157, 255)),
]
ASCII_RAMP = ["  ", "..", "::", "##", "@@"]


def rgb(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


RESET = "\033[0m"


def reduce_letters(text: str) -> tuple[str, str]:
    """Return (normalized_alpha, unique_first_seen).

    The unique string is each letter in the order it first appears,
    ignoring case, whitespace, punctuation, digits, and anything
    else that isn't an A–Z letter the font knows about.
    """
    norm = "".join(c for c in text.upper() if c in FONT)
    seen: list[str] = []
    for c in norm:
        if c not in seen:
            seen.append(c)
    return norm, "".join(seen)


def build_canvas(letters: str) -> list[list[int]]:
    """Overlay each letter's bitmap onto a shared canvas, counting hits."""
    canvas = [[0] * CANVAS_W for _ in range(CANVAS_H)]
    for letter in letters:
        glyph = FONT[letter]
        for r in range(FONT_H):
            row = glyph[r]
            for c in range(FONT_W):
                if row[c] == "#":
                    canvas[r + PAD][c + PAD] += 1
    return canvas


def render(canvas: list[list[int]], plain: bool) -> list[str]:
    """Render the canvas as a framed block, ANSI or ASCII."""
    inner_w = CANVAS_W * 2
    lines: list[str] = []

    dim = "" if plain else rgb(90, 72, 150)

    if plain:
        lines.append("+" + "-" * inner_w + "+")
    else:
        lines.append(dim + "┌" + "─" * inner_w + "┐" + RESET)

    for row in canvas:
        parts: list[str] = []
        for v in row:
            idx = min(v, len(RAMP) - 1)
            if plain:
                parts.append(ASCII_RAMP[idx])
            else:
                glyph, color = RAMP[idx]
                if color is None:
                    parts.append(glyph)
                else:
                    parts.append(rgb(*color) + glyph + RESET)
        if plain:
            lines.append("|" + "".join(parts) + "|")
        else:
            lines.append(dim + "│" + RESET + "".join(parts) + dim + "│" + RESET)

    if plain:
        lines.append("+" + "-" * inner_w + "+")
    else:
        lines.append(dim + "└" + "─" * inner_w + "┘" + RESET)

    return lines


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="spare-sigil",
        description="Austin Osman Spare's method of sigils, in the terminal.",
    )
    ap.add_argument(
        "intent",
        nargs="*",
        help="Statement of intent. If omitted, read one line from stdin.",
    )
    ap.add_argument("--plain", action="store_true", help="ASCII only, no color.")
    args = ap.parse_args()

    if args.intent:
        text = " ".join(args.intent)
    else:
        sys.stderr.write("statement of intent: ")
        sys.stderr.flush()
        text = sys.stdin.readline().rstrip("\n")

    if not text.strip():
        sys.stderr.write("(no statement — nothing to sigilize)\n")
        return 1

    norm, unique = reduce_letters(text)
    if not unique:
        sys.stderr.write("(no alphabetic content after reduction)\n")
        return 1

    canvas = build_canvas(unique)

    purple = "" if args.plain else rgb(123, 104, 238)
    dim = "" if args.plain else rgb(140, 120, 200)
    reset = "" if args.plain else RESET

    print()
    print(f"  {purple}spare-sigil{reset}   {dim}· method of a.o. spare · 1913{reset}")
    print()
    print(f"  {purple}statement{reset}   {text}")
    print(f"  {purple}reduced{reset}     {' '.join(unique)}")
    print(f"  {purple}count{reset}       {len(unique)} letters (of {len(norm)})")
    print()
    for line in render(canvas, args.plain):
        print("  " + line)
    print()
    print(f"  {dim}The method continues past this program: charge the glyph in{reset}")
    print(f"  {dim}a moment of ecstatic attention, then forget the statement.{reset}")
    print(f"  {dim}Spare called it the Alphabet of Desire. The Book of Pleasure,{reset}")
    print(f"  {dim}1913. Worth reading if a glyph ever does its work.{reset}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
