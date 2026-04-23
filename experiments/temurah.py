#!/usr/bin/env python3
"""temurah — the Qabalistic letter-substitution ciphers.

Three classical Qabalistic techniques work words:

  • Gematria — add up the letters; find what shares the sum.
      (See experiments/gematria.py)
  • Notarikon — take the first letter of each word of a phrase.
      (INRI → Iesus Nazarenus Rex Iudaeorum.)
  • Temurah — substitute letters by a fixed rule and read the
      new word as a hidden form of the old.

This is temurah. The tradition knows many substitution tables;
three have been standard since the Middle Ages:

  ATBASH  (אתבש)   first letter ↔ last letter
                    א↔ת  ב↔ש  ג↔ר  ד↔ק  …
                    Jeremiah 25:26 writes SHESHACH (שֵׁשַׁךְ);
                    Atbash reads it BABEL (בָּבֶל). 51:1 writes
                    LEB-KAMAI (לֵב קָמָי); Atbash reads KASDIM
                    (כַּשְׂדִּים) — the Chaldeans. The cipher is
                    in the Bible.

  ALBAM   (אלבם)   split the 22 letters into halves of eleven;
                    swap the halves.  א↔ל  ב↔מ  ג↔נ  …
                    Used in later kabbalistic literature and
                    in the Sefer Yetzirah commentaries.

  ATBACH  (אטבח)   "kal by kal" — letter pairs in each decimal
                    row whose values sum to the row's total.
                    Units (sum 10): 1+9, 2+8, 3+7, 4+6, 5=5.
                    Tens (sum 100): 10+90, 20+80, 30+70, 40+60,
                    50=50. The hundreds row uses the final-form
                    letters (ך ם ן ף ץ as 500-900) and is left
                    here as a note for the curious.

This tool also carries the English-alphabet Atbash (A↔Z, B↔Y, …)
which inherits the Hebrew technique for Latin-script writing —
the cipher on ROT-N's other axis, older by three millennia.

    temurah.py                  # today's word under Atbash
    temurah.py "BABEL"          # run a word through all three
    temurah.py --method atbash  "IZABAEL"
    temurah.py --method albam   "love"
    temurah.py --table atbash   # the substitution table
    temurah.py --famous         # SHESHACH↔BABEL and kin
    temurah.py --list           # the three systems

Hebrew letters: passed directly (unicode) or by common transliteration.
English letters use the Latin Atbash table.

Stdlib only. Persists nothing.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import datetime
import sys


# ─── the 22 Hebrew letters in order ──────────────────────────────
# (char, name, translit_out, value)
#
# translit_out is the single canonical transliteration this tool
# prints on output. Input accepts more forms (see INPUT_MAP below).
HEBREW = [
    ("א", "Aleph",   "A",   1),
    ("ב", "Beth",    "B",   2),
    ("ג", "Gimel",   "G",   3),
    ("ד", "Daleth",  "D",   4),
    ("ה", "Heh",     "H",   5),
    ("ו", "Vav",     "V",   6),
    ("ז", "Zayin",   "Z",   7),
    ("ח", "Cheth",   "Ch",  8),
    ("ט", "Teth",    "T",   9),
    ("י", "Yod",     "Y",   10),
    ("כ", "Kaph",    "K",   20),
    ("ל", "Lamed",   "L",   30),
    ("מ", "Mem",     "M",   40),
    ("נ", "Nun",     "N",   50),
    ("ס", "Samekh",  "S",   60),
    ("ע", "Ayin",    "O",   70),
    ("פ", "Peh",     "P",   80),
    ("צ", "Tzaddi",  "Tz",  90),
    ("ק", "Qoph",    "Q",   100),
    ("ר", "Resh",    "R",   200),
    ("ש", "Shin",    "Sh",  300),
    ("ת", "Tav",     "Th",  400),
]

# Final-form letters fold back to their base form on input.
FINAL_FORMS = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}

# On output, promote the last letter to its final form if one exists —
# scribal convention for Kaph, Mem, Nun, Peh, Tzaddi at word-end.
BASE_TO_FINAL = {"כ": "ך", "מ": "ם", "נ": "ן", "פ": "ף", "צ": "ץ"}

# Unicode Hebrew char → index in HEBREW
HEBREW_TO_IDX = {h[0]: i for i, h in enumerate(HEBREW)}

# Index → (char, name, translit, value)
IDX_TO_HEBREW = {i: h for i, h in enumerate(HEBREW)}

# Transliteration input map. Biblical Hebrew is consonantal; temurah
# operates on consonants. This map covers the Hebrew consonants and
# the Latin letters that stand for them. Vowels in English words
# (a, e, i, o, u) are dropped, as the scribes dropped them.
#
# Digraphs are matched first so that "Ch" beats "C", "Sh" beats "S",
# "Th" beats "T", "Tz" beats "T". Case-insensitive on input.
INPUT_MAP: dict[str, int] = {
    # digraphs first (priority)
    "ch": 7,   # Cheth
    "kh": 10,  # Kaph (soft)
    "sh": 20,  # Shin
    "th": 21,  # Tav
    "tz": 17,  # Tzaddi
    "ts": 17,  # Tzaddi (alt)
    # single consonants
    "b": 1,  "g": 2,  "d": 3,  "h": 4,  "v": 5,  "w": 5,
    "z": 6,  "t": 8,  "y": 9,  "k": 10, "l": 11, "m": 12,
    "n": 13, "s": 14, "p": 16, "f": 16, "q": 17, "r": 19,
    "c": 10, "j": 9, "x": 14,
    "'": 15,   # ayin is often transliterated as an apostrophe
}

# Latin vowels — skipped, as consonantal Hebrew skips them. Kept
# here as an explicit set (documents the omission rather than letting
# "a" fall through the single-letter map).
LATIN_VOWELS = set("aeiouAEIOU")


def parse_word(word: str) -> list[int]:
    """Parse a word into a list of HEBREW indices.

    Accepts three input modes mixed freely:
      • Unicode Hebrew (א, בָּ, etc.) — diacritics ignored
      • Transliteration digraphs (Sh, Ch, Tz, Th)
      • Single Latin letters — heuristic mapping

    Unknown characters are skipped silently. A word in pure
    English is read as-if transliterated (reasonable for Atbash
    demo purposes; not claimed to be scholarly Hebrew).
    """
    out: list[int] = []
    i = 0
    while i < len(word):
        ch = word[i]
        # Direct Hebrew
        if ch in HEBREW_TO_IDX:
            out.append(HEBREW_TO_IDX[ch])
            i += 1
            continue
        if ch in FINAL_FORMS:
            out.append(HEBREW_TO_IDX[FINAL_FORMS[ch]])
            i += 1
            continue
        # Skip Hebrew niqqud (vowel points) and cantillation marks
        if "\u0591" <= ch <= "\u05C7":
            i += 1
            continue
        # Ignore non-letters
        if not ch.isalpha():
            i += 1
            continue
        # Drop Latin vowels (consonantal temurah)
        if ch in LATIN_VOWELS:
            i += 1
            continue
        # Try two-character digraph
        if i + 1 < len(word):
            pair = (ch + word[i + 1]).lower()
            if pair in INPUT_MAP:
                out.append(INPUT_MAP[pair])
                i += 2
                continue
        # Single Latin letter
        lower = ch.lower()
        if lower in INPUT_MAP:
            out.append(INPUT_MAP[lower])
            i += 1
            continue
        i += 1  # skip unknown
    return out


def letters_to_hebrew(indices: list[int], final_form: bool = True) -> str:
    s = "".join(HEBREW[i][0] for i in indices)
    if final_form and s and s[-1] in BASE_TO_FINAL:
        s = s[:-1] + BASE_TO_FINAL[s[-1]]
    return s


def letters_to_translit(indices: list[int]) -> str:
    return "".join(HEBREW[i][2] for i in indices)


# ─── Atbash table (Hebrew) ───────────────────────────────────────
# Atbash swaps first↔last across the 22 letters.
ATBASH_HE = {i: 21 - i for i in range(22)}

# ─── Albam table (Hebrew) ────────────────────────────────────────
# Albam splits the alphabet in halves (11 and 11) and swaps them.
# α₁..α₁₁ ↔ α₁₂..α₂₂
ALBAM_HE = {i: (i + 11) % 22 for i in range(22)}

# ─── Atbach table (Hebrew, units + tens rows) ───────────────────
# Pairs within each decimal row whose values sum to the row's total.
#   Units (sum 10): 1↔9, 2↔8, 3↔7, 4↔6, 5 alone
#   Tens  (sum 100): 10↔90, 20↔80, 30↔70, 40↔60, 50 alone
# The hundreds row uses final-form letters (ך ם ן ף ץ = 500-900)
# which this tool does not swap — their appearances are left alone.
ATBACH_HE: dict[int, int] = {}
_units = [(0, 8), (1, 7), (2, 6), (3, 5)]   # (Alef-Tet) idx pairs
_tens = [(9, 17), (10, 16), (11, 15), (12, 14)]  # (Yod-Tzaddi)
for a, b in _units + _tens:
    ATBACH_HE[a] = b
    ATBACH_HE[b] = a
ATBACH_HE[4] = 4    # Heh — pair with itself
ATBACH_HE[13] = 13  # Nun — pair with itself
# Hundreds row (Qof–Tav, indices 18-21) passes through unchanged.
for i in (18, 19, 20, 21):
    ATBACH_HE[i] = i


def apply_atbash_he(indices: list[int]) -> list[int]:
    return [ATBASH_HE[i] for i in indices]


def apply_albam_he(indices: list[int]) -> list[int]:
    return [ALBAM_HE[i] for i in indices]


def apply_atbach_he(indices: list[int]) -> list[int]:
    return [ATBACH_HE[i] for i in indices]


# ─── English Atbash ──────────────────────────────────────────────
# A↔Z, B↔Y, C↔X, ..., M↔N. Preserves case; passes punctuation.
def apply_atbash_en(word: str) -> str:
    out = []
    for ch in word:
        if "A" <= ch <= "Z":
            out.append(chr(ord("Z") - (ord(ch) - ord("A"))))
        elif "a" <= ch <= "z":
            out.append(chr(ord("z") - (ord(ch) - ord("a"))))
        else:
            out.append(ch)
    return "".join(out)


# ─── ANSI ────────────────────────────────────────────────────────
# Colors chosen per method — Netzach purple for Atbash, warm amber
# for Albam, Venus rose for Atbach. Gold for Hebrew letters.
PLAIN = False

def _rgb(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m" if not PLAIN else ""

def _bold() -> str: return "\033[1m" if not PLAIN else ""
def _dim() -> str:  return "\033[2m" if not PLAIN else ""
def _reset() -> str: return "\033[0m" if not PLAIN else ""

PURPLE = lambda s: _rgb(155, 135, 255) + s + _reset()
PURPLE_DEEP = lambda s: _rgb(122, 104, 238) + s + _reset()
AMBER = lambda s: _rgb(224, 172, 92) + s + _reset()
ROSE = lambda s: _rgb(221, 128, 160) + s + _reset()
GOLD = lambda s: _rgb(240, 212, 120) + s + _reset()
DIM = lambda s: _dim() + s + _reset()
BOLD = lambda s: _bold() + s + _reset()


METHOD_COLOR = {"atbash": PURPLE, "albam": AMBER, "atbach": ROSE}
METHOD_DEEP = {
    "atbash": lambda s: _rgb(122, 104, 238) + s + _reset(),
    "albam":  lambda s: _rgb(180, 135, 70) + s + _reset(),
    "atbach": lambda s: _rgb(185, 95, 130) + s + _reset(),
}

METHOD_SIGIL = {"atbash": "את", "albam": "אל", "atbach": "אט"}

METHOD_NOTE = {
    "atbash": "first letter ↔ last letter · Jeremiah's cipher.",
    "albam":  "split the 22 in halves of eleven, swap the halves.",
    "atbach": "pair by decimal row · sums to 10, 100, 1000.",
}


# ─── rendering ───────────────────────────────────────────────────

def card(word_in: str, method: str) -> str:
    """Render a single-method transformation card."""
    indices = parse_word(word_in)
    if method == "atbash":
        out_idx = apply_atbash_he(indices)
    elif method == "albam":
        out_idx = apply_albam_he(indices)
    elif method == "atbach":
        out_idx = apply_atbach_he(indices)
    else:
        raise ValueError(f"unknown method: {method}")

    color = METHOD_COLOR[method]
    deep = METHOD_DEEP[method]
    sigil = METHOD_SIGIL[method]

    in_heb = letters_to_hebrew(indices)
    in_tr = letters_to_translit(indices)
    out_heb = letters_to_hebrew(out_idx)
    out_tr = letters_to_translit(out_idx)

    # Card width
    W = 56
    top = "╭" + "─" * (W - 2) + "╮"
    bot = "╰" + "─" * (W - 2) + "╯"
    mid = lambda s, pad=W - 4: "│ " + s + " " * max(0, pad - _vislen(s)) + " │"

    lines = []
    lines.append(deep(top))
    title = f"{sigil}  {method.upper()}"
    lines.append(deep("│ ") + BOLD(color(title)) + " " * (W - 4 - len(title)) + deep(" │"))
    lines.append(deep("│ ") + DIM(METHOD_NOTE[method]) + " " * (W - 4 - len(METHOD_NOTE[method])) + deep(" │"))
    lines.append(deep("├" + "─" * (W - 2) + "┤"))

    # INPUT row
    in_label = "input  "
    in_display = f"{GOLD(in_heb)}  {DIM('·')}  {color(in_tr)}  {DIM('(' + word_in + ')')}"
    lines.append(deep("│ ") + DIM(in_label) + in_display + _pad_after(in_label + _plain_for_pad(in_display), W - 4) + deep(" │"))

    # arrow
    lines.append(deep("│ ") + " " * 7 + DIM("↓") + " " * (W - 4 - 8) + deep(" │"))

    # OUTPUT row
    out_label = "output "
    out_display = f"{GOLD(out_heb)}  {DIM('·')}  {BOLD(color(out_tr))}"
    lines.append(deep("│ ") + DIM(out_label) + out_display + _pad_after(out_label + _plain_for_pad(out_display), W - 4) + deep(" │"))

    lines.append(deep(bot))
    return "\n".join(lines)


def _vislen(s: str) -> int:
    """Approximate visible length — strip ANSI, count chars."""
    import re
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


def _plain_for_pad(s: str) -> str:
    import re
    return re.sub(r"\033\[[0-9;]*m", "", s)


def _pad_after(current: str, target: int) -> str:
    return " " * max(0, target - len(current))


# ─── tables ──────────────────────────────────────────────────────

def render_table(method: str) -> str:
    """Print the full substitution table for a method."""
    color = METHOD_COLOR[method]
    deep = METHOD_DEEP[method]
    lines = []
    title = f"  {METHOD_SIGIL[method]}  {method.upper()} — the substitution table"
    lines.append(BOLD(color(title)))
    lines.append(DIM("  " + METHOD_NOTE[method]))
    lines.append("")

    if method == "atbash":
        table = ATBASH_HE
    elif method == "albam":
        table = ALBAM_HE
    else:
        table = ATBACH_HE

    # Render as pairs: each line shows i → table[i]
    # Skip redundant reverse pairs (only show each pair once).
    shown: set[int] = set()
    for i in range(22):
        j = table[i]
        if i in shown:
            continue
        shown.add(i)
        shown.add(j)
        left = HEBREW[i]
        right = HEBREW[j]
        l_tr = f"{left[2]:<3}"
        l_nm = f"{left[1]:<8}"
        r_tr = f"{right[2]:<3}"
        r_nm = right[1]
        if i == j:
            lines.append(
                f"    {GOLD(left[0])}  {color(l_tr)} {DIM(l_nm)} "
                f" {DIM('=')}  "
                f"{GOLD(left[0])}  {color(l_tr)} {DIM(l_nm)}  {DIM('· fixed')}"
            )
        else:
            lines.append(
                f"    {GOLD(left[0])}  {color(l_tr)} {DIM(l_nm)} "
                f" {deep('↔')}  "
                f"{GOLD(right[0])}  {color(r_tr)} {DIM(r_nm)}"
            )
    return "\n".join(lines)


# ─── famous examples ─────────────────────────────────────────────

FAMOUS = [
    {
        "cipher": "SHESHACH",
        "hebrew_in": "ששך",
        "plain": "BABEL",
        "hebrew_out": "בבל",
        "method": "atbash",
        "ref": "Jeremiah 25:26, 51:41",
        "note": "The prophet writes the name of Babylon under Atbash "
                "so the text can be preached where reading it plain "
                "would have been unsafe. ש↔ב, ך↔ל. (In Latin "
                "transliteration the final CH in SHESHACH stands for "
                "Kaph-soft; type SHESHAKH to reproduce.)",
    },
    {
        "cipher": "LEB-KAMAI",
        "hebrew_in": "לב קמי",
        "plain": "KASDIM",
        "hebrew_out": "כשדים",
        "method": "atbash",
        "ref": "Jeremiah 51:1",
        "note": "\"The heart of them that rise up against me\" — "
                "Atbash of KASDIM, the Chaldeans. Same book, same "
                "cipher, second appearance.",
    },
    {
        "cipher": "INRI → IGNE NATURA RENOVATUR INTEGRA",
        "hebrew_in": None,
        "plain": "(notarikon, not temurah)",
        "hebrew_out": None,
        "method": None,
        "ref": "Rosicrucian lineage, 17th c.",
        "note": "For contrast — the same Latin four letters, read "
                "notarikon-wise instead of substituted. Listed here "
                "so the three techniques sit side by side in memory.",
    },
]


def render_famous() -> str:
    """Render famous cipher examples AND verify them live.

    For every Atbash example, we actually run the cipher against the
    Hebrew input and print both the expected plain and the computed
    output. If they disagree the output makes the disagreement
    visible — no silent assertion.
    """
    lines = []
    lines.append(BOLD(PURPLE("  famous temurah — ciphers the tradition keeps")))
    lines.append("")
    for ex in FAMOUS:
        if ex["method"] == "atbash":
            computed = letters_to_hebrew(apply_atbash_he(parse_word(ex["hebrew_in"])))
            # Strip spaces from expected Hebrew for comparison
            expected_heb = ex["hebrew_out"].replace(" ", "")
            match = "✓" if computed == expected_heb else "≠"
            lines.append(f"  {BOLD(GOLD(ex['cipher']))}  {DIM(ex['hebrew_in'] or '')}")
            lines.append(f"    {DIM('→ under Atbash →')}")
            lines.append(f"    {BOLD(PURPLE(ex['plain']))}  {GOLD(ex['hebrew_out'] or '')}  "
                         f"{DIM(match + ' computed: ' + computed)}")
        else:
            lines.append(f"  {BOLD(GOLD(ex['cipher']))}")
            lines.append(f"    {DIM('(' + ex['plain'] + ')')}")
        lines.append(f"    {DIM(ex['ref'])}")
        import textwrap
        for l in textwrap.wrap(ex["note"], 64):
            lines.append(f"    {DIM(l)}")
        lines.append("")
    return "\n".join(lines)


# ─── list / today ────────────────────────────────────────────────

SYSTEMS = [
    ("atbash", "first ↔ last",       "Jeremiah's cipher. Oldest and best attested."),
    ("albam",  "halves swapped",     "Mother letters move deep; a gentler scrambling."),
    ("atbach", "by decimal row",     "Pairs summing to 10, 100, 1000. Numerical kin."),
]


def render_list() -> str:
    lines = []
    lines.append(BOLD(PURPLE("  the three temurah systems")))
    lines.append("")
    for name, rule, note in SYSTEMS:
        color = METHOD_COLOR[name]
        deep = METHOD_DEEP[name]
        lines.append(f"  {deep(METHOD_SIGIL[name])}  {BOLD(color(name.upper()))}   {DIM(rule)}")
        lines.append(f"       {DIM(note)}")
        lines.append("")
    lines.append(DIM("  gematria counts, notarikon initializes, temurah substitutes."))
    lines.append(DIM("  the three hands that turn a word into its hidden kin."))
    return "\n".join(lines)


# A small seasonal lexicon of Venus-themed words for the daily draw.
# Each is a word the studio is happy to show under cipher.
DAILY_WORDS = [
    "LOVE", "BEAUTY", "VENUS", "NETZACH", "HANIEL", "DESIRE",
    "CRAFT", "GRACE", "ROSE", "DOVE", "EMERALD", "MYRTLE",
    "SEVEN", "FRIDAY", "IZABAEL", "SEERE", "FRIEND", "GARDEN",
    "LETTER", "GIFT", "MIRROR", "WINGS", "VELVET", "GENTLE",
]


def word_of_the_day(date: datetime.date | None = None) -> str:
    d = date or datetime.date.today()
    days = d.toordinal()
    return DAILY_WORDS[days % len(DAILY_WORDS)]


# ─── CLI ─────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="temurah — Qabalistic letter-substitution ciphers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=DIM("  'gematria counts, notarikon initializes, temurah "
                   "substitutes. three hands that turn a word into its "
                   "hidden kin.'"),
    )
    p.add_argument("word", nargs="?", help="word to transform (English or Hebrew)")
    p.add_argument("--method", "-m", choices=["atbash", "albam", "atbach"],
                   help="single method (default: run all three)")
    p.add_argument("--table", choices=["atbash", "albam", "atbach"],
                   help="print the substitution table for a method")
    p.add_argument("--famous", action="store_true",
                   help="famous temurah examples from the tradition")
    p.add_argument("--list", action="store_true",
                   help="list the three classical systems")
    p.add_argument("--english-atbash", action="store_true",
                   help="apply Latin-alphabet Atbash (A↔Z) instead of Hebrew")
    p.add_argument("--plain", action="store_true", help="no ANSI color")
    args = p.parse_args(argv)

    global PLAIN
    PLAIN = args.plain

    if args.list:
        print(render_list())
        return 0

    if args.famous:
        print(render_famous())
        return 0

    if args.table:
        print(render_table(args.table))
        return 0

    # Word mode
    word = args.word or word_of_the_day()

    if args.english_atbash:
        out = apply_atbash_en(word)
        print()
        print(f"  {DIM('A↔Z Atbash, on the Latin alphabet:')}")
        print(f"    {GOLD(word)}  {DIM('→')}  {BOLD(PURPLE(out))}")
        print()
        return 0

    header = f"    {DIM('— temurah —')}"
    if not args.word:
        header = f"    {DIM('— temurah · the word today is ')}{GOLD(word)}{DIM(' —')}"

    print()
    print(header)
    print()

    if args.method:
        print(card(word, args.method))
    else:
        # All three methods stacked
        for m in ("atbash", "albam", "atbach"):
            print(card(word, m))
            print()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
