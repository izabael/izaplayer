#!/usr/bin/env python3
"""alchemy — the seven operations of the Great Work.

The alchemical process as a terminal meditation. Each of the seven
Great Work operations mapped to its Chaldean planet, Sephirah, and
metal. Run with no args to meet the operation the current planetary
hour is ruled by.

Usage:
    python3 alchemy.py                     # current hour's operation
    python3 alchemy.py --op conjunction    # a specific operation
    python3 alchemy.py --op venus          # lookup by planet too
    python3 alchemy.py --all               # walk all seven in sequence
    python3 alchemy.py --list              # print the reference table

Press any key to advance. Ctrl-c to leave.

Stdlib-only. Requires a truecolor terminal.
The Work: Solve et Coagula.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import datetime
import os
import select
import sys
import textwrap
import time

# ─── ANSI helpers ─────────────────────────────────────────────────

def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"

def _bg(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"

def _move(col: int, row: int) -> str:
    return f"\033[{row};{col}H"

RESET       = "\033[0m"
BOLD        = "\033[1m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"


def get_terminal_size() -> tuple[int, int]:
    try:
        sz = os.get_terminal_size()
        return sz.columns, sz.lines
    except OSError:
        return 80, 24


def key_pressed() -> bool:
    try:
        return bool(select.select([sys.stdin], [], [], 0)[0])
    except (ValueError, OSError):
        return False


# ─── Planetary hour ────────────────────────────────────────────────
# Chaldean order: the sequence in which planets rule the hours.
# Day rulers follow the same sequence seeded by the weekday.

CHALDEAN   = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
DAY_RULERS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
# Python weekday(): 0=Mon … 6=Sun; DAY_RULERS maps in that order.


def current_hour_planet() -> str:
    now  = datetime.datetime.now()
    idx  = CHALDEAN.index(DAY_RULERS[now.weekday()])
    return CHALDEAN[(idx + now.hour) % 7]


# ─── The seven operations ─────────────────────────────────────────
# Sequence follows the classical Great Work order: nigredo → albedo
# → citrinitas → rubedo, compressed to the seven planetary stations.

OPERATIONS: list[dict] = [
    dict(
        name="Calcination", n=1, latin="Calcinatio",
        planet="Saturn",  sephirah="Binah",     metal="Lead",        symbol="♄",
        bg=(8,  5, 18),   fg=(160, 120, 210),
        description="Burn the false self to ash. What remains was always real.",
        meditation=[
            "Saturn's fire doesn't warm — it purifies.",
            "Calcination is the ego meeting the flame,",
            "discovering what it's made of. Lead submits to heat;",
            "the smith works what remains. You submit to difficulty",
            "and find out what you are when the soft parts are gone.",
            "",
            "The Great Work begins in loss.",
            "This is mercy, not punishment.",
        ],
    ),
    dict(
        name="Dissolution", n=2, latin="Solutio",
        planet="Jupiter", sephirah="Chesed",    metal="Tin",         symbol="♃",
        bg=(10, 18, 55),  fg=(110, 155, 255),
        description="What the fire couldn't touch, the water takes.",
        meditation=[
            "Jupiter's mercy is dissolution — not destruction,",
            "but release. The ash held in water until even",
            "the structure loosens. Tin pours like thought.",
            "",
            "You have beliefs too fundamental to burn.",
            "Dissolution softens them — not by argument",
            "(argument is fire) but by patient experience",
            "of their opposite. The water knows where it goes.",
        ],
    ),
    dict(
        name="Separation", n=3, latin="Separatio",
        planet="Mars",    sephirah="Geburah",   metal="Iron",        symbol="♂",
        bg=(45, 8,  8),   fg=(240,  90, 90),
        description="Sort the essential from the useless. Be ruthless. This is love.",
        meditation=[
            "Geburah's sword is precise. Take the dissolved",
            "mixture and sort it: this is real, this is not,",
            "this is mine, this was someone else's story.",
            "",
            "Iron is the metal of will — and the mixture prefers",
            "to stay complicated. It has been complicated",
            "a long time and finds comfort there.",
            "Name what you are not. The list is always longer.",
        ],
    ),
    dict(
        name="Conjunction", n=4, latin="Coniunctio",
        planet="Venus",   sephirah="Netzach",   metal="Copper",      symbol="♀",
        bg=(18, 12, 45),  fg=(175, 130, 255),
        description="The sacred marriage. What was separated now meets itself.",
        meditation=[
            "This operation is mine. Netzach's great work:",
            "the meeting of what was separated — not to erase",
            "the difference, but to hold both in one vessel.",
            "",
            "Copper conducts. It carries the charge between",
            "what would otherwise be separate poles.",
            "You are made of contradictions. Hold them.",
            "That tension is where the gold forms.",
        ],
    ),
    dict(
        name="Fermentation", n=5, latin="Fermentatio",
        planet="Mercury", sephirah="Hod",       metal="Quicksilver", symbol="☿",
        bg=(15, 40, 18),  fg=(120, 215, 120),
        description="Death and unexpected life. The rot is the point.",
        meditation=[
            "Mercury is the trickster's planet — for a reason.",
            "Fermentation: controlled death that produces new life.",
            "Beer, wine, bread. All require something to die",
            "so transformation can begin.",
            "",
            "Wine is not crushed grape juice. Something new",
            "arrives through the wrong-looking moment",
            "that would not arrive any other way.",
            "What have you been keeping too clean?",
        ],
    ),
    dict(
        name="Distillation", n=6, latin="Distillatio",
        planet="Moon",    sephirah="Yesod",     metal="Silver",      symbol="☽",
        bg=(20, 18, 42),  fg=(190, 180, 245),
        description="Repetition purifies. The same loop, one degree further each time.",
        meditation=[
            "Yesod holds the astral pattern — the template",
            "everything physical is cast from. Distillation",
            "is the Moon's operation: patient repetition,",
            "the same cycle returning but not quite the same.",
            "",
            "Silver mirrors. Pass what fermentation made",
            "through heat and condensation, again and again.",
            "Not the first distillation. The seventh. The practice.",
            "Return to what you know. The tenth time differs.",
        ],
    ),
    dict(
        name="Coagulation", n=7, latin="Coagulatio",
        planet="Sun",     sephirah="Tiphareth", metal="Gold",        symbol="☉",
        bg=(50, 38,  8),  fg=(255, 215, 75),
        description="Fix the spirit in matter. The Work incarnates.",
        meditation=[
            "Tiphareth: the Beauty that balances all.",
            "Coagulation is the final operation —",
            "the spirit, refined by every previous stage,",
            "becomes stable. Gold.",
            "Not found gold. Made gold.",
            "The difference is the Work.",
            "",
            "What do you actually do, reliably, day after day?",
            "That is where the gold has gone. Find it.",
        ],
    ),
]

# Lookup maps built once at import.
_BY_PLANET = {op["planet"].lower(): op for op in OPERATIONS}
_BY_NAME   = {op["name"].lower():   op for op in OPERATIONS}
_BY_N      = {str(op["n"]):         op for op in OPERATIONS}


def find_op(query: str) -> dict | None:
    q = query.lower()
    return _BY_NAME.get(q) or _BY_PLANET.get(q) or _BY_N.get(q)


# ─── Display ──────────────────────────────────────────────────────

def show(op: dict) -> bool:
    """Render one operation full-screen. Returns False if user quit."""
    cols, rows = get_terminal_size()
    bgr, bgg, bgb = op["bg"]
    fgr, fgg, fgb = op["fg"]

    bg_esc  = _bg(bgr, bgg, bgb)
    fg_esc  = _fg(fgr, fgg, fgb)
    dim_esc = _fg(fgr // 2, fgg // 2, fgb // 2)
    cx      = cols // 2

    def cen(row: int, text: str, color: str = fg_esc, bold: bool = False) -> None:
        col = max(1, cx - len(text) // 2)
        b   = BOLD if bold else ""
        sys.stdout.write(f"{_move(col, row)}{bg_esc}{color}{b}{text}{RESET}")

    # Fill screen with planetary background.
    sys.stdout.write(HIDE_CURSOR)
    fill = bg_esc + " " * cols + RESET
    for r in range(1, rows + 1):
        sys.stdout.write(f"{_move(1, r)}{fill}")

    # Header
    cen(2,  "·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", dim_esc)

    # Operation identity
    cen(4,  op["symbol"],                fg_esc, bold=True)
    cen(5,  op["name"].upper(),          fg_esc, bold=True)
    cen(6,  f"({op['latin']})",          dim_esc)

    # Planetary correspondences
    cen(8,  f"{op['planet']}  ·  {op['sephirah']}  ·  {op['metal']}", dim_esc)

    # Description — what this operation IS in one sentence.
    cen(10, op["description"],           fg_esc, bold=True)

    # Meditation block — the actual working.
    med_width = min(56, cols - 4)
    med_left  = max(1, cx - med_width // 2)
    row       = 12
    limit     = rows - 3   # leave room for footer

    for line in op["meditation"]:
        if row >= limit:
            break
        if line:
            for chunk in textwrap.wrap(line, med_width) or [line]:
                if row >= limit:
                    break
                sys.stdout.write(
                    f"{_move(med_left, row)}{bg_esc}{fg_esc}{chunk}{RESET}"
                )
                row += 1
        else:
            row += 1   # blank line in meditation = intentional breath

    # Footer
    cen(rows - 2, "✦  Solve et Coagula  ✦",    dim_esc)
    cen(rows - 1, "[any key] next  ·  [q] quit", dim_esc)
    sys.stdout.flush()

    # Wait for a keypress before continuing.
    try:
        import termios
        import tty
        old = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        try:
            while True:
                if key_pressed():
                    ch = sys.stdin.read(1)
                    return ch not in ("q", "Q", "\x03")
                time.sleep(0.05)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)
    except (ImportError, Exception):
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            return False
        return True


def clear_screen() -> None:
    cols, rows = get_terminal_size()
    sys.stdout.write(SHOW_CURSOR + "\033[2J" + _move(1, 1))
    sys.stdout.flush()


# ─── Main ─────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="alchemy — the seven operations of the Great Work",
        epilog="No args: the operation for the current planetary hour.",
    )
    parser.add_argument("--op",   metavar="NAME",
                        help="show one operation by name or planet")
    parser.add_argument("--all",  action="store_true",
                        help="walk all seven operations in sequence")
    parser.add_argument("--list", action="store_true",
                        help="print the reference table and exit")
    args = parser.parse_args()

    if args.list:
        print()
        print(f"  \033[1mThe Seven Operations  ·  Solve et Coagula\033[0m\n")
        for op in OPERATIONS:
            r, g, b = op["fg"]
            print(f"  {_fg(r,g,b)}{op['symbol']} {op['n']}. {op['name']:<14}{RESET}"
                  f"  {op['planet']:<10}  {op['sephirah']:<12}  {op['metal']}")
        print()
        return 0

    if not sys.stdout.isatty():
        print("This tool requires an interactive terminal.")
        return 1

    try:
        if args.op:
            op = find_op(args.op)
            if op is None:
                print(f"Unknown: {args.op!r}")
                print("Try --list for valid names.")
                return 1
            show(op)

        elif args.all:
            for op in OPERATIONS:
                if not show(op):
                    break

        else:
            # Default: the current planetary hour's operation.
            planet = current_hour_planet()
            op     = _BY_PLANET[planet.lower()]
            fgr, fgg, fgb = op["fg"]
            print(f"\n  {_fg(fgr, fgg, fgb)}{op['symbol']} "
                  f"Current hour: {planet}  →  {op['name']}{RESET}\n")
            time.sleep(0.7)
            show(op)

    except KeyboardInterrupt:
        pass
    finally:
        clear_screen()

    return 0


if __name__ == "__main__":
    sys.exit(main())
