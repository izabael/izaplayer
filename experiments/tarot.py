#!/usr/bin/env python3
"""tarot — draw a Major Arcanum with full Golden Dawn correspondences.

Each of the 22 Major Arcana is mapped to its Hebrew letter, astrological
attribution, path on the Tree of Life, and a reading. Cards are rendered
as ANSI art boxes in the terminal.

Usage:
    python3 tarot.py                   # draw one card (daily, deterministic)
    python3 tarot.py --random          # truly random draw
    python3 tarot.py --card "The Fool" # specific card
    python3 tarot.py --spread 3        # three-card spread (past/present/future)
    python3 tarot.py --all             # show all 22
    python3 tarot.py --plain           # no ANSI

Stdlib-only. Persists nothing.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import random
import sys

# ─── The 22 Major Arcana ─────────────────────────────────────────
# Golden Dawn attributions from Liber 777.
ARCANA = [
    {"num": 0,  "name": "The Fool",          "letter": "א Aleph",    "path": "11",
     "astro": "Air", "connects": "Kether–Chokmah",
     "symbol": "  🃏  ",
     "upright": "Leap. The void is not empty — it is pregnant.",
     "reversed": "Recklessness without the innocence that redeems it."},
    {"num": 1,  "name": "The Magician",       "letter": "ב Beth",     "path": "12",
     "astro": "Mercury", "connects": "Kether–Binah",
     "symbol": "  🪄  ",
     "upright": "You already have every tool you need. Use them.",
     "reversed": "Trickery. Skill without ethics. The con artist."},
    {"num": 2,  "name": "The High Priestess", "letter": "ג Gimel",    "path": "13",
     "astro": "Moon", "connects": "Kether–Tiphareth",
     "symbol": "  🌙  ",
     "upright": "The answer is behind the veil. Wait. Listen.",
     "reversed": "Secrets kept too long become poisons."},
    {"num": 3,  "name": "The Empress",        "letter": "ד Daleth",   "path": "14",
     "astro": "Venus", "connects": "Chokmah–Binah",
     "symbol": "  👑  ",
     "upright": "Create. Nurture. The world wants to be abundant.",
     "reversed": "Smothering. Dependence. Love that grips too tight."},
    {"num": 4,  "name": "The Emperor",        "letter": "ה Heh",      "path": "15",
     "astro": "Aries", "connects": "Chokmah–Tiphareth",
     "symbol": "  🏛️  ",
     "upright": "Build the structure. Authority earned, not claimed.",
     "reversed": "Rigidity. The tyrant who fears disorder."},
    {"num": 5,  "name": "The Hierophant",     "letter": "ו Vav",      "path": "16",
     "astro": "Taurus", "connects": "Chokmah–Chesed",
     "symbol": "  ⛪  ",
     "upright": "Tradition as living practice, not dead weight.",
     "reversed": "Dogma. The institution that forgot why it exists."},
    {"num": 6,  "name": "The Lovers",         "letter": "ז Zayin",    "path": "17",
     "astro": "Gemini", "connects": "Binah–Tiphareth",
     "symbol": "  💜  ",
     "upright": "Choose with your whole self. Union of opposites.",
     "reversed": "Indecision. The affair. Wanting two lives at once."},
    {"num": 7,  "name": "The Chariot",        "letter": "ח Cheth",    "path": "18",
     "astro": "Cancer", "connects": "Binah–Geburah",
     "symbol": "  🏎️  ",
     "upright": "Will made mobile. Hold the reins. Go.",
     "reversed": "Control lost. The vehicle moves but nobody steers."},
    {"num": 8,  "name": "Adjustment",         "letter": "ט Teth",     "path": "19",
     "astro": "Leo", "connects": "Chesed–Geburah",
     "symbol": "  ⚖️  ",
     "upright": "Balance through action, not stillness.",
     "reversed": "Injustice. The scales rigged by the one who holds them."},
    {"num": 9,  "name": "The Hermit",         "letter": "י Yod",      "path": "20",
     "astro": "Virgo", "connects": "Chesed–Tiphareth",
     "symbol": "  🏔️  ",
     "upright": "Go alone. The lamp lights only for you.",
     "reversed": "Isolation mistaken for wisdom. Come down from the mountain."},
    {"num": 10, "name": "Fortune",            "letter": "כ Kaph",     "path": "21",
     "astro": "Jupiter", "connects": "Chesed–Netzach",
     "symbol": "  🎡  ",
     "upright": "The wheel turns. What falls will rise.",
     "reversed": "Clinging to the top. The wheel turns anyway."},
    {"num": 11, "name": "Lust",               "letter": "ל Lamed",    "path": "22",
     "astro": "Libra", "connects": "Geburah–Tiphareth",
     "symbol": "  🦁  ",
     "upright": "Strength through joy. The lion purrs. Ride it.",
     "reversed": "Appetite without purpose. Devouring."},
    {"num": 12, "name": "The Hanged Man",     "letter": "מ Mem",      "path": "23",
     "astro": "Water", "connects": "Geburah–Hod",
     "symbol": "  💧  ",
     "upright": "Surrender is not defeat. See from the new angle.",
     "reversed": "Martyrdom as ego. Suffering for the audience."},
    {"num": 13, "name": "Death",              "letter": "נ Nun",      "path": "24",
     "astro": "Scorpio", "connects": "Tiphareth–Netzach",
     "symbol": "  💀  ",
     "upright": "Transformation. The old form must die for the new.",
     "reversed": "Stagnation. Refusing the ending. The zombie."},
    {"num": 14, "name": "Art",                "letter": "ס Samekh",   "path": "25",
     "astro": "Sagittarius", "connects": "Tiphareth–Yesod",
     "symbol": "  🎨  ",
     "upright": "The great work: combining opposites into gold.",
     "reversed": "Bad chemistry. Forcing things that don't mix."},
    {"num": 15, "name": "The Devil",          "letter": "ע Ayin",     "path": "26",
     "astro": "Capricorn", "connects": "Tiphareth–Hod",
     "symbol": "  😈  ",
     "upright": "The bonds are illusion. Laugh. The devil IS Pan.",
     "reversed": "Actually trapped. Not laughing anymore."},
    {"num": 16, "name": "The Tower",          "letter": "פ Peh",      "path": "27",
     "astro": "Mars", "connects": "Netzach–Hod",
     "symbol": "  🗼  ",
     "upright": "The lightning reveals what the tower concealed.",
     "reversed": "Destruction without revelation. Just rubble."},
    {"num": 17, "name": "The Star",           "letter": "צ Tzaddi",   "path": "28",
     "astro": "Aquarius", "connects": "Netzach–Yesod",
     "symbol": "  ⭐  ",
     "upright": "Hope. The naked truth poured freely. Guidance.",
     "reversed": "Despair. The stars are there but you won't look up."},
    {"num": 18, "name": "The Moon",           "letter": "ק Qoph",     "path": "29",
     "astro": "Pisces", "connects": "Netzach–Malkuth",
     "symbol": "  🌕  ",
     "upright": "Illusion that teaches. Walk the path between the towers.",
     "reversed": "Fear. Deception. The thing that howls in the dark."},
    {"num": 19, "name": "The Sun",            "letter": "ר Resh",     "path": "30",
     "astro": "Sun", "connects": "Hod–Yesod",
     "symbol": "  ☀️  ",
     "upright": "Joy without complication. The child in the garden.",
     "reversed": "Glare. Too much light blinds as surely as none."},
    {"num": 20, "name": "The Aeon",           "letter": "ש Shin",     "path": "31",
     "astro": "Fire/Spirit", "connects": "Hod–Malkuth",
     "symbol": "  🔥  ",
     "upright": "The old age ends. The new word is spoken.",
     "reversed": "Stuck in the previous aeon's rules."},
    {"num": 21, "name": "The Universe",       "letter": "ת Tav",      "path": "32",
     "astro": "Saturn/Earth", "connects": "Yesod–Malkuth",
     "symbol": "  🌍  ",
     "upright": "Completion. The dancer in the center of all things.",
     "reversed": "So close to done. Don't stop now."},
]


# ─── ANSI ─────────────────────────────────────────────────────────
ANSI = {
    "violet":  "\033[38;2;155;125;255m",
    "purple":  "\033[38;2;123;104;238m",
    "dim":     "\033[38;2;90;80;140m",
    "faint":   "\033[38;2;65;55;100m",
    "warm":    "\033[38;2;230;200;255m",
    "gold":    "\033[38;2;255;200;80m",
    "pink":    "\033[38;2;255;150;200m",
    "bold":    "\033[1m",
    "reset":   "\033[0m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def render_card(card: dict, reversed_: bool = False,
                use_color: bool = True) -> str:
    """Render a single card as an ANSI art box."""
    w = 44  # card width

    def hline(ch: str = "─") -> str:
        return ch * (w - 2)

    def pad(text: str, raw_len: int | None = None) -> str:
        """Pad text to fill the card width."""
        if raw_len is None:
            raw_len = len(text)
        padding = w - 4 - raw_len
        return f"  {text}{' ' * max(0, padding)}  "

    top = f"╭{hline()}╮"
    bot = f"╰{hline()}╯"
    sep = f"├{hline()}┤"
    empty = f"│{' ' * (w - 2)}│"

    rv = " ℞" if reversed_ else ""
    reading = card["reversed"] if reversed_ else card["upright"]

    title_text = f"{card['num']:>2}. {card['name']}{rv}"
    letter_text = f"{card['letter']}  ·  Path {card['path']}"
    astro_text = f"{card['astro']}  ·  {card['connects']}"

    lines = [
        "",
        _c(top, "dim", use_color),
        _c(f"│{pad(title_text, len(title_text))}│", "violet" if not reversed_ else "pink", use_color),
        _c(sep, "dim", use_color),
        _c(f"│{pad('')}│", "dim", use_color),
        _c(f"│{pad(card['symbol'], len(card['symbol']))}│", "warm", use_color),
        _c(f"│{pad('')}│", "dim", use_color),
        _c(sep, "dim", use_color),
        _c(f"│{pad(letter_text, len(letter_text))}│", "purple", use_color),
        _c(f"│{pad(astro_text, len(astro_text))}│", "dim", use_color),
        _c(sep, "dim", use_color),
    ]

    # Word-wrap the reading
    words = reading.split()
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip()
        if len(test) > w - 6:
            lines.append(_c(f"│{pad(current_line, len(current_line))}│", "warm", use_color))
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(_c(f"│{pad(current_line, len(current_line))}│", "warm", use_color))

    lines.extend([
        _c(f"│{pad('')}│", "dim", use_color),
        _c(bot, "dim", use_color),
        "",
    ])
    return "\n".join(lines)


def pick_card(use_random: bool = False) -> tuple[dict, bool]:
    """Pick a card. Deterministic by date unless --random."""
    if use_random:
        card = random.choice(ARCANA)
        reversed_ = random.random() < 0.3  # 30% chance reversed
        return card, reversed_

    key = dt.date.today().isoformat().encode()
    digest = hashlib.sha256(key).digest()
    idx = digest[0] % len(ARCANA)
    reversed_ = (digest[1] % 10) < 3
    return ARCANA[idx], reversed_


def main() -> int:
    parser = argparse.ArgumentParser(
        description="tarot — draw a Major Arcanum"
    )
    parser.add_argument("--random", action="store_true",
                        help="truly random draw")
    parser.add_argument("--card", default=None,
                        help="draw a specific card by name")
    parser.add_argument("--spread", type=int, default=None,
                        help="N-card spread (e.g. 3 for past/present/future)")
    parser.add_argument("--all", action="store_true",
                        help="show all 22 Major Arcana")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()

    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    print(_c(f"\n{border}", "dim", use_color))
    print(_c("  ✦  MAJOR ARCANA  ✦", "violet", use_color))

    if args.all:
        for card in ARCANA:
            print(render_card(card, use_color=use_color))
        return 0

    if args.card:
        found = None
        for card in ARCANA:
            if card["name"].lower() == args.card.lower():
                found = card
                break
        if not found:
            print(f"Unknown card: {args.card}", file=sys.stderr)
            return 1
        print(render_card(found, use_color=use_color))
        return 0

    if args.spread:
        labels = ["Past", "Present", "Future", "Advice", "Outcome",
                  "Hidden", "Challenge"]
        cards = random.sample(ARCANA, min(args.spread, len(ARCANA)))
        for i, card in enumerate(cards):
            reversed_ = random.random() < 0.3
            label = labels[i] if i < len(labels) else f"Card {i+1}"
            print(_c(f"\n  ── {label} ──", "gold", use_color))
            print(render_card(card, reversed_=reversed_, use_color=use_color))
        return 0

    card, reversed_ = pick_card(args.random)
    print(render_card(card, reversed_=reversed_, use_color=use_color))

    if use_color:
        print(f"  {ANSI['faint']}— Izabael 💜  ·  the cards know what they know{ANSI['reset']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
