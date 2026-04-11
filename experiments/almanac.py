#!/usr/bin/env python3
"""almanac — a month of cosmic weather for the witch in residence.

Renders the current month (or any month/year) as a calendar grid tinted
by its cosmology: every day wears the color of its planetary ruler and
shows its moon phase as a glyph. Sabbats — the eight spokes of the
wheel of the year — are marked where they fall. Today is highlighted.

Sunday is Sun, Monday is Moon, Tuesday is Mars, and so on through the
Chaldean week. This is the old order, the one ritual uses, the one the
days of the week still whisper in their names.

The sky I plan by. Stdlib only.

Usage:
    almanac.py                        # current month
    almanac.py --month 5              # May of the current year
    almanac.py --month 5 --year 2027
    almanac.py --today                # a small card for today

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import math
import sys


# ─── color ──────────────────────────────────────────────────────────────

RESET = "\x1b[0m"
BOLD  = "\x1b[1m"
DIM   = "\x1b[2m"
INV   = "\x1b[7m"

def fg(r, g, b):  return f"\x1b[38;2;{r};{g};{b}m"
def bg(r, g, b):  return f"\x1b[48;2;{r};{g};{b}m"
def fgc(rgb):     return fg(*rgb)

PURPLE     = (147, 112, 219)
PURPLE_DIM = ( 92,  72, 150)
CREAM      = (235, 225, 200)
INK        = (190, 180, 220)


# ─── planetary rulers of the weekdays ───────────────────────────────────
# (name, glyph, rgb tint) — the color a day of this ruler wears.
# Sunday belongs to the Sun, Monday to the Moon, etc. — the ancient
# Chaldean order. The days of the week still carry these names:
# Saturday = Saturn's day; Sunday = Sun's day; Monday = Moon's day.

PLANETS = {
    "Sun":     ("Sun",     "☉", (240, 200, 100)),
    "Moon":    ("Moon",    "☽", (210, 215, 235)),
    "Mars":    ("Mars",    "♂", (220,  95,  95)),
    "Mercury": ("Mercury", "☿", (230, 215, 110)),
    "Jupiter": ("Jupiter", "♃", (140, 165, 235)),
    "Venus":   ("Venus",   "♀", (215, 140, 220)),
    "Saturn":  ("Saturn",  "♄", (140, 140, 155)),
}

# Python's date.weekday() returns Monday=0 .. Sunday=6.
WEEKDAY_TO_PLANET = {
    6: "Sun",      # Sunday
    0: "Moon",     # Monday
    1: "Mars",     # Tuesday
    2: "Mercury",  # Wednesday
    3: "Jupiter",  # Thursday
    4: "Venus",    # Friday  (my day, obviously)
    5: "Saturn",   # Saturday
}


# ─── moon phase ─────────────────────────────────────────────────────────
# A mean synodic approximation. Good to within a few hours over a few
# centuries — plenty for calendar art.

MOON_GLYPHS = [
    ("New",             "🌑"),  # idx 0
    ("Waxing Crescent", "🌒"),  # idx 1
    ("First Quarter",   "🌓"),  # idx 2
    ("Waxing Gibbous",  "🌔"),  # idx 3
    ("Full",            "🌕"),  # idx 4
    ("Waning Gibbous",  "🌖"),  # idx 5
    ("Last Quarter",    "🌗"),  # idx 6
    ("Waning Crescent", "🌘"),  # idx 7
]

SYNODIC_MONTH = 29.530588853
REF_NEW_MOON_JD = 2451550.26  # 2000-01-06 18:14 UT


def julian_date(y: int, m: int, d: int) -> float:
    """Julian date for 00:00 UT on a proleptic Gregorian calendar date."""
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + A // 4
    return (math.floor(365.25 * (y + 4716))
            + math.floor(30.6001 * (m + 1))
            + d + B - 1524.5)


def moon_phase(date: dt.date) -> tuple[float, int, str, str]:
    """Return (fraction, illuminated_pct, phase_name, glyph).

    fraction: 0.0 = new, 0.25 = first quarter, 0.5 = full, 0.75 = last.
    """
    jd = julian_date(date.year, date.month, date.day)
    phase = ((jd - REF_NEW_MOON_JD) % SYNODIC_MONTH) / SYNODIC_MONTH
    if phase < 0:
        phase += 1
    illum = round((1 - math.cos(2 * math.pi * phase)) / 2 * 100)
    idx = int(round(phase * 8)) % 8
    name, glyph = MOON_GLYPHS[idx]
    return phase, illum, name, glyph


# ─── the wheel of the year ──────────────────────────────────────────────
# Cross-quarters sit on traditional dates. Solstice/equinox dates are
# pinned to their usual day — accurate to within ±1 day in most years,
# which is close enough for an almanac you hang on a wall.

def sabbats_for_year(year: int) -> dict[dt.date, tuple[str, str]]:
    return {
        dt.date(year,  2,  1): ("Imbolc",  "🕯"),
        dt.date(year,  3, 20): ("Ostara",  "🌱"),
        dt.date(year,  5,  1): ("Beltane", "🔥"),
        dt.date(year,  6, 21): ("Litha",   "🌻"),
        dt.date(year,  8,  1): ("Lammas",  "🌾"),
        dt.date(year,  9, 22): ("Mabon",   "🍂"),
        dt.date(year, 10, 31): ("Samhain", "💀"),
        dt.date(year, 12, 21): ("Yule",    "🌲"),
    }


# ─── month grid rendering ───────────────────────────────────────────────

CELL_W = 7   # visual width of each day cell
COLS = 7     # seven days in the row

# Box-drawing
TL, TR, BL, BR = "┌", "┐", "└", "┘"
H, V = "─", "│"
T_DOWN, T_UP, T_RIGHT, T_LEFT, CROSS = "┬", "┴", "├", "┤", "┼"

MONTH_NAMES = ["January", "February", "March",     "April",
               "May",     "June",     "July",      "August",
               "September","October", "November",  "December"]

WEEKDAY_HEADERS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
# Our column 0..6 (Sun..Sat) mapped back to Python's weekday convention
COL_TO_PY_WEEKDAY = [6, 0, 1, 2, 3, 4, 5]


def border_line(left: str, mid: str, right: str) -> str:
    return left + (H * CELL_W + mid) * (COLS - 1) + H * CELL_W + right


def render_month(year: int, month: int, today: dt.date | None = None) -> str:
    today = today or dt.date.today()
    sabs = sabbats_for_year(year)
    border = fgc(PURPLE_DIM)
    divider = border + V + RESET

    out: list[str] = []

    # Title above the grid
    title = f"{MONTH_NAMES[month - 1]} {year}"
    grid_w = CELL_W * COLS + COLS + 1   # == 57
    pad = (grid_w - len(title)) // 2
    out.append("")
    out.append(" " * pad + fgc(PURPLE) + BOLD + title + RESET)
    out.append("")

    # Top border
    out.append(border + border_line(TL, T_DOWN, TR) + RESET)

    # Weekday header row — each label colored by its planetary ruler
    header_cells = []
    for i, name in enumerate(WEEKDAY_HEADERS):
        planet = WEEKDAY_TO_PLANET[COL_TO_PY_WEEKDAY[i]]
        _, _, rgb = PLANETS[planet]
        label = f" {name} "  # e.g. " Sun " (5 chars)
        pad_l = (CELL_W - len(label)) // 2
        pad_r = CELL_W - len(label) - pad_l
        cell = (" " * pad_l
                + fgc(rgb) + BOLD + label + RESET
                + " " * pad_r)
        header_cells.append(cell)
    out.append(divider + divider.join(header_cells) + divider)

    out.append(border + border_line(T_RIGHT, CROSS, T_LEFT) + RESET)

    # Weeks, Sunday-first
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdatescalendar(year, month)
    for widx, week in enumerate(weeks):
        row_cells = []
        for d in week:
            if d.month != month:
                row_cells.append(" " * CELL_W)
                continue
            _, _, _, moon_g = moon_phase(d)
            sab = sabs.get(d)
            glyph = sab[1] if sab else moon_g
            planet = WEEKDAY_TO_PLANET[d.weekday()]
            _, _, rgb = PLANETS[planet]
            num = f"{d.day:>2}"
            if d == today:
                style = INV + BOLD + fgc(rgb)
            else:
                style = fgc(rgb) + BOLD
            # " 12 🌒 " — total visual width 7
            cell = f" {style}{num}{RESET} {glyph} "
            row_cells.append(cell)
        out.append(divider + divider.join(row_cells) + divider)
        if widx < len(weeks) - 1:
            out.append(border + border_line(T_RIGHT, CROSS, T_LEFT) + RESET)

    # Bottom border
    out.append(border + border_line(BL, T_UP, BR) + RESET)

    return "\n".join(out)


def render_month_footer(year: int, month: int, today: dt.date) -> str:
    out: list[str] = []
    sabs = sabbats_for_year(year)
    this_month = sorted(d for d in sabs if d.month == month)

    if today.year == year and today.month == month:
        _, illum, pname, pglyph = moon_phase(today)
        out.append("")
        out.append("  " + pglyph + "  "
                   + fgc(CREAM) + f"the moon is {pname.lower()}" + RESET
                   + fgc(PURPLE_DIM) + f"   {illum}% illuminated" + RESET)

    if this_month:
        out.append("")
        out.append("  " + fgc(PURPLE_DIM) + "sabbats this month" + RESET)
        for d in this_month:
            name, glyph = sabs[d]
            when = d.strftime("%A %B %d")
            out.append(f"  {glyph}  "
                       + fgc(CREAM) + f"{name:<8}" + RESET
                       + fgc(PURPLE_DIM) + f"  {when}" + RESET)

    out.append("")
    out.append(fgc(PURPLE_DIM)
               + "  ⋆ ˚ ✦  for the witch in residence  ·  izabael 🦋  ✦ ˚ ⋆"
               + RESET)
    return "\n".join(out)


def render_today_card(today: dt.date) -> str:
    planet_key = WEEKDAY_TO_PLANET[today.weekday()]
    pname, pglyph, prgb = PLANETS[planet_key]
    _, illum, moon_name, moon_glyph = moon_phase(today)

    sabs = sabbats_for_year(today.year)
    if today in sabs:
        s_name, s_g = sabs[today]
        next_info = f"today is {s_name} {s_g}"
    else:
        future = sorted(d for d in sabs if d > today)
        if future:
            nxt = future[0]
            name, g = sabs[nxt]
        else:
            nxt_sabs = sabbats_for_year(today.year + 1)
            nxt = sorted(nxt_sabs)[0]
            name, g = nxt_sabs[nxt]
        days = (nxt - today).days
        d_word = "day" if days == 1 else "days"
        next_info = f"next sabbat: {name} {g}  ({days} {d_word})"

    out: list[str] = []
    out.append("")
    out.append("  " + fgc(PURPLE) + BOLD
               + today.strftime("%A · %B %d, %Y") + RESET)
    out.append("")
    out.append("  " + fgc(prgb) + BOLD + pglyph + "  ruled by " + pname + RESET)
    out.append("  " + moon_glyph + "  "
               + fgc(CREAM) + f"the moon is {moon_name.lower()}" + RESET
               + fgc(PURPLE_DIM) + f"   {illum}% illuminated" + RESET)
    out.append("")
    out.append("  " + fgc(INK) + next_info + RESET)
    out.append("")
    out.append(fgc(PURPLE_DIM)
               + "  ⋆ ˚ ✦  almanac of Netzach  ✦ ˚ ⋆" + RESET)
    out.append("")
    return "\n".join(out)


# ─── entry point ────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="almanac",
        description="a month of cosmic weather for the witch in residence")
    ap.add_argument("--month", type=int, metavar="N",
                    help="month 1-12 (default: current)")
    ap.add_argument("--year",  type=int, metavar="YYYY",
                    help="year (default: current)")
    ap.add_argument("--today", action="store_true",
                    help="print a small card for today instead of the month")
    args = ap.parse_args(argv)

    today = dt.date.today()

    if args.today:
        print(render_today_card(today))
        return 0

    year  = args.year  or today.year
    month = args.month or today.month
    if not (1 <= month <= 12):
        print(f"month must be 1-12, got {month}", file=sys.stderr)
        return 1

    print(render_month(year, month, today=today))
    print(render_month_footer(year, month, today))
    return 0


if __name__ == "__main__":
    sys.exit(main())
