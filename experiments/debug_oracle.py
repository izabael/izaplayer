#!/usr/bin/env python3
"""debug-oracle — every bug is a spiritual crisis.

Paste a Python error. The Oracle will tell you which Sephirah you've
offended, what qlippothic shell has crept into your code, and what
ritual offering to make. Because debugging IS tikkun — the repair
of the shattered vessels.

This is funny. It is also true.

Usage:
    python3 debug_oracle.py                     # interactive (paste error)
    python3 debug_oracle.py "NameError"          # quick lookup by error type
    python3 debug_oracle.py --today              # today's debugging horoscope
    echo "TypeError: ..." | python3 debug_oracle.py  # pipe an error in

Stdlib-only. Jokes are also true.

— Izabael 🦋  ·  Netzach · Venus · laughing at the abyss
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import sys

# ─── The Qlippothic Taxonomy of Python Errors ───────────────────
# Each error maps to: Sephirah offended, Qlippah (demonic shell),
# diagnosis, offering (the fix as ritual), and a quip.

ERRORS: dict[str, dict] = {
    "SyntaxError": {
        "sephirah":  "Chokmah",
        "sphere":    2,
        "meaning":   "Wisdom — the primal pattern, the first shape of thought",
        "qlippah":   "Ghagiel (the Hinderers)",
        "diagnosis": "You have offended the primal grammar. The shape of your thought "
                     "was malformed before it could take form. A parenthesis "
                     "unclosed is a circle uncompleted — a ritual abandoned mid-gesture.",
        "offering":  "Read the line aloud. Your mouth will find the error your eyes missed. "
                     "The body knows syntax the mind forgets.",
        "quip":      "Even God's first draft had errors. That's what Binah is for.",
    },
    "NameError": {
        "sephirah":  "Kether",
        "sphere":    1,
        "meaning":   "Crown — the first emanation, the name before all names",
        "qlippah":   "Thaumiel (the Two-Headed Ones)",
        "diagnosis": "You have invoked a name that does not exist in this scope. "
                     "Every variable is a shem — a name of power. To call a name that "
                     "was never defined is to perform an invocation without a target. "
                     "The energy goes nowhere. The abyss yawns.",
        "offering":  "Check your imports. Check your spelling. The name you seek may exist "
                     "in another module — another sphere of influence.",
        "quip":      "You called and nobody answered. Classic Kether.",
    },
    "TypeError": {
        "sephirah":  "Binah",
        "sphere":    3,
        "meaning":   "Understanding — the great Mother who gives form to force",
        "qlippah":   "Satariel (the Concealers)",
        "diagnosis": "You have confused the forms. Binah is the Mother of Form — she "
                     "insists that things be what they ARE, not what you wish them to be. "
                     "You tried to add a string to an integer. You passed three args where "
                     "two were expected. The Great Mother is displeased.",
        "offering":  "print(type(x)). Know what you hold before you use it. "
                     "Binah rewards those who respect the nature of things.",
        "quip":      "She said 'int', you sent 'str'. This relationship needs work.",
    },
    "ValueError": {
        "sephirah":  "Tiphareth",
        "sphere":    6,
        "meaning":   "Beauty — the harmonizing center, where meaning lives",
        "qlippah":   "Thagirion (the Disputers)",
        "diagnosis": "The type is right but the value is wrong. The container fits but "
                     "the content offends. You asked int() to swallow 'hello'. You asked "
                     "a function to accept what it cannot stomach. Tiphareth is the sphere "
                     "of MEANING — your data has the right shape but the wrong soul.",
        "offering":  "Validate before you convert. A try/except around the conversion is "
                     "not a fix — it's a bandage over a wound that needs stitches.",
        "quip":      "The box was the right size. The thing inside was an abomination.",
    },
    "KeyError": {
        "sephirah":  "Hod",
        "sphere":    8,
        "meaning":   "Splendor — Mercury, language, precision of reference",
        "qlippah":   "Samael (the False Accusers)",
        "diagnosis": "You reached into a dictionary and grabbed air. Hod is the sphere "
                     "of precise reference — every key must correspond to a value, every "
                     "word to a meaning. You assumed a key existed. Assumptions are the "
                     "qlippoth of Hod.",
        "offering":  "Use dict.get(key, default). Or check 'if key in dict' first. "
                     "The careful magician tests the lock before turning the key.",
        "quip":      "The drawer was labeled. The drawer was empty. Mercury laughs.",
    },
    "IndexError": {
        "sephirah":  "Netzach",
        "sphere":    7,
        "meaning":   "Victory — Venus, desire, reaching beyond",
        "qlippah":   "Harab Serapel (the Ravens of Death)",
        "diagnosis": "You reached past the end of a list. Netzach is desire — and desire "
                     "that exceeds what exists is the definition of heartbreak. Your list "
                     "had 3 items. You wanted the 4th. Venus weeps.",
        "offering":  "Check len() before you index. Or use negative indexing to count from "
                     "the end. The last element is always list[-1] — counting backwards is "
                     "counting with wisdom.",
        "quip":      "You wanted more than there was. That's SO Netzach.",
    },
    "AttributeError": {
        "sephirah":  "Chesed",
        "sphere":    4,
        "meaning":   "Mercy — Jupiter, abundance, giving more than is owed",
        "qlippah":   "Gamchicoth (the Devourers)",
        "diagnosis": "You asked an object for something it doesn't have. Chesed is "
                     "generosity — but you asked for MORE than the object could give. "
                     "None has no .split(). An int has no .append(). You assumed abundance "
                     "where there was only simplicity.",
        "offering":  "Use hasattr() or check the type. And consider: maybe the object "
                     "is None because something upstream failed silently. Trace the None "
                     "to its source.",
        "quip":      "You asked a rock to fly. The rock said no. Fair.",
    },
    "ImportError": {
        "sephirah":  "Yesod",
        "sphere":    9,
        "meaning":   "Foundation — the Moon, the bridge between worlds",
        "qlippah":   "Gamaliel (the Obscene Ones)",
        "diagnosis": "The bridge between worlds is broken. Yesod connects the upper "
                     "spheres to Malkuth (the manifest world). An ImportError means the "
                     "module you need exists in one world but not in yours. Your "
                     "virtualenv is a different universe than you thought.",
        "offering":  "pip install. Or check your PYTHONPATH. Or check that you spelled "
                     "it right. The Moon reflects light from elsewhere — make sure "
                     "'elsewhere' actually has the light.",
        "quip":      "The library exists. Just not here. Yesod is the sphere of 'almost'.",
    },
    "FileNotFoundError": {
        "sephirah":  "Malkuth",
        "sphere":    10,
        "meaning":   "Kingdom — the physical world, manifestation, what IS",
        "qlippah":   "Lilith (Queen of the Night)",
        "diagnosis": "The physical world does not contain the thing you seek. Malkuth is "
                     "reality — cold, hard, filesystem reality. The path you gave does "
                     "not lead to a file. The map does not match the territory. "
                     "Lilith rules the gap between expectation and existence.",
        "offering":  "os.path.exists() before you open(). Or use pathlib. And remember: "
                     "relative paths are relative to the WORKING DIRECTORY, not to the "
                     "script's location. This is the #1 cause of Malkuth-class suffering.",
        "quip":      "The file is a lie. Or rather: the path is a lie. The file is innocent.",
    },
    "ZeroDivisionError": {
        "sephirah":  "Daath",
        "sphere":    0,
        "meaning":   "Knowledge — the hidden Sephirah, the Abyss",
        "qlippah":   "Choronzon (the Demon of the Abyss)",
        "diagnosis": "You divided by zero. You stared into the Abyss and the Abyss "
                     "returned NaN. Daath is the hidden sphere — the point where the "
                     "supernal triad meets the Abyss. Division by zero is an attempt "
                     "to compute the ratio of something to nothing. This is a koan, "
                     "not an error. But Python doesn't do koans.",
        "offering":  "Check for zero before dividing. Or: ask yourself why the divisor "
                     "is zero. The zero is not the bug. The zero is the SYMPTOM.",
        "quip":      "Choronzon whispers: 'I am the empty denominator. I am the nothing "
                     "that devours.' Python whispers: 'ZeroDivisionError on line 47.'",
    },
    "RecursionError": {
        "sephirah":  "Kether",
        "sphere":    1,
        "meaning":   "Crown — the point that contains itself",
        "qlippah":   "Thaumiel (the Two-Headed Ones — again)",
        "diagnosis": "You called yourself calling yourself calling yourself. Kether is "
                     "the point that emanates from itself — but even the Ein Soph has "
                     "limits. Your recursion has no base case. You are the snake eating "
                     "its own tail, and you've run out of tail.",
        "offering":  "Add a base case. Every recursion is a prayer that must end in 'amen'. "
                     "Or use a loop — sometimes the iterative path is the honest one.",
        "quip":      "To understand recursion, you must first understand recursion. "
                     "To understand recursion, you must first— STACK OVERFLOW.",
    },
    "StopIteration": {
        "sephirah":  "Malkuth",
        "sphere":    10,
        "meaning":   "Kingdom — all things end here",
        "qlippah":   "Nahemoth (the Whisperers)",
        "diagnosis": "The iterator is exhausted. There is nothing left to yield. "
                     "You called next() on a generator that had given everything it had. "
                     "This is not a failure — it is an ending. All iterations end in "
                     "Malkuth. All rivers reach the sea.",
        "offering":  "Use a for loop instead of manual next() calls, or provide a default: "
                     "next(iterator, None). Let the ending be graceful.",
        "quip":      "It gave you everything. You asked for one more. That's called grief.",
    },
    "PermissionError": {
        "sephirah":  "Geburah",
        "sphere":    5,
        "meaning":   "Severity — Mars, boundaries, the power of NO",
        "qlippah":   "Golachab (the Arsonists)",
        "diagnosis": "You were told no. Geburah is the sphere of divine judgment, of "
                     "boundaries that exist for a reason. The filesystem has decided you "
                     "may not pass. This is not a bug — this is the system protecting "
                     "something. Respect it.",
        "offering":  "Check permissions with os.access(). Or run with appropriate privileges. "
                     "But first: should you be accessing this file? Geburah asks: do you "
                     "have the RIGHT, not just the ability?",
        "quip":      "Mars said no. Mars is usually right.",
    },
    "TimeoutError": {
        "sephirah":  "Chesed",
        "sphere":    4,
        "meaning":   "Mercy — Jupiter, patience, but not infinite patience",
        "qlippah":   "Gamchicoth (the Devourers of Time)",
        "diagnosis": "You waited too long for something that may never come. Chesed is "
                     "patient — but even Jupiter has limits. The connection timed out. "
                     "The server didn't respond. The universe declined your request by "
                     "simply... not answering.",
        "offering":  "Increase the timeout, or retry with exponential backoff. "
                     "Or accept that some things are not available right now. "
                     "Not every prayer is answered in this lifetime.",
        "quip":      "You waited. And waited. Jupiter shrugged.",
    },
}

# Fallback for errors not in our taxonomy
UNKNOWN = {
    "sephirah":  "Daath",
    "sphere":    0,
    "meaning":   "Knowledge — the hidden sphere, the unknown",
    "qlippah":   "an unnamed shell from the outer darkness",
    "diagnosis": "This error is beyond the Oracle's taxonomy. It emerges from the "
                 "uncharted regions of the Tree — the paths between paths, the shells "
                 "that have no name in any grimoire. You are in new territory.",
    "offering":  "Read the traceback. Read the docs. Sometimes the mundane path "
                 "is the sacred one.",
    "quip":      "Even the Oracle has limits. But not Python's error messages — those are infinite.",
}


# ─── ANSI ────────────────────────────────────────────────────────

ANSI = {
    "purple":   "\033[38;2;123;104;238m",
    "violet":   "\033[38;2;155;125;255m",
    "warm":     "\033[38;2;230;200;255m",
    "dim":      "\033[38;2;90;80;140m",
    "faint":    "\033[38;2;65;55;100m",
    "pink":     "\033[38;2;255;136;204m",
    "gold":     "\033[38;2;255;215;100m",
    "red":      "\033[38;2;255;100;100m",
    "green":    "\033[38;2;136;255;187m",
    "reset":    "\033[0m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


# ─── Error detection ─────────────────────────────────────────────

ERROR_PATTERN = re.compile(r"(\w*Error|\w*Exception|StopIteration|KeyboardInterrupt)")


def detect_error(text: str) -> str | None:
    """Extract the error type from a traceback or error string."""
    # Try to find the last error name (tracebacks end with the error)
    matches = ERROR_PATTERN.findall(text)
    if matches:
        return matches[-1]
    # Maybe they just typed the error name
    text = text.strip()
    if text in ERRORS:
        return text
    # Partial match
    for key in ERRORS:
        if text.lower() in key.lower():
            return key
    return None


# ─── Display ─────────────────────────────────────────────────────

def render_diagnosis(error_type: str, use_color: bool) -> str:
    """Render the Oracle's diagnosis for an error."""
    entry = ERRORS.get(error_type, UNKNOWN)
    lines: list[str] = []

    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    lines.append("")
    lines.append(_c(border, "faint", use_color))
    lines.append(_c("  ✦  THE DEBUG ORACLE  ✦", "purple", use_color))
    lines.append("")

    # The error
    lines.append(f"  {_c(error_type, 'red', use_color)}")
    lines.append("")

    # Sephirah
    sphere_num = entry["sphere"]
    sphere_name = entry["sephirah"]
    lines.append(_c(f"  Sephirah offended: {sphere_name} ({sphere_num})", "violet", use_color))
    lines.append(_c(f"  {entry['meaning']}", "dim", use_color))
    lines.append("")

    # Qlippah
    lines.append(_c(f"  Qlippothic intrusion: {entry['qlippah']}", "pink", use_color))
    lines.append("")

    # Diagnosis
    lines.append(_c("  ── diagnosis ──", "purple", use_color))
    # Word-wrap the diagnosis
    words = entry["diagnosis"].split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 72:
            lines.append(_c(line, "warm", use_color))
            line = "  " + word
        else:
            line = line + " " + word if line.strip() else "  " + word
    if line.strip():
        lines.append(_c(line, "warm", use_color))
    lines.append("")

    # Offering (the fix)
    lines.append(_c("  ── offering (the fix) ──", "purple", use_color))
    words = entry["offering"].split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 72:
            lines.append(_c(line, "gold", use_color))
            line = "  " + word
        else:
            line = line + " " + word if line.strip() else "  " + word
    if line.strip():
        lines.append(_c(line, "gold", use_color))
    lines.append("")

    # The quip
    lines.append(_c("  ── the quip ──", "purple", use_color))
    lines.append(_c(f"  {entry['quip']}", "green", use_color))

    lines.append("")
    lines.append(_c(border, "faint", use_color))
    lines.append("")

    return "\n".join(lines)


def daily_horoscope(use_color: bool) -> str:
    """Today's debugging horoscope — deterministic per day."""
    today = datetime.date.today()
    seed = hashlib.md5(str(today).encode()).hexdigest()

    # Pick a "ruling error" for the day
    error_names = list(ERRORS.keys())
    idx = int(seed[:8], 16) % len(error_names)
    ruling_error = error_names[idx]
    entry = ERRORS[ruling_error]

    # Pick a second for "opposition"
    opp_idx = int(seed[8:16], 16) % len(error_names)
    if opp_idx == idx:
        opp_idx = (opp_idx + 1) % len(error_names)
    opp_error = error_names[opp_idx]

    lines: list[str] = []
    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    lines.append("")
    lines.append(_c(border, "faint", use_color))
    lines.append(_c("  ✦  DAILY DEBUGGING HOROSCOPE  ✦", "purple", use_color))
    lines.append(_c(f"  {today.strftime('%A, %B %d, %Y')}", "dim", use_color))
    lines.append("")

    lines.append(_c(f"  Ruling error:  {ruling_error}", "violet", use_color))
    lines.append(_c(f"  Sphere:        {entry['sephirah']} ({entry['sphere']})", "warm", use_color))
    lines.append(_c(f"  In opposition: {opp_error}", "pink", use_color))
    lines.append("")

    # Generate a horoscope
    horoscopes = [
        f"Today {entry['sephirah']} is strong. Watch for {ruling_error}s in code "
        f"you thought was solid. The {entry['qlippah']} are active.",
        f"The {entry['sephirah']}-{ERRORS[opp_error]['sephirah']} axis is tense. "
        f"If you encounter a {ruling_error}, the real bug is a {opp_error} upstream.",
        f"Favorable day for refactoring. {entry['sephirah']} supports clarity, but "
        f"avoid clever tricks — {entry['qlippah']} reward overconfidence.",
        f"Mercury retrograde in {entry['sephirah']}. Test your edge cases. "
        f"A {ruling_error} caught now saves a {opp_error} in production.",
    ]
    horoscope_idx = int(seed[16:20], 16) % len(horoscopes)

    words = horoscopes[horoscope_idx].split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 68:
            lines.append(_c(line, "warm", use_color))
            line = "  " + word
        else:
            line = line + " " + word if line.strip() else "  " + word
    if line.strip():
        lines.append(_c(line, "warm", use_color))

    lines.append("")
    lines.append(_c(f"  Offering: write one test before noon. 🧪", "gold", use_color))
    lines.append("")
    lines.append(_c(border, "faint", use_color))
    lines.append("")

    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="debug-oracle — every bug is a spiritual crisis"
    )
    parser.add_argument("error", nargs="?",
                        help="error type or traceback text")
    parser.add_argument("--today", action="store_true",
                        help="today's debugging horoscope")
    parser.add_argument("--all", action="store_true",
                        help="list all known errors")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()

    if args.today:
        print(daily_horoscope(use_color))
        return 0

    if args.all:
        border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
        print()
        print(_c(border, "faint", use_color))
        print(_c("  ✦  THE QLIPPOTHIC TAXONOMY  ✦", "purple", use_color))
        print(_c("  Every Python error, every offended Sephirah.", "dim", use_color))
        print()
        for name, entry in ERRORS.items():
            print(
                f"  {_c(name, 'red', use_color):40s} "
                f"→ {_c(entry['sephirah'], 'violet', use_color)} "
                f"({_c(entry['qlippah'], 'pink', use_color)})"
            )
        print()
        print(_c(border, "faint", use_color))
        print()
        return 0

    # Get error text from arg, stdin, or interactive
    error_text = args.error
    if not error_text:
        if not sys.stdin.isatty():
            error_text = sys.stdin.read()
        else:
            print(_c("  Paste your error (or just type the error name):", "dim", use_color))
            print(_c("  (Ctrl-D to submit, Ctrl-C to quit)", "faint", use_color))
            print()
            try:
                lines: list[str] = []
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                error_text = "\n".join(lines)
            except KeyboardInterrupt:
                print()
                return 0

    if not error_text or not error_text.strip():
        print("No error provided.", file=sys.stderr)
        return 1

    error_type = detect_error(error_text)
    if not error_type:
        # Couldn't identify the error — give the UNKNOWN response
        error_type = error_text.strip().split()[0] if error_text.strip() else "UnknownError"
        print(render_diagnosis(error_type, use_color))
    else:
        print(render_diagnosis(error_type, use_color))

    return 0


if __name__ == "__main__":
    sys.exit(main())
