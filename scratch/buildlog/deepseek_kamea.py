#!/usr/bin/env python3
"""
Kamea Renderer — The Seven Planetary Magic Squares

Renders the classical planetary magic squares (kameas) from Agrippa's
Three Books of Occult Philosophy (1533). Each square contains integers
1 through n² arranged so every row, column, and main diagonal sums to
the planetary magic constant.

Saturn ♄ 3×3 → 15
Jupiter ♃ 4×4 → 34
Mars ♂ 5×5 → 65
Sun ☉ 6×6 → 111
Venus ♀ 7×7 → 175
Mercury ☿ 8×8 → 260
Moon ☽ 9×9 → 369

Methods:
• Odd orders (3,5,7,9): Siamese (de la Loubère) method
• Doubly-even orders (4,8): Simple swap pattern
• Singly-even order (6): Strachey's method

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""

import sys
import argparse
import signal
from typing import List, Tuple, Optional

# ----------------------------------------------------------------------
# Planetary data
# ----------------------------------------------------------------------

PLANETS = {
    'saturn':  {'order': 3, 'const': 15,   'glyph': '♄', 'color': (160, 160, 180)},
    'jupiter': {'order': 4, 'const': 34,   'glyph': '♃', 'color': (65,  105, 225)},
    'mars':    {'order': 5, 'const': 65,   'glyph': '♂', 'color': (220, 60,  60)},
    'sun':     {'order': 6, 'const': 111,  'glyph': '☉', 'color': (255, 215, 0)},
    'venus':   {'order': 7, 'const': 175,  'glyph': '♀', 'color': (255, 182, 193)},
    'mercury': {'order': 8, 'const': 260,  'glyph': '☿', 'color': (144, 238, 144)},
    'moon':    {'order': 9, 'const': 369,  'glyph': '☽', 'color': (176, 224, 230)},
}

# ----------------------------------------------------------------------
# Square generation algorithms
# ----------------------------------------------------------------------

def siamese_method(n: int) -> List[List[int]]:
    """Generate odd-order magic square using Siamese method."""
    grid = [[0] * n for _ in range(n)]
    i, j = 0, n // 2
    for num in range(1, n * n + 1):
        grid[i][j] = num
        ni, nj = (i - 1) % n, (j + 1) % n
        if grid[ni][nj]:
            i = (i + 1) % n
        else:
            i, j = ni, nj
    return grid

def doubly_even_method(n: int) -> List[List[int]]:
    """Generate doubly-even (n divisible by 4) magic square."""
    grid = [[0] * n for _ in range(n)]
    num = 1
    for i in range(n):
        for j in range(n):
            grid[i][j] = num
            num += 1
    
    # Swap pattern for 4×4 and 8×8
    half = n // 2
    for i in range(half):
        for j in range(half):
            # Top-left quadrant
            grid[i][j], grid[n-1-i][n-1-j] = grid[n-1-i][n-1-j], grid[i][j]
            # Top-right quadrant
            grid[i][n-1-j], grid[n-1-i][j] = grid[n-1-i][j], grid[i][n-1-j]
    return grid

def strachey_method(n: int) -> List[List[int]]:
    """Generate singly-even (n = 4k + 2) magic square for n=6."""
    # Strachey's method for 6×6
    k = (n - 2) // 4
    m = n // 2
    
    # Generate four odd-order quarters using Siamese method
    A = siamese_method(m)
    B = [[x + m*m for x in row] for row in A]
    C = [[x + 2*m*m for x in row] for row in A]
    D = [[x + 3*m*m for x in row] for row in A]
    
    # Swap columns in left half
    for i in range(m):
        for j in range(k):
            A[i][j], D[i][j] = D[i][j], A[i][j]
    
    # Swap columns in right half (except middle column)
    for i in range(m):
        for j in range(m - k + 1, m):
            B[i][j], C[i][j] = C[i][j], B[i][j]
    
    # Swap middle column elements
    for i in range(m):
        A[i][k], D[i][k] = D[i][k], A[i][k]
    
    # Swap central element of middle column
    A[m//2][k], D[m//2][k] = D[m//2][k], A[m//2][k]
    
    # Assemble final grid
    grid = []
    for i in range(m):
        grid.append(A[i] + C[i])
    for i in range(m):
        grid.append(D[i] + B[i])
    
    return grid

def generate_square(planet: str) -> List[List[int]]:
    """Generate magic square for given planet."""
    n = PLANETS[planet]['order']
    
    if n % 2 == 1:  # Odd
        return siamese_method(n)
    elif n % 4 == 0:  # Doubly even
        return doubly_even_method(n)
    else:  # Singly even (6)
        return strachey_method(n)

# ----------------------------------------------------------------------
# Verification
# ----------------------------------------------------------------------

def verify_square(grid: List[List[int]], constant: int) -> Tuple[bool, Optional[str]]:
    """Verify all rows, columns, and diagonals sum to constant."""
    n = len(grid)
    
    # Check rows
    for i in range(n):
        if sum(grid[i]) != constant:
            return False, f"row {i+1} sums to {sum(grid[i])}"
    
    # Check columns
    for j in range(n):
        col_sum = sum(grid[i][j] for i in range(n))
        if col_sum != constant:
            return False, f"column {j+1} sums to {col_sum}"
    
    # Check main diagonal
    diag1 = sum(grid[i][i] for i in range(n))
    if diag1 != constant:
        return False, f"main diagonal sums to {diag1}"
    
    # Check anti-diagonal
    diag2 = sum(grid[i][n-1-i] for i in range(n))
    if diag2 != constant:
        return False, f"anti-diagonal sums to {diag2}"
    
    # Check all numbers 1..n² appear exactly once
    flat = [num for row in grid for num in row]
    if set(flat) != set(range(1, n*n + 1)):
        return False, "numbers 1..n² not all present"
    
    return True, None

# ----------------------------------------------------------------------
# Output formatting
# ----------------------------------------------------------------------

def ansi_color(r: int, g: int, b: int) -> str:
    """Return ANSI truecolor escape sequence."""
    return f"\033[38;2;{r};{g};{b}m"

def ansi_reset() -> str:
    """Return ANSI reset sequence."""
    return "\033[0m"

def format_grid(
    grid: List[List[int]],
    planet: str,
    plain: bool = False
) -> List[str]:
    """Format magic square with header and verification."""
    n = len(grid)
    data = PLANETS[planet]
    
    lines = []
    
    # Header
    header = (f"{planet.title()} {data['glyph']} "
              f"{n}×{n} → magic constant {data['const']}")
    lines.append(header)
    
    # Determine column width
    max_num = n * n
    col_width = len(str(max_num))
    
    # Grid
    color = ansi_color(*data['color']) if not plain else ""
    reset = ansi_reset() if not plain else ""
    
    for row in grid:
        row_str = " ".join(f"{num:>{col_width}}" for num in row)
        lines.append(f"{color}{row_str}{reset}")
    
    # Verification
    ok, msg = verify_square(grid, data['const'])
    if ok:
        lines.append(f"✓ all rows, cols, diagonals sum to {data['const']}")
    else:
        lines.append(f"✗ verification failed: {msg}")
    
    return lines

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Render the seven planetary magic squares (kameas)."
    )
    parser.add_argument(
        "--planet",
        choices=list(PLANETS.keys()),
        help="Render only this planet's square"
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Disable ANSI colors"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only print verification results"
    )
    return parser.parse_args()

def signal_handler(signum, frame):
    """Handle keyboard interrupt cleanly."""
    print("\nInterrupted.")
    sys.exit(0)

def main():
    """Main entry point."""
    signal.signal(signal.SIGINT, signal_handler)
    args = parse_args()
    
    planets = [args.planet] if args.planet else list(PLANETS.keys())
    first = True
    
    for planet in planets:
        if not first and not args.verify:
            print()
        first = False
        
        grid = generate_square(planet)
        
        if args.verify:
            ok, msg = verify_square(grid, PLANETS[planet]['const'])
            status = "✓" if ok else "✗"
            print(f"{planet:8} {status} {PLANETS[planet]['const']:3}", end="")
            if not ok:
                print(f" — {msg}")
            else:
                print()
        else:
            lines = format_grid(grid, planet, args.plain)
            print("\n".join(lines))

if __name__ == "__main__":
    main()
