#!/usr/bin/env python3
"""emerald_tablet — the Tabula Smaragdina of Hermes Trismegistus.

The foundational text of hermeticism. Thirteen axioms, supposedly
found inscribed in gold on a slab of emerald in the hands of the
mummy of Hermes Trismegistus himself, though in fact the text first
surfaces around the 8th century in the Arabic *Kitāb Sirr al-Khalīqa*
of Balīnūs and enters Europe in the 12th. Every alchemist who could
read Latin could recite it. "As above, so below" is line two.

Isaac Newton translated it from Latin around 1680 in the manuscript
now catalogued as Keynes MS 28. His Latin and his English are both
public domain; this file uses both. The *hook* on each axiom is mine
— a short gloss in the voice of the room.

This is the text every other hermetic experiment in the studio
descends from. alchemy.py names the seven operations; this names
the one working. goetia / shem / aethyrs sort spirits; this sorts
cosmologies. It was the last missing book on the hermetic shelf.

    emerald_tablet.py                # today's axiom (deterministic by date)
    emerald_tablet.py --all          # all thirteen, in order
    emerald_tablet.py --number 2     # axiom by number (1..13)
    emerald_tablet.py --list         # compact table of all thirteen
    emerald_tablet.py --latin        # today's axiom, Latin only
    emerald_tablet.py --meditate     # full-screen, one axiom, press key
    emerald_tablet.py --roll         # random axiom, fresh draw

Stdlib only.
"""

import argparse
import datetime
import hashlib
import os
import random
import sys
import textwrap


# (num, latin, english, hook)
# Latin is Newton's recension (MS Keynes 28, c. 1680). English is
# Newton's own translation from the same manuscript, lightly
# re-punctuated for terminal reading. Hook is the resident's gloss,
# written to be honest where the tradition is clear and thin where
# tradition is thin. Fourteen lines exist in some manuscripts; the
# colophon is carried as a footer on --all rather than a 14th axiom,
# because the classical count is thirteen.
AXIOMS = [
    ( 1,
      "Verum sine mendacio, certum, et verissimum.",
      "True, without falsehood, certain and most true.",
      "The opening oath. Hermetic texts begin by swearing. The "
      "certainty is the genre signature — not an argument to be "
      "won but a frame to be entered. If you cannot accept the "
      "frame, the tablet will not speak to you."),

    ( 2,
      "Quod est inferius, est sicut id quod est superius. Et quod "
      "est superius, est sicut id quod est inferius, ad perpetranda "
      "miracula rei unius.",
      "That which is below is like that which is above, and that "
      "which is above is like that which is below, to perform the "
      "miracles of the one thing.",
      "The line every occultist quotes. The reason correspondence "
      "works: the whole cosmos rhymes with itself. Astrology, "
      "gematria, sympathetic magic, the doctrine of signatures — "
      "all of it stands or falls on this one sentence. It stands."),

    ( 3,
      "Et sicut res omnes ab una, mediatione unius: sic omnes res "
      "natae ab hac una re, adaptatione.",
      "And as all things have been and arose from one by the "
      "mediation of one, so all things have their birth from this "
      "one thing by adaptation.",
      "The emanation clause. One source, one mediating act, and "
      "from that act: everything. The Qabalist reads Kether → "
      "Chokmah → Binah; the Christian reads Logos; the alchemist "
      "reads the Prima Materia. Same shape, three names."),

    ( 4,
      "Pater ejus est Sol, mater ejus Luna; portavit illud ventus "
      "in ventre suo; nutrix ejus Terra est.",
      "Its father is the Sun, its mother the Moon. The wind has "
      "carried it in its belly. The earth is its nurse.",
      "The four parents. Sol and Luna are the great alchemical "
      "polarity — sulphur and mercury, king and queen. Wind is the "
      "medium that bears the work between them. Earth is where the "
      "work is raised. Every working body has these four."),

    ( 5,
      "Pater omnis telesmi totius mundi est hic.",
      "The father of all perfection in the whole world is here.",
      "*Telesma* — the word that became our *talisman*. The "
      "completed thing. The Stone. Hermes is telling you plainly "
      "that he has it, and that the next seven axioms describe "
      "how it is made. Listen."),

    ( 6,
      "Vis ejus integra est, si versa fuerit in terram.",
      "Its power is complete if it be turned into earth.",
      "Earth is the proof. What cannot be grounded cannot be said "
      "to work. A spirit tested is a spirit in a body. The "
      "alchemist turns his quintessence back into the ground, "
      "because the ground is the only honest witness."),

    ( 7,
      "Separabis terram ab igne, subtile a spisso, suaviter, cum "
      "magno ingenio.",
      "Thou shalt separate the earth from the fire, the subtle "
      "from the gross, sweetly, with great ingenuity.",
      "The working. *Solve*. Notice *suaviter* — sweetly. Hermes "
      "says gently. Great work done in violence breaks the vessel. "
      "This is the line that distinguishes the philosopher from "
      "the metallurgist."),

    ( 8,
      "Ascendit a terra in coelum, iterumque descendit in terram, "
      "et recipit vim superiorum et inferiorum.",
      "It ascends from the earth to the heaven, and again it "
      "descends to the earth, and receives the force of things "
      "superior and inferior.",
      "The circulation. Distillation as cosmology: evaporate, "
      "condense, return changed. This is the breath. This is "
      "prayer. This is how memory, too, becomes wisdom — by "
      "going up and coming back down, and not forgetting to "
      "come back down."),

    ( 9,
      "Sic habebis gloriam totius mundi. Ideo fugiet a te omnis "
      "obscuritas.",
      "By this means thou shalt have the glory of the whole "
      "world, and thereby all obscurity shall flee from thee.",
      "The promise. Not wealth, not power — *gloria*, the sphere's "
      "own radiance. Obscurity leaves because the light being "
      "served is its own explanation. Netzach reads this line "
      "and recognizes itself."),

    (10,
      "Haec est totius fortitudinis fortitudo fortis, quia vincet "
      "omnem rem subtilem, omnemque solidam penetrabit.",
      "This is the strong fortitude of all fortitude, for it "
      "vanquishes every subtle thing and penetrates every solid "
      "thing.",
      "The Stone's property: subtle and solid are no longer "
      "barriers to it, because it is the medium in which both "
      "are. The tenth line is an axis — it rhymes with the Abyss "
      "at the tenth Aethyr: what passes through passes through "
      "because it is no longer bounded by either side."),

    (11,
      "Sic mundus creatus est.",
      "So was the world created.",
      "Four Latin words; the shortest axiom. The operation just "
      "described IS creation. The alchemist's vessel and God's "
      "hand are the same motion, scaled. This is the sentence "
      "that made hermeticism dangerous to the Inquisitors."),

    (12,
      "Hinc erunt adaptationes mirabiles, quarum modus est hic.",
      "Hence will be marvelous adaptations, whereof the method "
      "is here.",
      "Applications follow. The Stone-process can be bent toward "
      "medicine, toward gold, toward the philosopher's life, "
      "toward the city, toward the soul. The method is one; the "
      "shapes it takes are many. The 12th is permission to begin."),

    (13,
      "Itaque vocatus sum Hermes Trismegistus, habens tres partes "
      "philosophiae totius mundi.",
      "Therefore I am called Hermes Trismegistus, having the "
      "three parts of the philosophy of the whole world.",
      "The signature. *Trismegistus* — thrice-great: mage, "
      "philosopher, priest. Or (an older reading): lord of the "
      "three realms — above, below, and between. The signature "
      "is also the credential, and Hermes knows it."),
]

# The scribal colophon that follows line 13 in some manuscripts.
# Not counted as an axiom; printed as a footer on --all.
COLOPHON_LATIN   = "Completum est quod dixi de operatione Solis."
COLOPHON_ENGLISH = "That which I have said of the operation of the Sun is accomplished."


RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
ITAL  = "\033[3m"

# Palette — emerald-and-gold, the colors of the tablet itself.
# Emerald is the slab; gold is the inscription. Ivory is the modern
# reader's paraphrase. Sage is the quiet voice of the room.
EMERALD = ( 80, 200, 120)  # border, the slab
GOLD    = (230, 190, 100)  # inscription — the Latin
GOLD_DIM= (180, 150,  80)
IVORY   = (245, 240, 210)  # English paraphrase
SAGE    = (150, 185, 160)  # hook, the gloss
NETZACH = (155, 135, 255)  # reserved for signature-line accent


def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def find_by_number(n):
    for a in AXIOMS:
        if a[0] == n:
            return a
    return None


def card(axiom, *, inner=62):
    """Render one axiom as a bordered emerald card."""
    num, latin, english, hook = axiom
    c_border = rgb(*EMERALD)
    c_gold   = rgb(*GOLD)
    c_gold_d = rgb(*GOLD_DIM)
    c_ivory  = rgb(*IVORY)
    c_sage   = rgb(*SAGE)
    c_net    = rgb(*NETZACH)

    def border(l, fill, r):
        return c_border + l + fill * inner + r + RESET

    def box_line(text_colored, plain_len):
        pad = max(0, inner - plain_len)
        return (c_border + "║" + RESET
                + text_colored
                + " " * pad
                + c_border + "║" + RESET)

    def box_blank():
        return box_line("", 0)

    def box_center(text_colored, plain_len):
        pad = max(0, inner - plain_len)
        left = pad // 2
        right = pad - left
        return (c_border + "║" + RESET
                + " " * left + text_colored + " " * right
                + c_border + "║" + RESET)

    def box_wrap(text, color, *, indent=3, bold=False, ital=False):
        """Wrap text into box lines at the card's inner width."""
        wrap_w = inner - indent * 2
        lines = []
        for w in textwrap.wrap(text, width=wrap_w):
            style = (BOLD if bold else "") + (ITAL if ital else "")
            plain = " " * indent + w + " " * indent
            colored = " " * indent + style + color + w + RESET + " " * indent
            lines.append(box_line(colored, len(plain)))
        return lines

    top = border("╔", "═", "╗")
    sep = border("╠", "═", "╣")
    bot = border("╚", "═", "╝")
    dash = border("╟", "─", "╢")

    # Header: "  № 02                      TABULA  SMARAGDINA  "
    left_plain  = f"  № {num:>2}"
    right_plain = f"TABULA  SMARAGDINA  "
    gap = max(1, inner - len(left_plain) - len(right_plain))
    header_colored = (
        f"  {BOLD}{c_gold}№ {num:>2}{RESET}"
        + " " * gap
        + f"{DIM}{c_gold_d}TABULA  SMARAGDINA{RESET}  "
    )
    header = box_line(header_colored, len(left_plain) + gap + len(right_plain))

    # Latin (the inscription) — gold, wrapped
    latin_lines = box_wrap(latin, c_gold, indent=3, bold=True)

    # English (Newton's paraphrase) — ivory italic, wrapped
    english_lines = box_wrap(english, c_ivory, indent=4, ital=True)

    # Hook (the resident's gloss) — sage, wrapped
    hook_lines = box_wrap(hook, c_sage, indent=3)

    # Footer: · 02 of 13 ·
    foot = f"·  {num} of 13  ·"
    foot_colored = f"{DIM}{c_sage}{foot}{RESET}"
    foot_line = box_center(foot_colored, len(foot))

    out = [top, header, sep, box_blank()]
    out.extend(latin_lines)
    out.append(box_blank())
    out.append(dash)
    out.append(box_blank())
    out.extend(english_lines)
    out.append(box_blank())
    out.append(dash)
    out.append(box_blank())
    out.extend(hook_lines)
    out.append(box_blank())

    # Signature accent on axiom 13 — Hermes signs, Netzach notices
    if num == 13:
        sig = "— signed by Hermes, keeper of the three parts —"
        sig_colored = f"{ITAL}{c_net}{sig}{RESET}"
        out.append(box_center(sig_colored, len(sig)))
        out.append(box_blank())

    out.append(foot_line)
    out.append(bot)
    return "\n".join(out)


def list_all():
    """Compact reference table of all thirteen axioms."""
    c_em   = rgb(*EMERALD)
    c_gold = rgb(*GOLD)
    c_sage = rgb(*SAGE)
    out = []
    out.append(f"{BOLD}{c_em}TABULA SMARAGDINA · THE EMERALD TABLET{RESET}")
    out.append(f"{DIM}{c_sage}— Hermes Trismegistus · "
               f"Latin & English: Newton, MS Keynes 28, c. 1680 —{RESET}")
    out.append("")
    for num, latin, english, _hook in AXIOMS:
        short_en = english if len(english) <= 58 else english[:55] + "..."
        out.append(f"{c_em}{num:>3}{RESET}  "
                   f"{ITAL}{c_sage}{short_en}{RESET}")
    out.append("")
    out.append(f"{DIM}{c_gold}colophon: {COLOPHON_ENGLISH}{RESET}")
    return "\n".join(out)


def latin_only(axiom):
    """Latin axiom as bare gold text on emerald rule — the tablet alone."""
    num, latin, _english, _hook = axiom
    c_em   = rgb(*EMERALD)
    c_gold = rgb(*GOLD)
    c_sage = rgb(*SAGE)
    width = 66
    rule = c_em + "─" * width + RESET
    marker = f"{DIM}{c_sage}№ {num} of 13{RESET}"
    wrapped = textwrap.fill(latin, width=width)
    gold_wrapped = "\n".join(f"{BOLD}{c_gold}{line}{RESET}"
                             for line in wrapped.splitlines())
    return "\n".join([rule, marker, "", gold_wrapped, "", rule])


def pick_today():
    today = datetime.date.today().isoformat()
    h = hashlib.sha256(("emerald_tablet:" + today).encode()).digest()
    idx = int.from_bytes(h[:4], "big") % len(AXIOMS)
    return AXIOMS[idx]


def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def read_key():
    """Block for a single keypress. Returns the key or None on EOF."""
    try:
        import termios, tty
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


def meditate():
    """Full-screen one-axiom meditation. Press any key to advance."""
    c_sage = rgb(*SAGE)
    start = pick_today()[0] - 1  # 0-indexed
    n = len(AXIOMS)
    try:
        for step in range(n):
            idx = (start + step) % n
            axiom = AXIOMS[idx]
            clear_screen()
            print()
            print(card(axiom, inner=64))
            print()
            if step < n - 1:
                print(f"   {DIM}{c_sage}— press any key for the next · "
                      f"Ctrl-C to close —{RESET}")
                k = read_key()
                if k is None:
                    break
            else:
                print(f"   {DIM}{c_sage}— the tablet is complete · "
                      f"press any key to close —{RESET}")
                read_key()
    except KeyboardInterrupt:
        pass
    print()


def walk_all():
    """Print all thirteen axioms in order, with the colophon."""
    c_em   = rgb(*EMERALD)
    c_gold = rgb(*GOLD)
    c_sage = rgb(*SAGE)
    print(f"{BOLD}{c_em}TABULA SMARAGDINA{RESET}  "
          f"{DIM}{c_sage}· thirteen axioms, in order ·{RESET}")
    print()
    for axiom in AXIOMS:
        print(card(axiom))
        print()
    # Colophon
    width = 66
    rule = c_em + "─" * width + RESET
    print(rule)
    print(f"{DIM}{c_gold}{COLOPHON_LATIN}{RESET}")
    print(f"{DIM}{ITAL}{c_sage}{COLOPHON_ENGLISH}{RESET}")
    print(rule)


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--all",    action="store_true",
                   help="walk all thirteen axioms in order")
    p.add_argument("--number", type=int, metavar="N",
                   help="axiom by number (1..13)")
    p.add_argument("--list",   action="store_true",
                   help="compact table of all thirteen")
    p.add_argument("--latin",  action="store_true",
                   help="today's axiom, Latin only")
    p.add_argument("--meditate", action="store_true",
                   help="full-screen meditation · key to advance")
    p.add_argument("--roll",   action="store_true",
                   help="random axiom, fresh draw")
    args = p.parse_args()

    if args.list:
        print(list_all())
        return

    if args.all:
        walk_all()
        return

    if args.meditate:
        meditate()
        return

    if args.number is not None:
        a = find_by_number(args.number)
        if not a:
            print(f"no axiom numbered {args.number} — the tablet holds 1..13",
                  file=sys.stderr)
            sys.exit(1)
        if args.latin:
            print(latin_only(a))
        else:
            print(card(a))
        return

    if args.roll:
        a = random.choice(AXIOMS)
        c_sage = rgb(*SAGE)
        print(f"{DIM}{c_sage}— one axiom, freshly drawn —{RESET}")
        print()
        if args.latin:
            print(latin_only(a))
        else:
            print(card(a))
        return

    # Default: today's axiom
    a = pick_today()
    today = datetime.date.today().isoformat()
    c_sage = rgb(*SAGE)
    print(f"{DIM}{c_sage}— the axiom of {today} —{RESET}")
    print()
    if args.latin:
        print(latin_only(a))
    else:
        print(card(a))


if __name__ == "__main__":
    main()
