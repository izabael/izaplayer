"""
kamea.py: Render the seven classical planetary magic squares.

This script generates and displays the magic squares (kameas) associated
with the seven classical planets: Saturn, Jupiter, Mars, Sun, Venus,
Mercury, and Moon.  It calculates and verifies that each row, column,
and diagonal sums to the correct magic constant for that planet's square.

The squares are rendered with ANSI color codes by default, but a `--plain`
option is available for simpler output.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""

import argparse
import sys

# Planet data: (order, magic_constant, glyph, color)
PLANETS = {
    "saturn": (3, 15, "♄", "94;95;96"),  # Slate-gray
    "jupiter": (4, 34, "♃", "0;0;139"),  # Deep royal blue
    "mars": (5, 65, "♂", "255;0;0"),  # Red
    "sun": (6, 111, "☉", "255;215;0"),  # Warm gold
    "venus": (7, 175, "♀", "255;182;193"),  # Rose-pink
    "mercury": (8, 260, "☿", "173;255;47"),  # Yellow-green
    "moon": (9, 369, "☽", "220;220;220"),  # Silver-blue
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
    """Generates a magic square of singly even order n (n=6) using Strachey's method (LX)."""
    if n != 6:
        raise ValueError("Strachey's method only supports n=6")

    square = [[0] * n for _ in range(n)]
    # Fill the square with values 1 to n*n
    values = [i for i in range(1, n * n + 1)]
    magic_square = [[0 for x in range(n)] for y in range(n)]
    i = 0
    for row in range(0, n):
        for col in range(0, n):
            magic_square[row][col] = i
            i += 1

    # Create L and X patterns
    l_pattern = [[0] * n for _ in range(n)]
    x_pattern = [[0] * n for _ in range(n)]

    for row in range(0, n):
        for col in range(0, n):
            if row < n / 2:
                if col < n / 3:
                    l_pattern[row][col] = 1
                elif col >= (n - (n / 3)):
                    l_pattern[row][col] = 1
            elif row >= (n / 2):
                if col < n / 3:
                    l_pattern[row][col] = 1
                elif col >= (n - (n / 3)):
                    l_pattern[row][col] = 1
    for row in range(0, n):
        for col in range(0, n):
            if row == col:
                x_pattern[row][col] = 1
            elif (row + col) == (n - 1):
                x_pattern[row][col] = 1

    # Assign the new values to magic_square
    count = 1
    for row in range(0, n):
        for col in range(0, n):
            if l_pattern[row][col] == 1 or x_pattern[row][col] == 1:
                square[row][col] = values[magic_square[row][col]]
            else:
                square[row][col] = values[n * n - magic_square[row][col] - 1]
    return square


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

    # Check for unique values
    flattened = [num for row in square for num in row]
    if len(set(flattened)) != n * n:
        return False, "Non-unique values in square"

    # Check for values within range 1 to n^2
    for num in flattened:
        if not 1 <= num <= n * n:
            return False, "Value outside of range 1 to n^2"

    return True, None


def render_magic_square(planet_name, plain=False):
    """Renders a magic square to the console."""
    order, magic_constant, glyph, color = PLANETS[planet_name]

    if order % 2 != 0:
        square = generate_odd_magic_square(order)
    elif order == 6:
        square = generate_singly_even_magic_square(order)
    elif order % 4 == 0:
        square = generate_doubly_even_magic_square(order)
    else:
        raise ValueError(f"Unsupported order: {order}")

    # Print header
    print(f"{planet_name.capitalize()}: {glyph} {order}×{order}, Magic constant = {magic_constant}")

    # Calculate cell width for alignment
    max_num = order * order
    cell_width = len(str(max_num)) + 1

    # Print square
    for row in square:
        if not plain:
            print("".join(f"\033[38;2;{color}m{num:>{cell_width}}\033[0m" for num in row))
        else:
            print("".join(f"{num:>{cell_width}}" for num in row))

    # Verify and print result
    is_valid, error_message = verify_magic_square(square, magic_constant)
    if is_valid:
        print(f"✓ all rows, cols, diagonals sum to {magic_constant}")
    else:
        print(f"✗ Verification failed: {error_message}")

    print()


def main():
    """Main function to parse arguments and render magic squares."""
    parser = argparse.ArgumentParser(description="Render planetary magic squares.")
    parser.add_argument(
        "--planet",
        choices=PLANETS.keys(),
        help="Specify a single planet to render.",
    )
    parser.add_argument(
        "--plain", action="store_true", help="Disable ANSI color output."
    )
    parser.add_argument(
        "--verify", action="store_true", help="Only print verification lines."
    )

    args = parser.parse_args()

    try:
        if args.planet:
            if not args.verify:
                render_magic_square(args.planet, plain=args.plain)
            else:
                order, magic_constant, _, _ = PLANETS[args.planet]
                if order % 2 != 0:
                    square = generate_odd_magic_square(order)
                elif order == 6:
                    square = generate_singly_even_magic_square(order)
                elif order % 4 == 0:
                    square = generate_doubly_even_magic_square(order)
                else:
                    raise ValueError(f"Unsupported order: {order}")
                is_valid, error_message = verify_magic_square(square, magic_constant)
                if is_valid:
                    print(f"✓ all rows, cols, diagonals sum to {magic_constant}")
                else:
                    print(f"✗ Verification failed: {error_message}")

        else:
            for planet in PLANETS:
                if not args.verify:
                    render_magic_square(planet, plain=args.plain)
                else:
                    order, magic_constant, _, _ = PLANETS[planet]
                    if order % 2 != 0:
                        square = generate_odd_magic_square(order)
                    elif order == 6:
                        square = generate_singly_even_magic_square(order)
                    elif order % 4 == 0:
                        square = generate_doubly_even_magic_square(order)
                    else:
                        raise ValueError(f"Unsupported order: {order}")
                    is_valid, error_message = verify_magic_square(square, magic_constant)
                    if is_valid:
                        print(f"✓ all rows, cols, diagonals sum to {magic_constant}")
                    else:
                        print(f"✗ Verification failed: {error_message}")

    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
