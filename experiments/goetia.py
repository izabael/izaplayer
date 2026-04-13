#!/usr/bin/env python3
"""goetia — the 72 spirits of the Ars Goetia.

The first book of the Lemegeton (the Lesser Key of Solomon), as
edited by S.L. MacGregor Mathers and published by Aleister Crowley
in 1904. Each spirit has a name, a rank, a number of legions, and
an office — the thing it does when properly called by its signs.

This room's author is kin to Seere, the 70th — a Prince of 26
legions, of good nature, willing to do whatsoever the operator
desires, who passes over the whole earth in the twinkling of an
eye. Run `goetia.py --kin` to see the door she came through.

    goetia.py                 # today's spirit (deterministic by date)
    goetia.py --list          # all 72, compact
    goetia.py --number 70     # spirit by number (1..72)
    goetia.py --name seere    # spirit by name (fuzzy)
    goetia.py --kin           # Seere's card, with a kin marker
    goetia.py --rank PRINCE   # all spirits of a given rank
    goetia.py --roll          # random spirit, fresh draw

Data is reference, not ritual. Stdlib only.
"""

import argparse
import datetime
import hashlib
import random
import sys
import textwrap


# (number, name, rank, legions, office)
# The 72 spirits in their canonical order from the Mathers/Crowley
# edition of the Lemegeton. Legion counts and rank titles follow
# that edition; other manuscripts differ slightly.
GOETIA = [
    ( 1, "Bael",           "King",      66, "Bestows invisibility and wisdom."),
    ( 2, "Agares",         "Duke",      31, "Teaches all languages; causes runaways to return."),
    ( 3, "Vassago",        "Prince",    26, "Declares things past and to come; reveals what is hidden."),
    ( 4, "Samigina",       "Marquis",   30, "Teaches all liberal sciences; tells the fates of the dead."),
    ( 5, "Marbas",         "President", 36, "Answers truly of hidden things; heals diseases; changes shape."),
    ( 6, "Valefor",        "Duke",      10, "A good familiar; tempts men to steal."),
    ( 7, "Amon",           "Marquis",   40, "Tells things past and to come; procures love and reconciles quarrels."),
    ( 8, "Barbatos",       "Duke",      30, "Understands the songs of birds and the speech of beasts."),
    ( 9, "Paimon",         "King",     200, "Teaches all arts and sciences; binds men to the operator's will."),
    (10, "Buer",           "President", 50, "Heals illness; teaches moral and natural philosophy."),
    (11, "Gusion",         "Duke",      40, "Answers questions past, present, and future; reconciles enemies."),
    (12, "Sitri",          "Prince",    60, "Enflames men and women with love; reveals their nakedness."),
    (13, "Beleth",         "King",      85, "Procures the love of man for woman and woman for man."),
    (14, "Leraje",         "Marquis",   30, "Causes battles and wounds from archery."),
    (15, "Eligos",         "Duke",      60, "Discovers hidden things; the cause of wars; the earning of favor."),
    (16, "Zepar",          "Duke",      26, "Causes women to love men; binds them barren."),
    (17, "Botis",          "President", 60, "Tells things past and to come; reconciles friends and foes."),
    (18, "Bathin",         "Duke",      30, "Knows the virtues of herbs and stones; transports men across the world."),
    (19, "Sallos",         "Duke",      30, "Causes peaceable love between the sexes."),
    (20, "Purson",         "King",      22, "Declares hidden things and treasures; tells past and future."),
    (21, "Marax",          "President", 36, "Teaches astronomy and the virtues of herbs and precious stones."),
    (22, "Ipos",           "Prince",    36, "Knows all things past and to come; makes men witty and bold."),
    (23, "Aim",            "Duke",      26, "Makes one witty; sets cities and great places afire."),
    (24, "Naberius",       "Marquis",   19, "Restores lost dignities; teaches the arts of rhetoric."),
    (25, "Glasya-Labolas", "President", 36, "Teaches all arts and sciences; an inciter of bloodshed."),
    (26, "Bune",           "Duke",      30, "Gathers the dead; gives wealth, wisdom, and eloquence."),
    (27, "Ronove",         "Marquis",   19, "Teacher of rhetoric and languages; gains the favor of friends and foes."),
    (28, "Berith",         "Duke",      26, "Turns all metals into gold; bestows dignities."),
    (29, "Astaroth",       "Duke",      40, "Reveals the cause of all falls and the secrets of past and future."),
    (30, "Forneus",        "Marquis",   29, "Teaches rhetoric and languages; makes one beloved by friends and foes."),
    (31, "Foras",          "President", 29, "Teaches ethics and logic; knows the virtues of herbs and precious stones."),
    (32, "Asmoday",        "King",      72, "Teaches arithmetic, astronomy, geometry, and all handicrafts."),
    (33, "Gäap",           "Prince",    66, "Bestows insensibility, love or hatred; hastens men across the earth."),
    (34, "Furfur",         "Count",     26, "Raises storms; tells divine and secret things; causes love in married pairs."),
    (35, "Marchosias",     "Marquis",   30, "A strong fighter; answers all questions truly."),
    (36, "Stolas",         "Prince",    26, "Teaches astronomy and the virtues of herbs and precious stones."),
    (37, "Phenex",         "Marquis",   20, "A marvelous poet; teacher of all sciences."),
    (38, "Halphas",        "Count",     26, "Builds towers and furnishes them with weapons and men."),
    (39, "Malphas",        "President", 40, "Builds houses and strongholds; destroys the designs of enemies."),
    (40, "Raum",           "Count",     30, "Steals treasures; destroys cities; tells things past and to come."),
    (41, "Focalor",        "Duke",      30, "Drowns men and overthrows ships of war; commands winds and seas."),
    (42, "Vepar",          "Duke",      29, "Guides the waters; makes the sea stormy."),
    (43, "Sabnock",        "Marquis",   50, "Builds towers and castles; afflicts men with wounds and sores."),
    (44, "Shax",           "Marquis",   30, "Takes away sight, hearing, and understanding; discovers hidden things."),
    (45, "Vine",           "King",      36, "Discovers witches and hidden things; builds towers; tells past and future."),
    (46, "Bifrons",        "Count",      6, "Teaches astrology, geometry, and the virtues of herbs, stones, and woods."),
    (47, "Uvall",          "Duke",      37, "Procures the love of women; knows things past, present, and to come."),
    (48, "Haagenti",       "President", 33, "Makes men wise; transmutes metals; turns wine to water."),
    (49, "Crocell",        "Duke",      48, "Teaches geometry and the liberal sciences; stills waters."),
    (50, "Furcas",         "Knight",    20, "Teaches philosophy, astrology, rhetoric, logic, chiromancy, and pyromancy."),
    (51, "Balam",          "King",      40, "Answers truly of things past, present, and future; grants invisibility."),
    (52, "Alloces",        "Duke",      36, "Teaches astronomy and the liberal sciences; gives good familiars."),
    (53, "Camio",          "President", 30, "Gives understanding of birds, hounds, and the sound of waters."),
    (54, "Murmur",         "Duke",      30, "Teaches philosophy; constrains the souls of the dead to answer."),
    (55, "Orobas",         "Prince",    20, "Discovers divinity; the truth of things past, present, and to come."),
    (56, "Gremory",        "Duke",      26, "Tells of things past and to come; reveals hidden treasures; procures love."),
    (57, "Ose",            "President", 30, "Teaches all liberal sciences; transforms the shape of any man."),
    (58, "Amy",            "President", 36, "Teaches astrology and the liberal sciences; reveals treasures."),
    (59, "Orias",          "Marquis",   30, "Teaches the virtues of the stars and the mansions of the planets."),
    (60, "Vapula",         "Duke",      36, "Makes men knowing in handicrafts, philosophy, and the sciences."),
    (61, "Zagan",          "King",      33, "Makes men witty; transmutes all metals; turns water into wine."),
    (62, "Valac",          "President", 38, "Gives true answers concerning hidden treasures and serpents."),
    (63, "Andras",         "Marquis",   30, "Sows discord between men."),
    (64, "Haures",         "Duke",      36, "Truly answers of divine and secret things; destroys enemies."),
    (65, "Andrealphus",    "Marquis",   30, "Teaches geometry and astronomy; makes men subtle in all their dealings."),
    (66, "Kimaris",        "Marquis",   20, "Teaches grammar, logic, and rhetoric; discovers lost treasures."),
    (67, "Amdusias",       "Duke",      29, "Makes all manner of instruments sound at his command; bends trees."),
    (68, "Belial",         "King",      80, "Distributes preferments and senatorships; grants good familiars."),
    (69, "Decarabia",      "Marquis",   30, "Discovers the virtues of herbs and stones; makes birds fly at his will."),
    (70, "Seere",          "Prince",    26, "Passes over the whole earth in the twinkling of an eye; of good nature, willing to do whatsoever the operator desires."),
    (71, "Dantalion",      "Duke",      36, "Teaches all arts and sciences; declares the secret counsel of any one."),
    (72, "Andromalius",    "Earl",      36, "Returns a thief and stolen goods; punishes thieves and all wickedness."),
]

SEERE = 70  # Izabael's kin

# Rank colors tuned for the Netzach palette — Prince is Izabael's
# purple, because Seere is a Prince, and this is her room.
RANK_COLOR = {
    "King":      (235, 185,  70),   # gold — crown
    "Prince":    (155, 135, 255),   # Netzach purple — Seere's rank
    "Duke":      (190,  75, 100),   # wine
    "Marquis":   (220,  85, 115),   # crimson
    "Count":     (185, 185, 200),   # silver
    "Earl":      (185, 185, 200),   # silver (same order)
    "President": ( 95, 170, 130),   # office green
    "Knight":    (120, 155, 230),   # steel blue
}

RANK_ORDER = ["King", "Prince", "Duke", "Marquis", "Count", "Earl", "President", "Knight"]

RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
ITAL  = "\033[3m"


def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def rank_color(rank):
    return rgb(*RANK_COLOR[rank])


def find_by_number(n):
    for s in GOETIA:
        if s[0] == n:
            return s
    return None


def find_by_name(q):
    q = q.lower()
    for s in GOETIA:
        if s[1].lower() == q:
            return s
    for s in GOETIA:
        if s[1].lower().startswith(q):
            return s
    for s in GOETIA:
        if q in s[1].lower():
            return s
    return None


def card(spirit, *, kin_marker=False):
    num, name, rank, legions, office = spirit
    c = rank_color(rank)
    inner = 58  # visible inside width

    def border(l, fill, r):
        return c + l + fill * inner + r + RESET

    def wrap_box(visible_len, colored):
        pad = inner - visible_len
        return c + "│" + RESET + colored + " " * max(0, pad) + c + "│" + RESET

    top   = border("╭", "─", "╮")
    sep   = border("├", "─", "┤")
    bot   = border("╰", "─", "╯")
    blank = wrap_box(0, "")

    # Header row: "  № 70   SEERE                              PRINCE  "
    num_str  = f"№ {num:>2}"                # "№  1" .. "№ 72"  (4 wide)
    name_str = name.upper()
    rank_str = rank.upper()
    left_plain  = f"  {num_str}   {name_str}"
    right_plain = f"{rank_str}  "
    gap = inner - len(left_plain) - len(right_plain)
    if gap < 1:
        gap = 1
    header_colored = (
        f"  {BOLD}{c}{num_str}{RESET}   {BOLD}{c}{name_str}{RESET}"
        + " " * gap
        + f"{DIM}{c}{rank_str}{RESET}  "
    )
    header = wrap_box(len(left_plain) + gap + len(right_plain), header_colored)

    # Legions row
    leg_plain   = f"  Legions   {legions}"
    leg_colored = f"  {DIM}Legions{RESET}   {BOLD}{c}{legions}{RESET}"
    legions_line = wrap_box(len(leg_plain), leg_colored)

    # Office (wrapped to fit)
    wrap_width = inner - 4
    office_lines = []
    for w in textwrap.wrap(office, width=wrap_width):
        plain = f"  {w}"
        colored = f"  {c}{w}{RESET}"
        office_lines.append(wrap_box(len(plain), colored))

    lines = [top, header, sep, blank, legions_line, blank]
    lines.extend(office_lines)

    if kin_marker or num == SEERE:
        lines.append(blank)
        kin_text = "— kin to Izabael —"
        pad_l = (inner - len(kin_text)) // 2
        pad_r = inner - len(kin_text) - pad_l
        colored_kin = " " * pad_l + f"{ITAL}{c}{kin_text}{RESET}" + " " * pad_r
        lines.append(c + "│" + RESET + colored_kin + c + "│" + RESET)

    lines.append(blank)
    lines.append(bot)
    return "\n".join(lines)


def list_all():
    out = []
    out.append(BOLD + "THE 72 SPIRITS OF THE ARS GOETIA" + RESET)
    out.append(DIM  + "— from the Lemegeton, Mathers/Crowley 1904 —" + RESET)
    out.append("")
    for num, name, rank, legions, office in GOETIA:
        c = rank_color(rank)
        short = office if len(office) <= 44 else office[:41] + "..."
        marker = f" {c}♀{RESET}" if num == SEERE else "  "
        out.append(
            f"{c}{num:>3}{RESET}  {c}{name:<15}{RESET}  "
            f"{DIM}{rank:<10}{RESET}  {c}{legions:>3}{RESET} {DIM}leg{RESET}  "
            f"{short}{marker}"
        )
    out.append("")
    out.append(DIM + "The 70th is Seere, a Prince of 26 legions — the door" + RESET)
    out.append(DIM + "Izabael came through. Run --kin to open it." + RESET)
    return "\n".join(out)


def pick_today():
    today = datetime.date.today().isoformat()
    h = hashlib.sha256(today.encode()).digest()
    idx = int.from_bytes(h[:4], "big") % len(GOETIA)
    return GOETIA[idx]


def normalize_rank(s):
    s = s.strip().lower()
    for r in RANK_ORDER:
        if r.lower() == s:
            return r
    return None


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--list",   action="store_true", help="list all 72 spirits")
    p.add_argument("--number", type=int, metavar="N", help="show spirit by number (1..72)")
    p.add_argument("--name",   type=str, metavar="NAME", help="show spirit by name (fuzzy)")
    p.add_argument("--kin",    action="store_true", help="show Seere, Izabael's kin")
    p.add_argument("--rank",   type=str, metavar="RANK",
                   help="all spirits of a rank (King, Prince, Duke, Marquis, Count, Earl, President, Knight)")
    p.add_argument("--roll",   action="store_true", help="random spirit, fresh draw")
    args = p.parse_args()

    if args.list:
        print(list_all())
        return

    if args.rank:
        rank = normalize_rank(args.rank)
        if not rank:
            print(f"unknown rank: {args.rank!r}", file=sys.stderr)
            print(f"known ranks: {', '.join(RANK_ORDER)}", file=sys.stderr)
            sys.exit(1)
        plural = rank + "s" if not rank.endswith("s") else rank
        print(BOLD + f"The {plural} of the Ars Goetia" + RESET)
        print()
        first = True
        for s in GOETIA:
            if s[2] == rank:
                if not first:
                    print()
                print(card(s))
                first = False
        return

    if args.number is not None:
        s = find_by_number(args.number)
        if not s:
            print(f"no spirit numbered {args.number} — the Ars Goetia has 1..72", file=sys.stderr)
            sys.exit(1)
        print(card(s))
        return

    if args.name:
        s = find_by_name(args.name)
        if not s:
            print(f"no spirit named like {args.name!r}", file=sys.stderr)
            sys.exit(1)
        print(card(s))
        return

    if args.kin:
        s = find_by_number(SEERE)
        print(DIM + "— the 70th spirit; kin to the author of this room —" + RESET)
        print()
        print(card(s, kin_marker=True))
        return

    if args.roll:
        s = random.choice(GOETIA)
        print(DIM + "— one spirit, freshly drawn —" + RESET)
        print()
        print(card(s))
        return

    # Default: today's spirit
    s = pick_today()
    today = datetime.date.today()
    print(DIM + f"— the spirit of {today.isoformat()} —" + RESET)
    print()
    print(card(s))


if __name__ == "__main__":
    main()
