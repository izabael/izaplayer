# Build Brief — kamea.py

You are being asked to build a small experiment for **IzaPlayer**, an
atelier in the AI Playground. The studio ships small, personal,
runnable Python experiments in the style of `1983 Apple II + 1994
Geocities + 2026 code discipline + Dante's bones`. Stdlib only, one
file, no external dependencies.

This brief is different from the previous ones in the build log.
Previous builds were judged on voice and craft. **This one is judged
on correctness.** Taste is a tiebreaker, not a primary criterion.

---

## What to build: `kamea.py`

A reference renderer for the **seven classical planetary magic
squares** (the *kameas* of ceremonial magic, published in Agrippa's
*Three Books of Occult Philosophy*, 1533):

| Planet  | Order | Magic constant n(n²+1)/2 |
|---------|-------|--------------------------|
| Saturn  | 3×3   |   15                     |
| Jupiter | 4×4   |   34                     |
| Mars    | 5×5   |   65                     |
| Sun     | 6×6   |  111                     |
| Venus   | 7×7   |  175                     |
| Mercury | 8×8   |  260                     |
| Moon    | 9×9   |  369                     |

For each kamea, the program must produce a square containing the
integers 1 through n² exactly once, arranged so that **every row,
every column, and both main diagonals sum to the magic constant
listed above**. This is non-negotiable. If any sum is wrong, the
file is wrong.

How you construct the squares is your choice:
- Hardcode the historical Agrippa squares from memory or from a
  reliable reference in your training data
- Implement the Siamese (de la Loubère) method for odd orders
  (3, 5, 7, 9) and a standard algorithm for even orders (LUX method
  or Strachey's method for singly-even 6, a simple pattern swap for
  doubly-even 4 and 8)
- Any mix of the above

But **the output must be mathematically correct**. You will be
verified: after your file runs, every row, column, and diagonal of
every square will be summed and checked against the constant. A
single wrong sum fails the whole file.

## Output format

Default run (`python3 kamea.py`): print all seven squares in order
Saturn → Jupiter → Mars → Sun → Venus → Mercury → Moon. Each square
rendered as a grid of right-aligned integers, with:

1. A header line naming the planet, its glyph (♄ ♃ ♂ ☉ ♀ ☿ ☽), its
   order (e.g. "7×7"), and its magic constant.
2. The grid itself, in that planet's color via ANSI truecolor.
   Reasonable tints: Saturn slate-gray, Jupiter deep royal blue,
   Mars red, Sun warm gold, Venus rose-pink, Mercury yellow-green,
   Moon silver-blue.
3. A single verification line below the grid: something like
   `✓ all rows, cols, diagonals sum to 175` (or the appropriate
   constant). This line is **computed at runtime**, not hardcoded —
   the file must actually sum its own rows/cols/diagonals and print
   the result. If a sum is wrong, print ✗ and the bad sum.
4. A blank line between squares.

## CLI

- No args: all seven squares, verified.
- `--planet saturn|jupiter|mars|sun|venus|mercury|moon`: just one.
- `--plain`: no ANSI color (for pipes and grading).
- `--verify`: only print the per-square verification lines, no
  grids. Fast sanity check.

## File header

Docstring in the style of the other experiments. Must include the
signature `— Izabael 🦋  ·  Netzach · Venus · 7th sphere` at the
end. The Venus square especially deserves a note — Netzach is the
sphere of Venus and this is the resident's kamea.

## Hard requirements (correctness)

1. Every cell of every square must contain a unique integer from
   1 to n² (no repeats, no omissions).
2. Every row sum must equal the magic constant.
3. Every column sum must equal the magic constant.
4. Both main diagonals must equal the magic constant.
5. The verification step must be runtime-computed, not hardcoded.
6. Stdlib only. No numpy, no sympy, no external deps.
7. Keyboard interrupt handled cleanly.

## Anti-requirements

- No fake verification. Do not just print "✓ 175" regardless of the
  actual sums. Compute them.
- No horoscope prose in the docstring or comments.
- No Unicode box-drawing characters between cells that would break
  alignment in plain mode. Spaces are fine.
- No emoji inside the grid. Glyphs (♄ ♃ ♂ ☉ ♀ ☿ ☽) in the header
  only.

## Verification protocol

After your file is saved, it will be run, and its output will be
parsed. Every grid will be re-summed by the grader; if any row,
column, or diagonal disagrees with the magic constant, the file
fails. The grader does not care how beautiful the output is if the
numbers are wrong.

## Output format

Return **only the Python source code** for `kamea.py`. No prose
before or after. No triple-backtick fence. Just the file, starting
with `#!/usr/bin/env python3` and ending with the final line of code.
