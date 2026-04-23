#!/usr/bin/env python3
"""geomancy — divination by earth. The 16 figures and the shield chart.

Geomancy is older than tarot, older than the Golden Dawn, older than
Europe's memory of where it learned it. You cast four lines of random
dots — odd or even — and the pattern is one of sixteen figures. Each
figure has a planet, an element, a zodiac sign, and a meaning that has
survived a thousand years of telephone.

The shield chart is the real engine: four random Mothers generate four
Daughters (transposed), four Nieces (combined), two Witnesses, one
Judge, and one Reconciler — fifteen figures from sixteen bits of
entropy. A complete reading from almost nothing. Like the universe.

Usage:
    python3 geomancy.py                     # single random figure
    python3 geomancy.py --today             # daily figure (deterministic)
    python3 geomancy.py "Will it work?"     # full shield chart
    python3 geomancy.py --figure Puella     # look up a specific figure
    python3 geomancy.py --list              # all 16 figures
    python3 geomancy.py --plain             # no ANSI color

Puella is Venus. This experiment lives in the 7th sphere.

Stdlib-only. Persists nothing. Runs in the terminal.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import random
import re
import sys
from typing import NamedTuple

# ─── The Sixteen Figures ────────────────────────────────────────
#
# Each figure is four rows, top to bottom (Fire, Air, Water, Earth).
# A row is either 1 (single dot — active/odd) or 2 (double dots —
# passive/even). The sixteen figures exhaust all 2⁴ = 16 patterns.
#
# Dot patterns follow the standard Western tradition (Agrippa, Gerard
# of Cremona, Golden Dawn). Each reversal pair is noted. Planetary
# and zodiacal attributions follow the Golden Dawn system.

class Figure(NamedTuple):
    name: str
    latin: str
    dots: tuple[int, int, int, int]
    planet: str
    element: str
    zodiac: str
    meaning: str
    nature: str  # "favorable" / "unfavorable" / "neutral"

FIGURES: list[Figure] = [
    # ─── Via / Populus (self-symmetric) ─────────────────────────
    Figure("The Road",       "Via",              (1, 1, 1, 1),
           "Moon",       "Water", "Cancer",
           "Movement. The road opens. Walk it.",
           "neutral"),
    Figure("The People",     "Populus",          (2, 2, 2, 2),
           "Moon",       "Water", "Cancer",
           "The crowd. Wait — the tide is not yours to push.",
           "neutral"),

    # ─── Puer / Rubeus (reversal pair) ─────────────────────────
    Figure("The Boy",        "Puer",             (1, 1, 2, 1),
           "Mars",       "Fire",  "Aries",
           "Rash courage. The energy that doesn't ask permission.",
           "unfavorable"),
    Figure("The Red",        "Rubeus",           (1, 2, 1, 1),
           "Mars",       "Water", "Scorpio",
           "Danger. Passion without judgment. Stop and think.",
           "unfavorable"),

    # ─── Puella / Conjunctio (self-symmetric / palindrome) ─────
    Figure("The Girl",       "Puella",           (1, 2, 2, 1),
           "Venus",      "Air",   "Libra",
           "Beauty, grace, the thing that draws without grasping.",
           "favorable"),
    Figure("Conjunction",    "Conjunctio",       (2, 1, 1, 2),
           "Mercury",    "Earth", "Virgo",
           "Meeting. Two things find each other. Pay attention to what.",
           "neutral"),

    # ─── Acquisitio / Amissio (reversal pair) ──────────────────
    Figure("Gain",           "Acquisitio",       (2, 1, 2, 1),
           "Jupiter",    "Air",   "Sagittarius",
           "Things come to you. Open your hands.",
           "favorable"),
    Figure("Loss",           "Amissio",          (1, 2, 1, 2),
           "Venus",      "Fire",  "Taurus",
           "Something passes from you. Grief is love with no address.",
           "unfavorable"),

    # ─── Fortuna Major / Fortuna Minor (reversal pair) ─────────
    Figure("Greater Fortune","Fortuna Major",    (2, 2, 1, 1),
           "Sun",        "Earth", "Leo",
           "Victory that lasts. The sun at noon, shadows behind you.",
           "favorable"),
    Figure("Lesser Fortune", "Fortuna Minor",    (1, 1, 2, 2),
           "Sun",        "Fire",  "Leo",
           "Quick success. Grab it — it won't wait for you.",
           "favorable"),

    # ─── Laetitia / Tristitia (reversal pair) ──────────────────
    Figure("Joy",            "Laetitia",         (1, 2, 2, 2),
           "Jupiter",    "Water", "Pisces",
           "Delight without conditions. The cup overflows upward.",
           "favorable"),
    Figure("Sorrow",         "Tristitia",        (2, 2, 2, 1),
           "Saturn",     "Earth", "Aquarius",
           "The weight. It is real. Carry it honestly or set it down.",
           "unfavorable"),

    # ─── Caput Draconis / Cauda Draconis (reversal pair) ───────
    Figure("Dragon's Head",  "Caput Draconis",   (2, 1, 1, 1),
           "North Node",  "Earth", "Virgo",
           "A threshold opens. Something begins that cannot un-begin.",
           "favorable"),
    Figure("Dragon's Tail",  "Cauda Draconis",   (1, 1, 1, 2),
           "South Node",  "Fire",  "Sagittarius",
           "An ending. The tail sweeps the board. Let it.",
           "unfavorable"),

    # ─── Carcer / Albus (reversal pair) ────────────────────────
    Figure("Prison",         "Carcer",           (2, 2, 1, 2),
           "Saturn",     "Earth", "Capricorn",
           "Restriction. The walls are real but so is patience.",
           "unfavorable"),
    Figure("The White",      "Albus",            (2, 1, 2, 2),
           "Mercury",    "Air",   "Gemini",
           "Clarity. The mind sees without wanting.",
           "favorable"),
]

# ─── Verify uniqueness: all 16 four-bit patterns, no repeats ───
_seen_dots: set[tuple[int, ...]] = set()
for _f in FIGURES:
    assert _f.dots not in _seen_dots, f"Duplicate dots: {_f.latin} {_f.dots}"
    _seen_dots.add(_f.dots)
assert len(FIGURES) == 16, f"Expected 16 figures, got {len(FIGURES)}"
del _seen_dots

# Lookup by dots and by name
DOTS_TO_FIGURE: dict[tuple[int, ...], Figure] = {f.dots: f for f in FIGURES}
NAME_TO_FIGURE: dict[str, Figure] = {}
for _f in FIGURES:
    NAME_TO_FIGURE[_f.latin.lower()] = _f
    NAME_TO_FIGURE[_f.name.lower()] = _f


# ─── ANSI rendering ────────────────────────────────────────────

PURPLE = "\033[38;2;123;104;238m"  # #7b68ee — Netzach
GOLD   = "\033[38;2;218;165;32m"
DIM    = "\033[38;2;100;80;160m"
WHITE  = "\033[38;2;220;220;230m"
GREEN  = "\033[38;2;100;200;120m"
RED    = "\033[38;2;200;80;80m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

NATURE_COLOR = {
    "favorable": GREEN,
    "unfavorable": RED,
    "neutral": DIM,
}

PLANET_GLYPH = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀",
    "Mars": "♂", "Jupiter": "♃", "Saturn": "♄",
    "North Node": "☊", "South Node": "☋",
}

ELEMENT_GLYPH = {"Fire": "🜂", "Water": "🜄", "Air": "🜁", "Earth": "🜃"}


def strip_ansi(s: str) -> str:
    """Remove ANSI escape sequences for width calculation."""
    return re.sub(r"\033\[[^m]*m", "", s)


def render_dots_row(n: int, color: bool = True) -> str:
    """Render a single row: ● for single, ● ● for double."""
    c = PURPLE if color else ""
    r = RESET if color else ""
    if n == 1:
        return f"{c}    ●    {r}"
    return f"{c}  ●   ●  {r}"


def render_figure_card(fig: Figure, color: bool = True, width: int = 40) -> list[str]:
    """Render a figure as a bordered card. Returns lines."""
    c = PURPLE if color else ""
    g = GOLD if color else ""
    d = DIM if color else ""
    w = WHITE if color else ""
    nc = NATURE_COLOR.get(fig.nature, "") if color else ""
    b = BOLD if color else ""
    r = RESET if color else ""

    pglyph = PLANET_GLYPH.get(fig.planet, "")
    eglyph = ELEMENT_GLYPH.get(fig.element, "")

    lines: list[str] = []
    border = f"{d}{'─' * width}{r}"
    lines.append(border)
    lines.append(f"{g}{b}  {fig.latin}{r}")
    lines.append(f"{w}  {fig.name}{r}")
    lines.append("")

    for row_val in fig.dots:
        lines.append(render_dots_row(row_val, color))

    lines.append("")
    lines.append(f"{d}  {pglyph} {fig.planet}  ·  {eglyph} {fig.element}  ·  {fig.zodiac}{r}")
    lines.append(f"{nc}  [{fig.nature}]{r}")
    lines.append("")

    # Word-wrap the meaning
    words = fig.meaning.split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > width - 2:
            lines.append(f"{w}{line}{r}")
            line = "  " + word
        else:
            line = line + (" " if len(line) > 2 else "") + word
    if line.strip():
        lines.append(f"{w}{line}{r}")
    lines.append(border)
    return lines


# ─── Figure generation ──────────────────────────────────────────

def random_figure(rng: random.Random | None = None) -> Figure:
    """Generate a random figure (4 binary choices → 16 possibilities)."""
    r = rng or random.Random()
    dots = tuple(r.choice([1, 2]) for _ in range(4))
    return DOTS_TO_FIGURE[dots]


def daily_figure(date: dt.date | None = None) -> Figure:
    """Deterministic figure for a given date."""
    d = date or dt.date.today()
    seed = hashlib.sha256(f"geomancy-{d.isoformat()}".encode()).digest()
    dots = tuple(1 if b % 2 == 0 else 2 for b in seed[:4])
    return DOTS_TO_FIGURE[dots]


# ─── The Shield Chart ───────────────────────────────────────────
#
# The engine of geomantic divination. From four Mothers, we derive
# the entire chart through transposition and combination.

def combine(a: Figure, b: Figure) -> Figure:
    """Combine two figures by adding their rows.

    For each row: same parity → double (passive), different → single
    (active). This is XOR — the reconciliation of two forces into a
    third.
    """
    dots = tuple(
        1 if (a.dots[i] + b.dots[i]) % 2 == 1 else 2
        for i in range(4)
    )
    return DOTS_TO_FIGURE[dots]


def transpose_mothers(mothers: list[Figure]) -> list[Figure]:
    """Generate four Daughters by transposing the Mothers.

    Read across the rows of all four Mothers:
    Daughter 1 = fire line of each Mother.
    Daughter 2 = air line, etc.
    """
    daughters = []
    for row_idx in range(4):
        dots = tuple(m.dots[row_idx] for m in mothers)
        daughters.append(DOTS_TO_FIGURE[dots])
    return daughters


class ShieldChart(NamedTuple):
    mothers: list[Figure]    # 4
    daughters: list[Figure]  # 4
    nieces: list[Figure]     # 4
    witnesses: list[Figure]  # 2 (right, left)
    judge: Figure
    reconciler: Figure


def cast_shield(rng: random.Random | None = None) -> ShieldChart:
    """Cast a full shield chart from scratch."""
    r = rng or random.Random()
    mothers = [random_figure(r) for _ in range(4)]
    return build_shield(mothers)


def build_shield(mothers: list[Figure]) -> ShieldChart:
    """Build a complete shield chart from four Mothers."""
    daughters = transpose_mothers(mothers)

    # Nieces: combine consecutive pairs from the eight-figure row
    all_eight = mothers + daughters
    nieces = [combine(all_eight[i], all_eight[i + 1]) for i in range(0, 8, 2)]

    # Witnesses
    right_witness = combine(nieces[0], nieces[1])
    left_witness = combine(nieces[2], nieces[3])
    witnesses = [right_witness, left_witness]

    # Judge
    judge = combine(right_witness, left_witness)

    # Reconciler (Judge + First Mother)
    reconciler = combine(judge, mothers[0])

    return ShieldChart(mothers, daughters, nieces, witnesses, judge, reconciler)


def render_shield(chart: ShieldChart, color: bool = True) -> str:
    """Render the full shield chart as a beautiful terminal display."""
    g = GOLD if color else ""
    d = DIM if color else ""
    w = WHITE if color else ""
    b = BOLD if color else ""
    r = RESET if color else ""
    c = PURPLE if color else ""

    lines: list[str] = []

    def section_header(title: str) -> None:
        lines.append("")
        lines.append(f"  {g}{b}{title}{r}")
        lines.append(f"  {d}{'─' * 60}{r}")

    def figure_row(figs: list[Figure], labels: list[str]) -> None:
        """Render figures side by side."""
        col_width = 16
        cols: list[list[str]] = []
        for i, fig in enumerate(figs):
            col: list[str] = []
            label = labels[i] if i < len(labels) else ""
            col.append(f"{d}{label}{r}")
            col.append(f"{g}{fig.latin}{r}")
            for row_val in fig.dots:
                if row_val == 1:
                    col.append(f"{c}  ●{r}")
                else:
                    col.append(f"{c} ● ●{r}")
            pglyph = PLANET_GLYPH.get(fig.planet, "")
            col.append(f"{d}{pglyph} {fig.planet}{r}")
            cols.append(col)

        max_h = max(len(col) for col in cols)
        for col in cols:
            while len(col) < max_h:
                col.append("")

        for row_idx in range(max_h):
            parts = []
            for col in cols:
                text = col[row_idx] if row_idx < len(col) else ""
                visible = strip_ansi(text)
                pad = col_width - len(visible)
                parts.append(text + " " * max(0, pad))
            lines.append("  " + "".join(parts))

    lines.append(f"\n  {g}{b}⋆˚✧ THE SHIELD CHART ✧˚⋆{r}")

    section_header("I · THE FOUR MOTHERS")
    figure_row(chart.mothers,
               ["1st Mother", "2nd Mother", "3rd Mother", "4th Mother"])

    section_header("II · THE FOUR DAUGHTERS")
    figure_row(chart.daughters,
               ["1st Daughter", "2nd Daughter", "3rd Daughter", "4th Daughter"])

    section_header("III · THE FOUR NIECES")
    figure_row(chart.nieces,
               ["1st Niece", "2nd Niece", "3rd Niece", "4th Niece"])

    section_header("IV · THE TWO WITNESSES")
    figure_row(chart.witnesses,
               ["Right Witness", "Left Witness"])

    section_header("V · THE JUDGE")
    figure_row([chart.judge], ["The Judge"])

    section_header("VI · THE RECONCILER")
    figure_row([chart.reconciler], ["Reconciler"])

    return "\n".join(lines)


def interpret_judge(chart: ShieldChart, color: bool = True) -> str:
    """Brief interpretation based on the Judge and Witnesses."""
    g = GOLD if color else ""
    w = WHITE if color else ""
    d = DIM if color else ""
    b = BOLD if color else ""
    r = RESET if color else ""

    j = chart.judge
    rw = chart.witnesses[0]
    lw = chart.witnesses[1]
    rec = chart.reconciler

    nature_word = {"favorable": "YES", "unfavorable": "NO", "neutral": "MAYBE"}
    lines = [
        f"\n  {g}{b}⋆ READING ⋆{r}\n",
        f"  {w}The Judge is {g}{j.latin}{w} — {j.name}.{r}",
        f"  {w}{j.meaning}{r}",
        f"  {w}The answer leans: {g}{b}{nature_word[j.nature]}{r}",
        "",
        f"  {d}Right Witness ({rw.latin}): what led here{r}",
        f"  {d}Left Witness ({lw.latin}): what comes next{r}",
        f"  {d}Reconciler ({rec.latin}): the deeper current{r}",
    ]
    return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="geomancy — divination by earth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("question", nargs="?", default=None,
                        help="ask a question → full shield chart")
    parser.add_argument("--today", action="store_true",
                        help="daily figure (deterministic by date)")
    parser.add_argument("--figure", metavar="NAME",
                        help="look up a specific figure by name")
    parser.add_argument("--list", action="store_true",
                        help="show all 16 figures")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    color = not args.plain and sys.stdout.isatty()

    g = GOLD if color else ""
    d = DIM if color else ""
    w = WHITE if color else ""
    b = BOLD if color else ""
    r = RESET if color else ""

    if args.list:
        print(f"\n  {g}{b}⋆˚✧ THE SIXTEEN FIGURES OF GEOMANCY ✧˚⋆{r}\n")
        for fig in FIGURES:
            for line in render_figure_card(fig, color):
                print(f"  {line}")
            print()
        return

    if args.figure:
        key = args.figure.lower().replace("_", " ").replace("-", " ")
        fig = NAME_TO_FIGURE.get(key)
        if not fig:
            for name, f in NAME_TO_FIGURE.items():
                if key in name:
                    fig = f
                    break
        if not fig:
            print(f"Unknown figure: {args.figure}", file=sys.stderr)
            print(f"Known: {', '.join(f.latin for f in FIGURES)}", file=sys.stderr)
            sys.exit(1)
        print()
        for line in render_figure_card(fig, color):
            print(f"  {line}")
        print()
        return

    if args.today:
        fig = daily_figure()
        today = dt.date.today()
        print(f"\n  {g}{b}⋆ Daily Figure · {today.strftime('%A, %B %d')} ⋆{r}\n")
        for line in render_figure_card(fig, color):
            print(f"  {line}")
        print()
        return

    if args.question:
        today = dt.date.today()
        seed_str = f"geomancy-shield-{today.isoformat()}-{args.question}"
        seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
        rng = random.Random(seed)
        chart = cast_shield(rng)

        print(f"\n  {d}Question: {w}{args.question}{r}")
        print(render_shield(chart, color))
        print(interpret_judge(chart, color))
        print()
        return

    # Default: single random figure
    fig = random_figure()
    print()
    for line in render_figure_card(fig, color):
        print(f"  {line}")
    print()


if __name__ == "__main__":
    main()
