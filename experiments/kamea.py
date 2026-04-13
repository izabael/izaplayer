#!/usr/bin/env python3
"""kamea — render the seven classical planetary magic squares.

Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon — each planet's
kamea from Agrippa's *Three Books of Occult Philosophy* (1533,
Book II, Chapters XVII–XXII). Every row, column, and diagonal sums
to the planet's magic constant, and the file verifies its own
arithmetic at runtime before printing the ✓.

Built as round 3 of the supervised multi-provider build log — the
first round where correctness dominated voice. Gemini 2.0 Flash's
draft shipped: 6 of 7 squares were correct on first try (Saturn,
Jupiter, Mars, Venus, Mercury, Moon), against DeepSeek's 4 of 7.
Both models failed the Sun 6×6 — it is the hardest case, singly-
even, requiring Strachey's method — so the broken construction
was replaced with the historical Agrippa Sol square, hardcoded.
Everything else is Gemini's original draft with a harmonized
color palette matching daybook.py.

Venus especially deserves a look. Netzach is the sphere of Venus,
and the 7×7 is the resident's kamea — the square that venus_sigil.py
traces words on.

Usage:
    kamea.py                      # all seven squares
    kamea.py --planet venus       # just one
    kamea.py --plain              # no color, pipeable
    kamea.py --verify             # verification lines only

Stdlib only.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import sys


# Planet data: (order, magic_constant, glyph, "r;g;b")
# Colors harmonized with experiments/daybook.py for studio consistency.
PLANETS = {
    "saturn":  (3,  15, "♄", "112;128;144"),   # slate gray
    "jupiter": (4,  34, "♃",  "65; 80;160"),   # deep royal blue
    "mars":    (5,  65, "♂", "178; 34; 34"),   # firebrick
    "sun":     (6, 111, "☉", "218;165; 32"),   # goldenrod
    "venus":   (7, 175, "♀", "232;160;191"),   # rose pink
    "mercury": (8, 260, "☿", "154;205; 50"),   # yellow-green
    "moon":    (9, 369, "☽", "176;196;222"),   # silver-blue
}


def generate_odd_magic_square(n):
    """Generates a magic square of odd order n using the Siamese method."""
    square = [[0] * n for _ in range(n)]
    num = 1
    i, j = 0, n // 2

    while num <= n * n:
        square[i][j] = num
        num += 1
        new_i, new_j = (i - 1) % n, (j + 1) % n
        if square[new_i][new_j] == 0:
            i, j = new_i, new_j
        else:
            i = (i + 1) % n
    return square


def generate_singly_even_magic_square(n):
    """Returns the 6×6 Agrippa Sol square, hardcoded from the historical
    source (*Three Books of Occult Philosophy*, 1533, Book II, Ch. XXII).
    Strachey's LUX construction is brittle and the historical square is
    the one ceremonial tradition actually uses."""
    if n != 6:
        raise ValueError("Only n=6 supported for singly-even")
    return [
        [ 6, 32,  3, 34, 35,  1],
        [ 7, 11, 27, 28,  8, 30],
        [19, 14, 16, 15, 23, 24],
        [18, 20, 22, 21, 17, 13],
        [25, 29, 10,  9, 26, 12],
        [36,  5, 33,  4,  2, 31],
    ]


def generate_doubly_even_magic_square(n):
    """Generates a magic square of doubly even order n (n=4 or n=8) using pattern swapping."""
    square = [[0] * n for _ in range(n)]
    values = [i for i in range(1, n * n + 1)]
    index_matrix = [[(i * n) + j + 1 for j in range(n)] for i in range(n)]

    # Create pattern matrix (ones indicate cells to swap)
    pattern_matrix = [[0] * n for _ in range(n)]
    for i in range(n // 4):
        for j in range(n // 4):
            pattern_matrix[i][j] = 1
            pattern_matrix[i][n - 1 - j] = 1
            pattern_matrix[n - 1 - i][j] = 1
            pattern_matrix[n - 1 - i][n - 1 - j] = 1

    # Fill square with values
    for i in range(n // 4, n - n // 4):
        for j in range(n // 4, n - n // 4):
            pattern_matrix[i][j] = 1

    # Swap values based on pattern matrix
    for row in range(n):
        for col in range(n):
            if pattern_matrix[row][col] == 1:
                square[row][col] = index_matrix[row][col]
            else:
                square[row][col] = n * n + 1 - index_matrix[row][col]
    return square


def build_square(planet_name):
    order, _magic, _glyph, _color = PLANETS[planet_name]
    if order % 2 != 0:
        return generate_odd_magic_square(order)
    elif order == 6:
        return generate_singly_even_magic_square(order)
    elif order % 4 == 0:
        return generate_doubly_even_magic_square(order)
    else:
        raise ValueError(f"Unsupported order: {order}")


def verify_magic_square(square, magic_constant):
    """Verifies that a magic square is correct."""
    n = len(square)
    # Check rows
    for row in square:
        if sum(row) != magic_constant:
            return False, f"Row sum {sum(row)} != {magic_constant}"

    # Check columns
    for col in range(n):
        if sum(square[row][col] for row in range(n)) != magic_constant:
            return False, f"Col sum {sum(square[row][col] for row in range(n))} != {magic_constant}"

    # Check diagonals
    if sum(square[i][i] for i in range(n)) != magic_constant:
        return False, f"Diag sum {sum(square[i][i] for i in range(n))} != {magic_constant}"
    if sum(square[i][n - 1 - i] for i in range(n)) != magic_constant:
        return False, f"Diag sum {sum(square[i][n - 1 - i] for i in range(n))} != {magic_constant}"

    # Check for unique values 1..n²
    flattened = [num for row in square for num in row]
    if sorted(flattened) != list(range(1, n * n + 1)):
        return False, "Square does not contain exactly 1..n²"

    return True, None


def render_magic_square(planet_name, plain=False):
    """Renders a magic square to the console."""
    order, magic_constant, glyph, color = PLANETS[planet_name]
    square = build_square(planet_name)

    # Header
    header = f"{planet_name.capitalize()}: {glyph}  {order}×{order}  magic constant {magic_constant}"
    if not plain:
        header = f"\033[38;2;{color}m{header}\033[0m"
    print(header)

    # Cell width
    max_num = order * order
    cell_width = len(str(max_num)) + 1

    # Grid
    for row in square:
        if not plain:
            line = "".join(f"\033[38;2;{color}m{num:>{cell_width}}\033[0m" for num in row)
        else:
            line = "".join(f"{num:>{cell_width}}" for num in row)
        print(line)

    # Verify
    is_valid, error_message = verify_magic_square(square, magic_constant)
    if is_valid:
        print(f"✓ all rows, cols, diagonals sum to {magic_constant}")
    else:
        print(f"✗ Verification failed: {error_message}")
    print()


def verify_only(planet_name):
    order, magic_constant, _, _ = PLANETS[planet_name]
    square = build_square(planet_name)
    is_valid, error_message = verify_magic_square(square, magic_constant)
    glyph = " ✓" if is_valid else " ✗"
    detail = f"{magic_constant}" if is_valid else f"{magic_constant} — {error_message}"
    print(f"{planet_name:<8}{glyph}  {detail}")


def main():
    parser = argparse.ArgumentParser(description="Render planetary magic squares.")
    parser.add_argument("--planet", choices=PLANETS.keys(),
                        help="Specify a single planet.")
    parser.add_argument("--plain", action="store_true",
                        help="Disable ANSI color output.")
    parser.add_argument("--verify", action="store_true",
                        help="Only print per-square verification lines.")
    args = parser.parse_args()

    try:
        planets = [args.planet] if args.planet else list(PLANETS.keys())
        for planet in planets:
            if args.verify:
                verify_only(planet)
            else:
                render_magic_square(planet, plain=args.plain)
    except KeyboardInterrupt:
        print()
        sys.exit(130)


if __name__ == "__main__":
    main()
