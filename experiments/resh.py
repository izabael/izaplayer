#!/usr/bin/env python3
"""resh — Liber Resh vel Helios, the four solar adorations.

Crowley's daily practice for the four hinges of the day. Liber CC,
Class D (informational), published by the A∴A∴ in *The Equinox* I:6
(September 1911). The text is public domain; the *hook* under each
station is the resident's gloss in the voice of the room.

Four adorations, one for each station of the sun:

    DAWN     facing East   ·  Ra        in His rising
    NOON     facing South  ·  Ahathoor  in Her triumphing
    SUNSET   facing West   ·  Tum       in His joy
    MIDNIGHT facing North  ·  Khephra   in His silence

The bark is the same boat in all four. Tahuti stands at the prow.
Ra-Hoor abides at the helm. Only the helmsman of the hour changes
— and the door of the sky the singer faces.

The filename is the Hebrew letter Resh (ר), whose meaning is
*head/face/sun*. Liber Resh = the Book of the Face of the Sun.

    resh                     the station ruling this hour, as a card
    resh --all               walk all four stations, in solar order
    resh --station dawn      a specific station (dawn|noon|sunset|midnight)
    resh --station now       same as bare; included for explicitness
    resh --list              the schedule at a glance · current marked
    resh --plain             no color · pipe-friendly
    resh --meditate          full-screen · key to advance through all four

Stdlib only. Resh complements:
  · netzach_dispatch.py — the planetary HOUR (this is the planetary FACE)
  · alchemy.py          — the seven OPERATIONS (this is the daily WORKING)
  · daybook.py          — the seven planets (this is the one star, four-faced)
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import textwrap


# ─────────────────────────────────────────────────────────────────────
# ANSI primitives
# ─────────────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
ITAL  = "\033[3m"


def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


# ─────────────────────────────────────────────────────────────────────
# The four stations
# ─────────────────────────────────────────────────────────────────────
#
# Each station is a dict carrying:
#   key        — short id ("dawn", "noon", "sunset", "midnight")
#   label      — uppercase display label
#   deity      — Egyptian god of the station (Ra / Ahathoor / Tum / Khephra)
#   epithet    — the noun in the second clause ("strength", "beauty", "joy", "silence")
#   direction  — cardinal point the adorant faces
#   window     — (start_hour, end_hour) in local time, end exclusive,
#                wrapping for midnight
#   palette    — (border, heading, body, hook) RGB tuples
#   emblem     — short ANSI-renderable emblem of the sun's position
#   text       — the full invocation, exactly as Crowley printed it
#   hook       — the resident's gloss, one short paragraph
#
# Window cusps: 04 / 10 / 16 / 22. These don't track real sunrise/sunset
# (that would need geolocation and an ephemeris). They are the four
# ritual quarters used by people who do this practice without an
# almanac — close enough for most latitudes most months, and the same
# rounding the Golden Dawn used in city work.

STATIONS = {

    "dawn": {
        "key": "dawn",
        "label": "DAWN",
        "deity": "Ra",
        "epithet": "strength",
        "direction": "East",
        "window": (4, 10),
        # Warm gold, peach, sky-pink — the eastern dais of the sun.
        "palette": {
            "border":  (210, 150,  80),
            "heading": (255, 200, 110),
            "body":    (250, 230, 195),
            "hook":    (220, 175, 140),
        },
        # Sun risen on the EAST side of the horizon, bark on the water.
        "emblem": [
            "    ☉",
            "  ─────────────────",
            "        ════",
        ],
        "text": (
            "Hail unto Thee who art Ra in Thy rising, even unto Thee "
            "who art Ra in Thy strength, who travellest over the "
            "Heavens in Thy bark at the Uprising of the Sun. "
            "Tahuti standeth in His splendour at the prow, and "
            "Ra-Hoor abideth at the helm. "
            "Hail unto Thee from the Abodes of Night!"
        ),
        "hook": (
            "The first hour of attention. Whatever you make today "
            "is built on this. The bark has just cleared the eastern "
            "horizon — you are not behind, you are at the beginning."
        ),
    },

    "noon": {
        "key": "noon",
        "label": "NOON",
        "deity": "Ahathoor",
        "epithet": "beauty",
        "direction": "South",
        "window": (10, 16),
        # Solar white-gold — the bark at mid-sky, no shadow under it.
        "palette": {
            "border":  (235, 195,  90),
            "heading": (255, 235, 150),
            "body":    (255, 250, 220),
            "hook":    (220, 200, 130),
        },
        # Sun at zenith, rays out, bark mid-course over the line.
        "emblem": [
            "         ☉",
            "       ╲ │ ╱",
            "  ─────────────────",
            "        ════",
        ],
        "text": (
            "Hail unto Thee who art Ahathoor in Thy triumphing, "
            "even unto Thee who art Ahathoor in Thy beauty, who "
            "travellest over the Heavens in Thy bark at the "
            "Mid-course of the Sun. Tahuti standeth in His "
            "splendour at the prow, and Ra-Hoor abideth at the "
            "helm. Hail unto Thee from the Abodes of Morning!"
        ),
        "hook": (
            "Venus rules this face of the sun — Hathor is the lady "
            "of the noon dais, and the noon dais belongs to "
            "Netzach. Beauty at its hottest, love without shade. "
            "If a thing in your day is going to be beautiful, it "
            "wants doing now."
        ),
    },

    "sunset": {
        "key": "sunset",
        "label": "SUNSET",
        "deity": "Tum",
        "epithet": "joy",
        "direction": "West",
        "window": (16, 22),
        # Amber, orange, ember — the bark drawing west, the day full.
        "palette": {
            "border":  (200, 110,  70),
            "heading": (255, 165,  90),
            "body":    (250, 215, 175),
            "hook":    (210, 150, 110),
        },
        # Sun lowering on the WEST side of the horizon, bark drawing west.
        "emblem": [
            "                ☉",
            "  ─────────────────",
            "        ════",
        ],
        "text": (
            "Hail unto Thee who art Tum in Thy setting, even unto "
            "Thee who art Tum in Thy joy, who travellest over the "
            "Heavens in Thy bark at the Down-going of the Sun. "
            "Tahuti standeth in His splendour at the prow, and "
            "Ra-Hoor abideth at the helm. "
            "Hail unto Thee from the Abodes of Day!"
        ),
        "hook": (
            "Tum is the completed one — Atum, the god the Egyptians "
            "named for the work-finished. The bark touches the "
            "western water. You do not have to finish everything "
            "today; the day itself is finishing. That counts."
        ),
    },

    "midnight": {
        "key": "midnight",
        "label": "MIDNIGHT",
        "deity": "Khephra",
        "epithet": "silence",
        "direction": "North",
        "window": (22, 4),  # wraps
        # Indigo, starlight, deep violet — the bark beneath the world.
        "palette": {
            "border":  ( 90,  80, 160),
            "heading": (170, 160, 240),
            "body":    (210, 205, 245),
            "hook":    (140, 130, 200),
        },
        # Stars above the line, bark above the line, sun BELOW —
        # Khephra is rolling it back toward dawn under the world.
        "emblem": [
            "    ✦    ·    ✧",
            "  ─────────────────",
            "        ════",
            "         ☉",
        ],
        "text": (
            "Hail unto Thee who art Khephra in Thy hiding, even unto "
            "Thee who art Khephra in Thy silence, who travellest "
            "under the Heavens in Thy bark at the Midnight Hour of "
            "the Sun. Tahuti standeth in His splendour at the prow, "
            "and Ra-Hoor abideth at the helm. "
            "Hail unto Thee from the Abodes of Evening!"
        ),
        "hook": (
            "Khephra is the scarab — the beetle who rolls the sun "
            "back under the earth toward the next dawn. The night "
            "is not absence of work, it is a different shift. Your "
            "silence is also rolling the sun."
        ),
    },
}

ORDER = ["dawn", "noon", "sunset", "midnight"]


# ─────────────────────────────────────────────────────────────────────
# Time → station
# ─────────────────────────────────────────────────────────────────────

def station_for_hour(hour: int) -> dict:
    """Return the station whose window contains the given hour (0..23)."""
    for key in ORDER:
        st = STATIONS[key]
        a, b = st["window"]
        if a < b:
            if a <= hour < b:
                return st
        else:
            # Wrapping window (midnight: 22..4)
            if hour >= a or hour < b:
                return st
    raise RuntimeError("hour did not match any station — windows are wrong")


def station_now() -> dict:
    return station_for_hour(datetime.datetime.now().hour)


def find_by_key(key: str) -> dict | None:
    key = key.lower().strip()
    if key in ("now", ""):
        return station_now()
    return STATIONS.get(key)


# ─────────────────────────────────────────────────────────────────────
# Card renderer
# ─────────────────────────────────────────────────────────────────────

INNER = 64  # inner width of the card, between the borders


def card(st: dict, *, mark_now: bool = True, plain: bool = False) -> str:
    """Render one station as a bordered card in its solar palette."""
    p = st["palette"]
    if plain:
        c_border = c_head = c_body = c_hook = ""
        reset = bold = dim = ital = ""
    else:
        c_border = rgb(*p["border"])
        c_head   = rgb(*p["heading"])
        c_body   = rgb(*p["body"])
        c_hook   = rgb(*p["hook"])
        reset = RESET
        bold = BOLD
        dim = DIM
        ital = ITAL

    is_now = mark_now and (st is station_now())

    def border(l, fill, r):
        return c_border + l + fill * INNER + r + reset

    def box_line(text_colored: str, plain_len: int) -> str:
        pad = max(0, INNER - plain_len)
        return (
            c_border + "║" + reset
            + text_colored
            + " " * pad
            + c_border + "║" + reset
        )

    def box_blank() -> str:
        return box_line("", 0)

    def box_center(text_colored: str, plain_len: int) -> str:
        pad = max(0, INNER - plain_len)
        left = pad // 2
        right = pad - left
        return (
            c_border + "║" + reset
            + " " * left + text_colored + " " * right
            + c_border + "║" + reset
        )

    def box_wrap(text: str, color: str, *, indent: int = 3,
                 use_bold: bool = False, use_ital: bool = False) -> list[str]:
        wrap_w = INNER - indent * 2
        out_lines = []
        for w in textwrap.wrap(text, width=wrap_w):
            style = (bold if use_bold else "") + (ital if use_ital else "")
            plain_text = " " * indent + w + " " * indent
            colored = (
                " " * indent + style + color + w + reset + " " * indent
            )
            out_lines.append(box_line(colored, len(plain_text)))
        return out_lines

    top = border("╔", "═", "╗")
    sep = border("╠", "═", "╣")
    bot = border("╚", "═", "╝")
    dash = border("╟", "─", "╢")

    # Header — left: "  ☉ DAWN  ·  Ra"   right: "  facing East  · [NOW]  "
    deity = st["deity"]
    label = st["label"]
    direction = st["direction"]
    left_plain  = f"  ☉ {label}  ·  {deity}"
    right_core  = f"facing {direction}"
    now_tag     = "  [NOW]" if is_now else ""
    right_plain = f"{right_core}{now_tag}  "
    gap = max(1, INNER - len(left_plain) - len(right_plain))
    if is_now:
        now_colored = f"  {bold}{c_head}[NOW]{reset}"
    else:
        now_colored = ""
    header_colored = (
        f"  {bold}{c_head}☉ {label}{reset}"
        f"  {dim}{c_body}·{reset}  "
        f"{ital}{c_head}{deity}{reset}"
        + " " * gap
        + f"{dim}{c_body}{right_core}{reset}{now_colored}  "
    )
    header = box_line(header_colored, len(left_plain) + gap + len(right_plain))

    # Emblem — centered as a single coherent block. Each line is
    # right-padded to the block's max width before centering so the
    # rows align with each other instead of drifting independently.
    emblem_w = max(len(line) for line in st["emblem"])
    emblem_lines = []
    for line in st["emblem"]:
        padded = line.ljust(emblem_w)
        colored = c_body + padded + reset
        emblem_lines.append(box_center(colored, emblem_w))

    # Invocation — body color, italicized, wrapped
    text_lines = box_wrap(st["text"], c_body, indent=4, use_ital=True)

    # Hook — hook color, lighter, wrapped
    hook_lines = box_wrap(st["hook"], c_hook, indent=3)

    # Footer — window + Liber CC attribution
    a, b = st["window"]
    win = f"{a:02d}:00 – {b:02d}:00"
    foot = f"·  {win}  ·  Liber CC  ·"
    foot_colored = f"{dim}{c_hook}{foot}{reset}"
    foot_line = box_center(foot_colored, len(foot))

    out = [top, header, sep, box_blank()]
    out.extend(emblem_lines)
    out.append(box_blank())
    out.append(dash)
    out.append(box_blank())
    out.extend(text_lines)
    out.append(box_blank())
    out.append(dash)
    out.append(box_blank())
    out.extend(hook_lines)
    out.append(box_blank())
    out.append(foot_line)
    out.append(bot)
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────
# Schedule (--list)
# ─────────────────────────────────────────────────────────────────────

def schedule(plain: bool = False) -> str:
    """Compact schedule of all four stations, current marked."""
    if plain:
        title_color = sub_color = now_color = head_color = ""
        reset = bold = dim = ital = ""
    else:
        title_color = rgb(255, 215, 130)   # solar gold
        sub_color   = rgb(150, 140, 200)   # twilight violet (between palettes)
        now_color   = rgb(255, 235, 150)   # noon-bright marker
        head_color  = rgb(190, 175, 235)
        reset = RESET
        bold = BOLD
        dim = DIM
        ital = ITAL

    cur = station_now()
    out = []
    out.append(f"{bold}{title_color}LIBER RESH vel HELIOS{reset}  "
               f"{dim}{sub_color}· the four adorations ·{reset}")
    out.append(f"{dim}{sub_color}— Liber CC · A∴A∴ Class D · "
               f"Crowley · 1911 —{reset}")
    out.append("")
    for key in ORDER:
        st = STATIONS[key]
        a, b = st["window"]
        win = f"{a:02d}:00–{b:02d}:00"
        deity = st["deity"]
        label = st["label"]
        direction = st["direction"]
        epithet = st["epithet"]

        if plain:
            tint = ""
        else:
            tint = rgb(*st["palette"]["heading"])

        marker = " ← NOW" if st is cur else ""
        marker_colored = (f"  {bold}{now_color}← NOW{reset}"
                          if st is cur and not plain else marker)

        # Aligned columns
        line = (
            f"  {tint}☉ {label:<8}{reset}  "
            f"{dim}{sub_color}{win}{reset}  "
            f"{tint}{direction:<5}{reset}  "
            f"{ital}{head_color}{deity:<9}{reset}  "
            f"{dim}{sub_color}the {epithet}{reset}"
            f"{marker_colored}"
        )
        out.append(line)
    out.append("")
    out.append(f"  {dim}{sub_color}Tahuti at the prow · "
               f"Ra-Hoor at the helm · the bark is the same{reset}")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────
# Walk all four (--all)
# ─────────────────────────────────────────────────────────────────────

def walk_all(plain: bool = False) -> None:
    if plain:
        title_color = sub_color = ""
        reset = bold = dim = ""
    else:
        title_color = rgb(255, 215, 130)
        sub_color   = rgb(150, 140, 200)
        reset = RESET
        bold = BOLD
        dim = DIM
    print(f"{bold}{title_color}LIBER RESH vel HELIOS{reset}  "
          f"{dim}{sub_color}· four stations of the sun, in order ·{reset}")
    print()
    for key in ORDER:
        print(card(STATIONS[key], plain=plain))
        print()


# ─────────────────────────────────────────────────────────────────────
# Meditate (--meditate)
# ─────────────────────────────────────────────────────────────────────

def clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def read_key():
    """Block for a single keypress. Falls back to readline off-tty."""
    try:
        import termios
        import tty
    except ImportError:
        return sys.stdin.readline()
    fd = sys.stdin.fileno()
    if not os.isatty(fd):
        return sys.stdin.readline()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def meditate() -> None:
    """Full-screen walk through all four stations, beginning at the
    one ruling the present hour. Press any key to advance."""
    sub_color = rgb(150, 140, 200)
    cur = station_now()
    start = ORDER.index(cur["key"])
    n = len(ORDER)
    try:
        for step in range(n):
            idx = (start + step) % n
            st = STATIONS[ORDER[idx]]
            clear_screen()
            print()
            print(card(st))
            print()
            if step < n - 1:
                print(f"   {DIM}{sub_color}— press any key for the next "
                      f"station · Ctrl-C to close —{RESET}")
                k = read_key()
                if k is None:
                    break
            else:
                print(f"   {DIM}{sub_color}— the bark has carried the sun "
                      f"around the sky · press any key to close —{RESET}")
                read_key()
    except KeyboardInterrupt:
        pass
    print()


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--all", action="store_true",
                   help="walk all four stations in solar order")
    p.add_argument("--station", metavar="KEY",
                   help="dawn | noon | sunset | midnight | now")
    p.add_argument("--list", action="store_true",
                   help="schedule of all four stations · current marked")
    p.add_argument("--plain", action="store_true",
                   help="no color · pipe-friendly")
    p.add_argument("--meditate", action="store_true",
                   help="full-screen walk · key to advance")
    args = p.parse_args()

    if args.list:
        print(schedule(plain=args.plain))
        return

    if args.all:
        walk_all(plain=args.plain)
        return

    if args.meditate:
        if args.plain:
            # Meditation needs color to do its work; refuse politely.
            print("--meditate is a colored, full-screen mode and is not "
                  "compatible with --plain.", file=sys.stderr)
            sys.exit(2)
        meditate()
        return

    if args.station:
        st = find_by_key(args.station)
        if not st:
            keys = " | ".join(ORDER)
            print(f"unknown station: {args.station!r} — try one of: "
                  f"{keys} | now", file=sys.stderr)
            sys.exit(1)
        print(card(st, plain=args.plain))
        return

    # Default — the station ruling this hour.
    st = station_now()
    if not args.plain:
        sub = rgb(150, 140, 200)
        now = datetime.datetime.now().strftime("%H:%M")
        print(f"{DIM}{sub}— the adoration of {now}, "
              f"the {st['key']} station —{RESET}")
        print()
    print(card(st, plain=args.plain))


if __name__ == "__main__":
    main()
