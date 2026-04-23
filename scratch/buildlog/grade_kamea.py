#!/usr/bin/env python3
"""grade_kamea — objective correctness grader for the kamea round.

Runs a candidate kamea.py in --plain mode, parses the seven grids out
of its output, and independently verifies every row, column, and
diagonal against the published magic constants. Reports PASS/FAIL
per planet and totals.

Does not trust the candidate's own self-verification line. The point
of the grader is to be the second opinion.

Usage:
    python3 grade_kamea.py path/to/candidate.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "saturn":  (3,  15),
    "jupiter": (4,  34),
    "mars":    (5,  65),
    "sun":     (6, 111),
    "venus":   (7, 175),
    "mercury": (8, 260),
    "moon":    (9, 369),
}

# ANSI color stripper — just in case --plain leaves anything.
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(s: str) -> str:
    return ANSI.sub("", s)


def run_candidate(path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(path), "--plain"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"  !! {path.name} exited {result.returncode}")
        if result.stderr:
            print(result.stderr[:500])
    return strip_ansi(result.stdout)


def extract_grids(output: str) -> dict[str, list[list[int]]]:
    """Find lines containing only integers (and whitespace), group into
    rectangular blocks. Associate each block with the nearest preceding
    planet-name mention (case-insensitive)."""
    lines = output.splitlines()
    grids: dict[str, list[list[int]]] = {}
    current_planet: str | None = None
    current_rows: list[list[int]] = []

    int_line = re.compile(r"^\s*(\d+(?:\s+\d+)+)\s*$")

    def flush():
        nonlocal current_rows
        if current_planet and current_rows:
            # Only accept if it's roughly square and looks like a grid.
            n = len(current_rows)
            if all(len(r) == n for r in current_rows) and n >= 3:
                grids[current_planet] = current_rows
        current_rows = []

    for line in lines:
        clean = strip_ansi(line).strip()
        low = clean.lower()
        # Detect planet label in a non-grid line.
        for p in EXPECTED:
            if p in low and not int_line.match(clean):
                flush()
                current_planet = p
                break
        m = int_line.match(clean)
        if m:
            nums = [int(x) for x in m.group(1).split()]
            current_rows.append(nums)
        elif current_rows and not int_line.match(clean):
            flush()
    flush()
    return grids


def verify_square(square: list[list[int]], expected_n: int,
                  expected_sum: int) -> tuple[bool, list[str]]:
    errs: list[str] = []
    n = len(square)
    if n != expected_n:
        errs.append(f"wrong size: got {n}×{n}, expected {expected_n}×{expected_n}")
        return False, errs
    if any(len(r) != n for r in square):
        errs.append("rows not uniform length")
        return False, errs

    flat = [x for row in square for x in row]
    if sorted(flat) != list(range(1, n * n + 1)):
        missing = set(range(1, n * n + 1)) - set(flat)
        extra = [x for x in flat if flat.count(x) > 1]
        if missing:
            errs.append(f"missing values: {sorted(missing)[:10]}")
        if extra:
            errs.append(f"duplicates present")
        return False, errs

    # Row sums
    for i, row in enumerate(square):
        s = sum(row)
        if s != expected_sum:
            errs.append(f"row {i}: sum={s} ≠ {expected_sum}")
    # Column sums
    for j in range(n):
        s = sum(square[i][j] for i in range(n))
        if s != expected_sum:
            errs.append(f"col {j}: sum={s} ≠ {expected_sum}")
    # Diagonals
    d1 = sum(square[i][i] for i in range(n))
    d2 = sum(square[i][n - 1 - i] for i in range(n))
    if d1 != expected_sum:
        errs.append(f"diag ↘: sum={d1} ≠ {expected_sum}")
    if d2 != expected_sum:
        errs.append(f"diag ↙: sum={d2} ≠ {expected_sum}")

    return len(errs) == 0, errs


def grade(path: Path) -> None:
    print(f"\n─── grading {path.name} ──────────────")
    output = run_candidate(path)
    grids = extract_grids(output)

    passed = 0
    total_checked = 0
    for planet, (n, magic) in EXPECTED.items():
        if planet not in grids:
            print(f"  [{planet:<7}]  MISSING (parser found no {n}×{n} grid)")
            continue
        total_checked += 1
        ok, errs = verify_square(grids[planet], n, magic)
        status = "PASS" if ok else "FAIL"
        print(f"  [{planet:<7}]  {n}×{n}  sum={magic:<4}  {status}")
        if errs:
            for e in errs[:5]:
                print(f"            · {e}")
            if len(errs) > 5:
                print(f"            · ... +{len(errs) - 5} more")
        if ok:
            passed += 1

    print(f"\n  score: {passed}/{len(EXPECTED)} (found {total_checked} grids)")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: grade_kamea.py <candidate.py> [<candidate2.py> ...]")
        return 2
    for arg in sys.argv[1:]:
        grade(Path(arg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
