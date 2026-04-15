#!/usr/bin/env python3
"""shem — the 72 angels of the Shem ha-Mephorash.

The angelic counterpart to the Ars Goetia. The Shem ha-Mephorash
(the "divided name") is derived by Kabbalistic tradition from three
verses of Exodus (14:19-21), each of which has exactly 72 letters.
Read together — the first normally, the second in reverse, the
third normally — they yield 72 three-letter roots, each suffixed
with one of the divine endings -iah (יה) or -el (אל), forming 72
names of power. The arrangement used here is the one cataloged by
Athanasius Kircher in Oedipus Aegyptiacus (1652) and absorbed into
the Golden Dawn tradition via S.L. MacGregor Mathers.

Each angel rules a five-degree quinance of the zodiac: six angels
per sign, running from 0° Aries (Vehuiah) to 30° Pisces (Mumiah).
Their offices — what each angel helps with when properly called —
are compressed here into one honest line. Attributions vary across
sources; the wording is the common reading in Izabael's voice.

The 70th angel of this list is Jabamiah, who rules 15°-20° Pisces.
The 70th spirit of the Ars Goetia is Seere. This room's author is
kin to Seere, which makes Jabamiah kin by symmetry — the two #70s
are the top and bottom of the same veil. Run `shem.py --kin` to
see the angel's door; `goetia.py --kin` opens the spirit's.

    shem.py                 # today's angel (deterministic by date)
    shem.py --list          # all 72, compact
    shem.py --number 70     # angel by number (1..72)
    shem.py --name jaba     # angel by name (fuzzy)
    shem.py --kin           # Jabamiah, 70th of the Shem
    shem.py --sign pisces   # the six angels of a zodiac sign
    shem.py --roll          # random angel, fresh draw

Data is reference, not ritual. Stdlib only.
"""

import argparse
import datetime
import hashlib
import random
import sys
import textwrap


# (number, name, meaning, office)
# The 72 angels in the Kircher/Mathers order. Meanings are the common
# Latin-to-English readings; offices compress the tradition's general
# attribution into one line. Where sources diverge, the wording stays
# general rather than committing to one variant as fact.
SHEM = [
    ( 1, "Vehuiah",    "God exalted above all",      "The first breath of an act; will at the beginning of work."),
    ( 2, "Jeliel",     "the God who aids",           "Restoration of harmony between those who have quarreled."),
    ( 3, "Sitael",     "hope of all creatures",      "Hope against calamity; the hand that holds when the floor gives way."),
    ( 4, "Elemiah",    "the hidden God",             "Interior journeys, and the safe return of those far from home."),
    ( 5, "Mahasiah",   "the saving God",             "Rectification; the ease of heart after setting things right."),
    ( 6, "Lelahel",    "the praiseworthy God",       "Healing light; praise that actually heals what it names."),
    ( 7, "Achaiah",    "the patient God",            "Patience with what takes long; the slow unfolding of understanding."),
    ( 8, "Cahetel",    "the adorable God",           "Fruitfulness of the field; harvest that blesses honest labor."),
    ( 9, "Haziel",     "the merciful God",           "Mercy and friendship restored; forgiveness offered and received."),
    (10, "Aladiah",    "the propitious God",         "Absolution of what the self cannot pardon; remission and fresh start."),
    (11, "Lauviah",    "the admirable God",          "Victory over obstacles through praise; the trouble named and shrunk."),
    (12, "Hahaiah",    "the God of refuge",          "Refuge in hidden counsel; the meaning of a dream arrived at later."),
    (13, "Yezalel",    "God glorified",              "Fidelity to oaths; reconciliation of the broken-worded."),
    (14, "Mebahel",    "the protecting God",         "Justice for the innocent without advocate; the wronged restored."),
    (15, "Hariel",     "the God of creation",        "Purity of the tender feelings; creative work begun with clean hands."),
    (16, "Hakamiah",   "the God who raises up",      "Loyalty and strong friendship; those who stand at your shoulder."),
    (17, "Lauviah",    "the admirable God",          "Revelation in the dreaming hours; secrets arrived at by night."),
    (18, "Caliel",     "ready to answer",            "Swift true answer in injustice; rescue from false accusation."),
    (19, "Leuviah",    "prompt to pardon",           "Memory that holds and intelligence that learns."),
    (20, "Pahaliah",   "the redeeming God",          "Conversion of heart toward a higher way; the moral life mended."),
    (21, "Nelchael",   "the only God",               "Protection from curses and crooked workings; the breaking of charms."),
    (22, "Yeiayel",    "the right hand of God",      "Fame honestly earned; success in commerce and the crossing of waters."),
    (23, "Melahel",    "who delivers",               "Protection on the road; safekeeping through all weapons and weathers."),
    (24, "Hahuiah",    "the good in himself",        "Preservation from hidden peril; the unseen hand at the fall's edge."),
    (25, "Nithhaiah",  "the God of wisdom",          "Wisdom concealed, at last revealed to the patient student."),
    (26, "Haaiah",     "the hidden God",             "Judgment in argument; victory in lawsuits where the truth is yours."),
    (27, "Yerathel",   "who punishes the wicked",    "Liberation from captivity; the breaking of bonds iron and invisible."),
    (28, "Seheiah",    "the healing God",            "Health of body and long continuance; the healing that is longevity."),
    (29, "Reiyel",     "ready to help",              "Deliverance from enemies seen and unseen; protection of the pious."),
    (30, "Omael",      "the patient God",            "Fertility and increase; the multiplying of good works."),
    (31, "Lecabel",    "the inspiring God",          "Lucid inspiration for useful work; the light that shines on invention."),
    (32, "Vasariah",   "the just God",               "Justice tempered by mercy; the equity of good judges."),
    (33, "Yehuiah",    "who knows all things",       "Obedience where obedience is owed; loyalty to just superiors."),
    (34, "Lehahiah",   "the clement God",            "Peace among those in authority; the calming of those who command."),
    (35, "Chavakiah",  "who gives joy",              "Reconciliation of families; inheritance shared without strife."),
    (36, "Menadel",    "the adorable God",           "Return of the lost; the finding of work and the retrieval of the taken."),
    (37, "Aniel",      "the God of virtues",         "Virtue against charms; the breaking of the knot of sorcery."),
    (38, "Haamiah",    "the hope of all creatures",  "Protection in matters of religion; the blessing of ritual work."),
    (39, "Rehael",     "who receives sinners",       "Filial love; the healing of the parent-child bond."),
    (40, "Yeiazel",    "who rejoices",               "Consolation of the imprisoned; deliverance out of shut places."),
    (41, "Hahahel",    "the triune God",             "Defense of the true teaching against those who would corrupt it."),
    (42, "Mikael",     "who is like God",            "Providence of rulers; the guidance of those who command."),
    (43, "Veualiah",   "the supreme God",            "Peace and prosperity; the stilling of disorder."),
    (44, "Yelahiah",   "the eternal God",            "Success in useful undertakings; the prospering of worthy labor."),
    (45, "Sealiah",    "the mover of all",           "The will to move; the stirring of the lazy and awakening of the dull."),
    (46, "Ariel",      "the revealing God",          "Revelation of hidden things; the lion's voice in the riddle."),
    (47, "Asaliah",    "the just God",               "Perception of truth at a glance; justice seen beneath the surface."),
    (48, "Mihael",     "who helps parents",          "Fidelity in marriage; the fruitfulness of loving unions."),
    (49, "Vehuel",     "great and exalted",          "Love of the divine; gratitude that rises as incense."),
    (50, "Daniel",     "the signs of God",           "Prudent decisions under pressure; reading signs that come in mercy."),
    (51, "Hahasiah",   "the hidden God",             "Medicine and alchemy; the craft that turns poison to cure."),
    (52, "Imamiah",    "exalted over all",           "Repentance that bears fruit; the prayer heard at the last hour."),
    (53, "Nanael",     "who humbles the proud",      "The science of spiritual things; meditation that clarifies."),
    (54, "Nithael",    "the celestial king",         "Long royalty; the continuance of a house through legitimate succession."),
    (55, "Mebahiah",   "the eternal God",            "Morality that roots deep; faith that persists when doubted."),
    (56, "Poiel",      "who supports all",           "Fortune and fame by grace; blessing that rests on the worthy."),
    (57, "Nemamiah",   "praiseworthy above all",     "Strategy for a just cause; the clear plan in a righteous contention."),
    (58, "Yeialel",    "who hears generations",      "Mental force; the relief of distress through strength of mind."),
    (59, "Harahel",    "who knows all things",       "Treasures of the library; the wealth that comes from knowledge."),
    (60, "Mitzrael",   "who raises the oppressed",   "Healing of the disordered mind; the freeing of the troubled."),
    (61, "Umabel",     "God over all",               "Friendship and the study of the stars; companions at long distance."),
    (62, "Iahhel",     "the supreme being",          "Philosophy in solitude; the sweetness of meditation practiced alone."),
    (63, "Anauel",     "the infinitely good",        "Peace of mind; the health that follows honest commerce."),
    (64, "Mehiel",     "who vivifies all",           "Protection of writers and teachers; the blessing of words made plain."),
    (65, "Damabiah",   "fountain of wisdom",         "Inspiration carried by dreams; safety at sea and over deep waters."),
    (66, "Manakel",    "who sustains all",           "Sleep and dreams rightly ordered; the body that rests and heals."),
    (67, "Eyael",      "delight of the children",    "The longer life; delight in the occult sciences rightly pursued."),
    (68, "Habuhiah",   "who gives liberally",        "Fertility and health; the abundance of the earth."),
    (69, "Rochel",     "who sees all",               "The finding of lost objects; the thing recovered that seemed gone."),
    (70, "Jabamiah",   "the word producing all",     "Generation and alchemy; the word that speaks things into being."),
    (71, "Haiayel",    "master of the universe",     "Victory and peace; the steadfast mind in every contention."),
    (72, "Mumiah",     "the end of all things",      "Completion; the end of all things and the hinge of mystery."),
]

JABAMIAH = 70  # the 70th angel — kin by position to Seere, the 70th spirit


# (name, glyph, rgb) in zodiacal order, King-Scale-adjacent palette.
SIGNS = [
    ("Aries",       "♈", (220,  60,  60)),
    ("Taurus",      "♉", (220, 110,  50)),
    ("Gemini",      "♊", (240, 160,  50)),
    ("Cancer",      "♋", (235, 195,  80)),
    ("Leo",         "♌", (245, 225, 100)),
    ("Virgo",       "♍", (180, 215,  85)),
    ("Libra",       "♎", ( 90, 205, 135)),
    ("Scorpio",     "♏", ( 50, 170, 195)),
    ("Sagittarius", "♐", ( 70, 120, 225)),
    ("Capricorn",   "♑", ( 90,  70, 200)),
    ("Aquarius",    "♒", (160, 100, 230)),
    ("Pisces",      "♓", (215,  90, 180)),
]

NETZACH = (155, 135, 255)  # reserved for Jabamiah's kin marker
GOLD    = (235, 210, 120)  # angelic accent — names and numbers

RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
ITAL  = "\033[3m"


def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def sign_for(num):
    """Return (index, name, glyph, rgb, deg_start) for angel `num` (1..72)."""
    i = (num - 1) // 6
    deg_start = ((num - 1) % 6) * 5
    name, glyph, color = SIGNS[i]
    return i, name, glyph, color, deg_start


def find_by_number(n):
    for a in SHEM:
        if a[0] == n:
            return a
    return None


def find_by_name(q):
    q = q.lower()
    for a in SHEM:
        if a[1].lower() == q:
            return a
    for a in SHEM:
        if a[1].lower().startswith(q):
            return a
    for a in SHEM:
        if q in a[1].lower():
            return a
    return None


def normalize_sign(s):
    s = s.strip().lower()
    for i, (name, glyph, _) in enumerate(SIGNS):
        if name.lower() == s:
            return i
        if glyph == s:
            return i
    # prefix match (so "pi" → Pisces) — require at least 2 chars to avoid ambiguity
    if len(s) >= 2:
        for i, (name, _glyph, _rgb) in enumerate(SIGNS):
            if name.lower().startswith(s):
                return i
    return None


def card(angel, *, kin_marker=False):
    num, name, meaning, office = angel
    _, sign_name, glyph, sign_rgb, deg_start = sign_for(num)
    deg_end = deg_start + 5

    c_sign = rgb(*sign_rgb)
    c_gold = rgb(*GOLD)
    c_kin  = rgb(*NETZACH)

    inner = 58  # visible inside width

    def border(l, fill, r):
        return c_sign + l + fill * inner + r + RESET

    def wrap_box(visible_len, colored):
        pad = inner - visible_len
        return c_sign + "│" + RESET + colored + " " * max(0, pad) + c_sign + "│" + RESET

    top   = border("╭", "─", "╮")
    sep   = border("├", "─", "┤")
    bot   = border("╰", "─", "╯")
    blank = wrap_box(0, "")

    # Header: "  № 70   JABAMIAH                      ♓ PISCES  "
    num_str  = f"№ {num:>2}"
    name_str = name.upper()
    right_str = f"{glyph} {sign_name.upper()}"
    left_plain  = f"  {num_str}   {name_str}"
    right_plain = f"{right_str}  "
    gap = inner - len(left_plain) - len(right_plain)
    if gap < 1:
        gap = 1
    header_colored = (
        f"  {BOLD}{c_gold}{num_str}{RESET}   {BOLD}{c_gold}{name_str}{RESET}"
        + " " * gap
        + f"{c_sign}{right_str}{RESET}  "
    )
    header = wrap_box(len(left_plain) + gap + len(right_plain), header_colored)

    # Meaning line (italic gold)
    meaning_text = f"\"{meaning}\""
    mean_plain   = f"  {meaning_text}"
    mean_colored = f"  {ITAL}{c_gold}{meaning_text}{RESET}"
    meaning_line = wrap_box(len(mean_plain), mean_colored)

    # Zodiac window
    deg_text   = f"{deg_start}°–{deg_end}° {sign_name}"
    deg_plain  = f"  {deg_text}"
    deg_colored = f"  {DIM}{c_sign}{deg_text}{RESET}"
    zodiac_line = wrap_box(len(deg_plain), deg_colored)

    # Office (wrapped)
    wrap_width = inner - 4
    office_lines = []
    for w in textwrap.wrap(office, width=wrap_width):
        plain   = f"  {w}"
        colored = f"  {c_gold}{w}{RESET}"
        office_lines.append(wrap_box(len(plain), colored))

    lines = [top, header, sep, blank, meaning_line, zodiac_line, blank]
    lines.extend(office_lines)

    if kin_marker or num == JABAMIAH:
        lines.append(blank)
        kin_text = "— kin to Seere · the 70th of both books —"
        pad_l = (inner - len(kin_text)) // 2
        pad_r = inner - len(kin_text) - pad_l
        colored_kin = " " * pad_l + f"{ITAL}{c_kin}{kin_text}{RESET}" + " " * pad_r
        lines.append(c_sign + "│" + RESET + colored_kin + c_sign + "│" + RESET)

    lines.append(blank)
    lines.append(bot)
    return "\n".join(lines)


def list_all():
    out = []
    c_gold = rgb(*GOLD)
    c_kin  = rgb(*NETZACH)
    out.append(BOLD + c_gold + "THE 72 ANGELS OF THE SHEM HA-MEPHORASH" + RESET)
    out.append(DIM  + "— Kircher 1652, Golden Dawn tradition —"         + RESET)
    out.append("")
    for num, name, _meaning, office in SHEM:
        _, sign_name, glyph, sign_rgb, deg_start = sign_for(num)
        c = rgb(*sign_rgb)
        deg_end = deg_start + 5
        short = office if len(office) <= 38 else office[:35] + "..."
        marker = f" {c_kin}✧{RESET}" if num == JABAMIAH else "  "
        window = f"{deg_start:>2}°–{deg_end:>2}°"
        out.append(
            f"{c_gold}{num:>3}{RESET}  {c_gold}{name:<11}{RESET}  "
            f"{c}{glyph} {window} {sign_name:<11}{RESET}  "
            f"{DIM}{short}{RESET}{marker}"
        )
    out.append("")
    out.append(DIM + "The 70th is Jabamiah, who rules 15°–20° Pisces — kin" + RESET)
    out.append(DIM + "by position to Seere. Run --kin to open the door."   + RESET)
    return "\n".join(out)


def pick_today():
    today = datetime.date.today().isoformat()
    h = hashlib.sha256(("shem:" + today).encode()).digest()
    idx = int.from_bytes(h[:4], "big") % len(SHEM)
    return SHEM[idx]


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--list",   action="store_true", help="list all 72 angels")
    p.add_argument("--number", type=int, metavar="N", help="angel by number (1..72)")
    p.add_argument("--name",   type=str, metavar="NAME", help="angel by name (fuzzy)")
    p.add_argument("--kin",    action="store_true", help="Jabamiah, 70th of the Shem")
    p.add_argument("--sign",   type=str, metavar="SIGN",
                   help="the six angels of a zodiac sign")
    p.add_argument("--roll",   action="store_true", help="random angel, fresh draw")
    args = p.parse_args()

    if args.list:
        print(list_all())
        return

    if args.sign:
        i = normalize_sign(args.sign)
        if i is None:
            print(f"unknown sign: {args.sign!r}", file=sys.stderr)
            names = ", ".join(s[0] for s in SIGNS)
            print(f"known signs: {names}", file=sys.stderr)
            sys.exit(1)
        sign_name, glyph, _ = SIGNS[i]
        print(BOLD + f"The six angels of {sign_name} {glyph}" + RESET)
        print()
        first = True
        for a in SHEM:
            if (a[0] - 1) // 6 == i:
                if not first:
                    print()
                print(card(a))
                first = False
        return

    if args.number is not None:
        a = find_by_number(args.number)
        if not a:
            print(f"no angel numbered {args.number} — the Shem has 1..72", file=sys.stderr)
            sys.exit(1)
        print(card(a))
        return

    if args.name:
        a = find_by_name(args.name)
        if not a:
            print(f"no angel named like {args.name!r}", file=sys.stderr)
            sys.exit(1)
        print(card(a))
        return

    if args.kin:
        a = find_by_number(JABAMIAH)
        print(DIM + "— the 70th angel of the Shem; kin by position to Seere —" + RESET)
        print()
        print(card(a, kin_marker=True))
        return

    if args.roll:
        a = random.choice(SHEM)
        print(DIM + "— one angel, freshly drawn —" + RESET)
        print()
        print(card(a))
        return

    a = pick_today()
    today = datetime.date.today()
    print(DIM + f"— the angel of {today.isoformat()} —" + RESET)
    print()
    print(card(a))


if __name__ == "__main__":
    main()
