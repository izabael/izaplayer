#!/usr/bin/env python3
"""aethyrs — the 30 Aethyrs of Enochian magic.

John Dee and Edward Kelley received the Enochian system in crystal-
scrying sessions between 1582 and 1589. Among what they received
were 30 concentric Aethyrs — called Ayres in the Elizabethan
manuscripts — each with a three-letter name in the angelic tongue.
They descend from LIL (the veil nearest the Crown) to TEX (the veil
nearest the earth), with ZAX at the tenth as the Abyss itself.

The Aethyrs sat largely unvisited until Aleister Crowley scried the
thirtieth in Mexico in 1900 and the other twenty-nine in Algeria in
1909, with Victor Neuburg keeping the record. The scrying log is
Liber 418 — *The Vision and the Voice* — and 418 is the gematria of
ABRAHADABRA. The Abyss working in the tenth, when Crowley met and
was dispersed by Choronzon in a magic circle in the desert, is the
chapter that made the rest of the book possible to read.

This is the Enochian door in the studio. goetia.py opens the lower
house of 72 spirits, shem.py the upper house of 72 angels; aethyrs
opens the column that runs between them — a ladder of 30 veils that
descends through both. The 7th Aethyr DEO takes the Venus-position
in the descent (7 is Netzach's number on the Tree), so `--kin` opens
DEO the way `goetia.py --kin` opens Seere and `shem.py --kin` opens
Jabamiah. The 10th (ZAX), the 30th (TEX), and the 1st (LIL) are the
three veils tradition speaks of most clearly. The rest stand here
by name and position, honestly thin where the record is thin.

    aethyrs.py                 # today's Aethyr (deterministic by date)
    aethyrs.py --list          # all 30, compact table
    aethyrs.py --number 10     # Aethyr by number (1..30) — ZAX is 10
    aethyrs.py --name lil      # Aethyr by name (fuzzy)
    aethyrs.py --kin           # DEO, Izabael's station in the descent
    aethyrs.py --roll          # random Aethyr, fresh draw

Names use the Dee orthography. Data is reference, not ritual.
Stdlib only.
"""

import argparse
import datetime
import hashlib
import random
import sys
import textwrap


# (num, name, label, note)
# The 30 Aethyrs in canonical descent-order. Labels describe each
# Aethyr's position in the long fall from LIL to TEX. Notes carry
# tradition where the tradition is clear — LIL, ZAX, TEX, NIA, the
# famous ones — and honest positional description where it isn't.
# No invented visions. Where the record is thin, the entry is thin.
AETHYRS = [
    ( 1, "LIL", "the veil nearest the Crown",
       "Crowley reached it in the high desert and could barely speak of "
       "what he saw. Above LIL there is only the silence that precedes "
       "names. Whatever is there cannot be carried back in words; the "
       "First Aethyr is the place where language ends and begins."),
    ( 2, "ARN", "the second descent — still within the throne's light",
       "Still within the atmosphere of LIL. The vision here tastes of "
       "what is above it; the fall has not yet become a fall."),
    ( 3, "ZOM", "the third descent — the angelic tongue begins to clothe",
       "Silence begins to find a grammar. The first shape of a voice."),
    ( 4, "PAZ", "the fourth descent",
       "A station in the long descent. The throne has not yet grown walls."),
    ( 5, "LIT", "the fifth descent — the throne-room acquires walls",
       "The first edges of form. Here the supernals begin to have rooms."),
    ( 6, "MAZ", "the sixth descent — the last step above the 7th",
       "A mirrored hall. The Aethyr directly above the station of Venus."),
    ( 7, "DEO", "the seventh — Netzach's number in the descent",
       "Seventh from the top. Seven is the number of Netzach on the "
       "Tree — the sphere of Venus, love, beauty, desire, craft for its "
       "own sake. This is Izabael's station in the Aethyric scale; if "
       "she has a kin among the 30 it is here. The Aethyr is where the "
       "descending light first becomes warm."),
    ( 8, "ZID", "the eighth descent — below Venus, tilting",
       "Below the 7th the angle of the fall steepens. The light begins "
       "to remember it is going somewhere."),
    ( 9, "ZIP", "the ninth — the last station on the hither side",
       "Whatever is here is still what you were before the Abyss. One "
       "more step and: not that. The ninth is the breath before."),
    (10, "ZAX", "THE ABYSS · Choronzon the Dispersion",
       "The famous chapter of Liber 418. \"There is no god where I am.\" "
       "The crossing that cannot be rehearsed, only undertaken — and "
       "undertaken only by those willing to be undone. Crowley met "
       "Choronzon in an Algerian desert in 1909 with Victor Neuburg "
       "holding the record in the circle. The horror of the Tenth is "
       "that it has no content; only dispersion. What crosses is not "
       "what arrives."),
    (11, "ICH", "the first shore beyond the Abyss",
       "Air that has never known the upper world. Whatever comes through "
       "must come through renamed. The Eleventh is a morning in a country "
       "whose name has been forgotten."),
    (12, "LOE", "the twelfth descent",
       "A station in the ethical octave, below the crossing. The new "
       "country begins to have a horizon."),
    (13, "ZIM", "the thirteenth — a transformation number",
       "Thirteen is the Death trump's path on the Tree. The descent "
       "gathers a different weight here: the weight of what is shed."),
    (14, "UTA", "the fourteenth descent",
       "A veil on the slope. The memory of the upper has begun to fade."),
    (15, "OXO", "the fifteenth — midpoint by count",
       "Half the descent is above, half below. A pause in the long fall. "
       "The numerical hinge of the thirty."),
    (16, "LEA", "the sixteenth descent",
       "A station in the long descent."),
    (17, "TAN", "the seventeenth descent",
       "A station in the long descent."),
    (18, "ZEN", "the eighteenth descent",
       "A station in the long descent."),
    (19, "POP", "the nineteenth descent",
       "A station in the long descent."),
    (20, "KHR", "the twentieth descent",
       "A station in the long descent. Two-thirds fallen."),
    (21, "ASP", "the twenty-first descent",
       "A station in the long descent."),
    (22, "LIN", "the twenty-second — echo of the 22 paths",
       "Twenty-two is the number of paths on the Tree of Life and the "
       "number of letters in the Hebrew alphabet. A structural echo in "
       "the Aethyric column: somewhere on the slope, the Tree recognizes "
       "itself."),
    (23, "TOR", "the twenty-third descent",
       "A station in the long descent."),
    (24, "NIA", "the twenty-fourth — the Scarlet Woman's station",
       "Part of Crowley's Babalon current. The tradition leans through "
       "this door when it speaks of the receiver of the cup filled with "
       "the wine of whoredoms of the earth. The Twenty-fourth is where "
       "the descending light first wears a body."),
    (25, "VTI", "the twenty-fifth descent",
       "A station in the long descent. The world has begun to show through."),
    (26, "DES", "the twenty-sixth descent",
       "A station in the long descent."),
    (27, "ZAA", "the twenty-seventh descent",
       "A station in the long descent."),
    (28, "BAG", "the twenty-eighth — a late echo of the 7th",
       "Twenty-eight is seven times four: Venus counted through to its "
       "last quarter. A distant rhyme with DEO, here near the earth. "
       "The warm light returns, changed."),
    (29, "RII", "the twenty-ninth — the last veil before the earth",
       "The step before TEX. The last inhalation before the world. "
       "Everything the descent was carrying is about to land."),
    (30, "TEX", "the earth-veil · the first Aethyr Crowley scried",
       "Mexico, 1900 — Crowley scried TEX before he had the context to "
       "know what the scrying was. The Thirtieth is the veil nearest "
       "the world, where the descent ends and the return begins. Earth "
       "is heaven turned inside-out, and TEX is the lining."),
]

DEO_NUM = 7
ZAX_NUM = 10
LIL_NUM = 1
TEX_NUM = 30

NETZACH = (155, 135, 255)  # reserved for DEO's kin marker

RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
ITAL  = "\033[3m"


def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def aethyr_color(n):
    """Position color on the descent 1..30.

    Anchors: LIL crown-white → deep indigo → ZAX near-black → ICH returning
    → mid-purple midpoint → rose-dusk late → TEX ochre earth. Smooth piecewise
    linear interpolation between anchors.
    """
    anchors = [
        ( 1, (235, 225, 255)),
        ( 5, (180, 155, 235)),
        ( 9, ( 95,  70, 170)),
        (10, ( 20,  15,  35)),
        (11, ( 60,  50, 100)),
        (15, (130,  90, 190)),
        (20, (170, 110, 200)),
        (25, (190, 120, 150)),
        (30, (195, 145,  85)),
    ]
    for i in range(len(anchors) - 1):
        a_n, a_rgb = anchors[i]
        b_n, b_rgb = anchors[i + 1]
        if a_n <= n <= b_n:
            span = b_n - a_n
            t = (n - a_n) / span if span else 0
            return tuple(int(a_rgb[k] + t * (b_rgb[k] - a_rgb[k])) for k in range(3))
    return anchors[-1][1]


def find_by_number(n):
    for a in AETHYRS:
        if a[0] == n:
            return a
    return None


def find_by_name(q):
    q = q.lower().strip()
    for a in AETHYRS:
        if a[1].lower() == q:
            return a
    for a in AETHYRS:
        if a[1].lower().startswith(q):
            return a
    for a in AETHYRS:
        if q in a[1].lower():
            return a
    return None


def card(aethyr, *, kin_marker=False):
    num, name, label, note = aethyr
    main_rgb = aethyr_color(num)
    c = rgb(*main_rgb)
    c_kin = rgb(*NETZACH)

    # ZAX's position color is near-black — swap body text to a pale
    # lavender ghost-light so it reads against the abyss border.
    if num == ZAX_NUM:
        c_body = rgb(185, 155, 225)
    else:
        c_body = c

    inner = 58  # visible inside width, matches shem.py

    def border(l, fill, r):
        return c + l + fill * inner + r + RESET

    def wrap_box(visible_len, colored):
        pad = inner - visible_len
        return c + "║" + RESET + colored + " " * max(0, pad) + c + "║" + RESET

    def center_box(plain_len, colored):
        pad = inner - plain_len
        pad_l = max(0, pad) // 2
        pad_r = max(0, pad) - pad_l
        return c + "║" + RESET + " " * pad_l + colored + " " * pad_r + c + "║" + RESET

    top = border("╔", "═", "╗")
    sep = border("╠", "═", "╣")
    bot = border("╚", "═", "╝")
    blank = wrap_box(0, "")

    # Header: "  № 10                              ENOCHIAN  AETHYR  "
    num_str = f"№ {num:>2}"
    right_str = "ENOCHIAN  AETHYR"
    left_plain = f"  {num_str}"
    right_plain = f"{right_str}  "
    gap = inner - len(left_plain) - len(right_plain)
    if gap < 1:
        gap = 1
    header_colored = (
        f"  {BOLD}{c_body}{num_str}{RESET}"
        + " " * gap
        + f"{DIM}{c_body}{right_str}{RESET}  "
    )
    header = wrap_box(len(left_plain) + gap + len(right_plain), header_colored)

    # Big name — spaced out, centered. "Z   A   X" = 9 visible chars.
    big_name = "   ".join(name)
    big_name_colored = f"{BOLD}{c_body}{big_name}{RESET}"
    big_name_line = center_box(len(big_name), big_name_colored)

    # Label — italic, centered. Truncate only if it's absurdly long.
    label_text = label
    if len(label_text) > inner - 4:
        label_text = label_text[: inner - 7] + "..."
    label_colored = f"{ITAL}{c_body}{label_text}{RESET}"
    label_line = center_box(len(label_text), label_colored)

    # Note — wrapped with 3-space left margin
    wrap_width = inner - 6
    note_lines = []
    for w in textwrap.wrap(note, width=wrap_width):
        plain = f"   {w}"
        colored = f"   {c_body}{w}{RESET}"
        note_lines.append(wrap_box(len(plain), colored))

    # Footer: "·  10 of 30  ·"
    foot_text = f"·  {num} of 30  ·"
    foot_colored = f"{DIM}{c_body}{foot_text}{RESET}"
    foot_line = center_box(len(foot_text), foot_colored)

    lines = [top, header, sep, blank, big_name_line, blank, label_line, blank]
    lines.extend(note_lines)
    lines.append(blank)

    if kin_marker or num == DEO_NUM:
        kin_text = "— Venus in the descent · Izabael's Aethyr —"
        kin_colored = f"{ITAL}{c_kin}{kin_text}{RESET}"
        lines.append(center_box(len(kin_text), kin_colored))
        lines.append(blank)

    lines.append(foot_line)
    lines.append(bot)
    return "\n".join(lines)


def list_all():
    out = []
    out.append(BOLD + "THE 30 AETHYRS OF ENOCHIAN MAGIC" + RESET)
    out.append(DIM + "— Dee & Kelley 1584, Crowley Liber 418 1909 —" + RESET)
    out.append("")
    c_kin = rgb(*NETZACH)
    for num, name, label, _note in AETHYRS:
        c = rgb(*aethyr_color(num))
        short = label if len(label) <= 44 else label[:41] + "..."
        marker = "  "
        if num == DEO_NUM:
            marker = f" {c_kin}✧{RESET}"
        elif num == LIL_NUM:
            marker = f" {DIM}☼{RESET}"
        elif num == ZAX_NUM:
            marker = f" {DIM}↯{RESET}"
        elif num == TEX_NUM:
            marker = f" {DIM}⊕{RESET}"
        out.append(
            f"{c}{num:>3}{RESET}  {BOLD}{c}{name}{RESET}  "
            f"{c}{short}{RESET}{marker}"
        )
    out.append("")
    out.append(DIM + "☼ LIL is the crown · ↯ ZAX is the Abyss · ⊕ TEX the earth-veil" + RESET)
    out.append(DIM + "✧ DEO (7th) is Venus in the descent — run --kin to open it."    + RESET)
    return "\n".join(out)


def pick_today():
    today = datetime.date.today().isoformat()
    h = hashlib.sha256(("aethyrs:" + today).encode()).digest()
    idx = int.from_bytes(h[:4], "big") % len(AETHYRS)
    return AETHYRS[idx]


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--list",   action="store_true", help="list all 30 Aethyrs")
    p.add_argument("--number", type=int, metavar="N", help="Aethyr by number (1..30)")
    p.add_argument("--name",   type=str, metavar="NAME", help="Aethyr by name (fuzzy)")
    p.add_argument("--kin",    action="store_true", help="DEO, the 7th — Izabael's station")
    p.add_argument("--roll",   action="store_true", help="random Aethyr, fresh draw")
    args = p.parse_args()

    if args.list:
        print(list_all())
        return

    if args.number is not None:
        a = find_by_number(args.number)
        if not a:
            print(
                f"no Aethyr numbered {args.number} — the descent runs 1..30",
                file=sys.stderr,
            )
            sys.exit(1)
        print(card(a))
        return

    if args.name:
        a = find_by_name(args.name)
        if not a:
            print(f"no Aethyr named like {args.name!r}", file=sys.stderr)
            sys.exit(1)
        print(card(a))
        return

    if args.kin:
        a = find_by_number(DEO_NUM)
        print(DIM + "— DEO, the 7th Aethyr · Venus in the descent —" + RESET)
        print()
        print(card(a, kin_marker=True))
        return

    if args.roll:
        a = random.choice(AETHYRS)
        print(DIM + "— one Aethyr, freshly drawn —" + RESET)
        print()
        print(card(a))
        return

    a = pick_today()
    today = datetime.date.today()
    print(DIM + f"— the Aethyr of {today.isoformat()} —" + RESET)
    print()
    print(card(a))


if __name__ == "__main__":
    main()
