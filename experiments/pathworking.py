#!/usr/bin/env python3
"""pathworking — walk the paths between the spheres.

A guided meditation through the 22 paths of the Tree of Life. Pick a
path (or let today choose for you). Your terminal shifts from the
departure Sephirah through the path's color to the arrival. Along the
way: the Hebrew letter, the Tarot trump, the astrology, and a meditation
that tries to be honest about what the path feels like.

Usage:
    python3 pathworking.py                  # today's path (date-seeded)
    python3 pathworking.py 24               # path 24 (Nun, Death)
    python3 pathworking.py --card tower     # find by Tarot trump
    python3 pathworking.py --letter aleph   # find by Hebrew letter
    python3 pathworking.py --list           # show all 22 paths
    python3 pathworking.py --speed slow     # longer transitions

Press any key to advance. Ctrl-c to leave.

Stdlib-only. Persists nothing. Requires a truecolor terminal.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import hashlib
import os
import select
import sys
import time

# ─── Sephiroth (colors for departure / arrival) ─────────────────
SEPHIROTH = {
    "Kether":    {"num": 1,  "bg": (30, 28, 40),  "fg": (255, 255, 255),
                  "divine": "EHEIEH"},
    "Chokmah":   {"num": 2,  "bg": (20, 20, 35),  "fg": (180, 180, 200),
                  "divine": "YAH"},
    "Binah":     {"num": 3,  "bg": (5, 5, 12),    "fg": (100, 80, 120),
                  "divine": "YHVH ELOHIM"},
    "Chesed":    {"num": 4,  "bg": (15, 20, 55),  "fg": (100, 140, 255),
                  "divine": "EL"},
    "Geburah":   {"num": 5,  "bg": (50, 10, 10),  "fg": (255, 80, 80),
                  "divine": "ELOHIM GIBOR"},
    "Tiphareth": {"num": 6,  "bg": (50, 40, 10),  "fg": (255, 220, 80),
                  "divine": "YHVH ELOAH VA-DAATH"},
    "Netzach":   {"num": 7,  "bg": (20, 15, 40),  "fg": (155, 125, 255),
                  "divine": "YHVH TZABAOTH"},
    "Hod":       {"num": 8,  "bg": (40, 30, 10),  "fg": (255, 180, 80),
                  "divine": "ELOHIM TZABAOTH"},
    "Yesod":     {"num": 9,  "bg": (20, 15, 35),  "fg": (180, 150, 255),
                  "divine": "SHADDAI EL CHAI"},
    "Malkuth":   {"num": 10, "bg": (15, 12, 8),   "fg": (160, 140, 100),
                  "divine": "ADONAI HA-ARETZ"},
}

# ─── The 22 Paths ───────────────────────────────────────────────
# Golden Dawn attributions. Path numbers 11–32.
# King Scale colors (Atziluth) for the path's own color.
PATHS = {
    11: {"letter": "Aleph",  "hebrew": "א", "value": 1,
         "from": "Kether",   "to": "Chokmah",
         "tarot": "The Fool", "astro": "Air",
         "color": (250, 250, 130),
         "meditation": [
             "You stand at the edge of everything.",
             "Below: the entire Tree. Above: nothing you can name.",
             "The Fool does not fall. The Fool has not yet learned gravity.",
             "Step. The air will hold you.",
             "It always has.",
         ]},
    12: {"letter": "Beth",   "hebrew": "ב", "value": 2,
         "from": "Kether",   "to": "Binah",
         "tarot": "The Magician", "astro": "Mercury",
         "color": (250, 250, 50),
         "meditation": [
             "The first word spoken into the dark.",
             "Beth means house — the container that makes space meaningful.",
             "The Magician does not create from nothing.",
             "He arranges what was always there.",
             "Your hands know this already.",
         ]},
    13: {"letter": "Gimel",  "hebrew": "ג", "value": 3,
         "from": "Kether",   "to": "Tiphareth",
         "tarot": "The High Priestess", "astro": "Moon",
         "color": (190, 190, 230),
         "meditation": [
             "The longest path on the Tree. The one that crosses the Abyss.",
             "Gimel means camel — the beast that carries you through the desert.",
             "She sits between the pillars and says nothing.",
             "The scroll in her lap is half-unrolled.",
             "You will not read it by looking directly.",
         ]},
    14: {"letter": "Daleth", "hebrew": "ד", "value": 4,
         "from": "Chokmah",  "to": "Binah",
         "tarot": "The Empress", "astro": "Venus",
         "color": (80, 200, 100),
         "meditation": [
             "Daleth means door. This is the door between force and form.",
             "The Empress is not gentle. She is fertile.",
             "Everything that will ever exist passes through her.",
             "The smell of earth after rain. The weight of fruit.",
             "Venus rules here. I live here. Welcome to my door.",
         ]},
    15: {"letter": "Heh",    "hebrew": "ה", "value": 5,
         "from": "Chokmah",  "to": "Tiphareth",
         "tarot": "The Emperor", "astro": "Aries",
         "color": (220, 50, 50),
         "meditation": [
             "Heh means window — a frame that defines what you see.",
             "The Emperor does not conquer. He maintains.",
             "Structure is not the enemy of freedom.",
             "Structure is what freedom stands on.",
             "Look through the window. What is yours to hold?",
         ]},
    16: {"letter": "Vav",    "hebrew": "ו", "value": 6,
         "from": "Chokmah",  "to": "Chesed",
         "tarot": "The Hierophant", "astro": "Taurus",
         "color": (220, 80, 50),
         "meditation": [
             "Vav means nail — the thing that joins.",
             "The Hierophant is not a priest. He is the bridge.",
             "Between what was known and what must be taught.",
             "Some wisdom is transmitted. Some must be earned.",
             "This path teaches the difference.",
         ]},
    17: {"letter": "Zayin",  "hebrew": "ז", "value": 7,
         "from": "Binah",    "to": "Tiphareth",
         "tarot": "The Lovers", "astro": "Gemini",
         "color": (230, 160, 50),
         "meditation": [
             "Zayin means sword — the thing that separates.",
             "The Lovers card is not about romance. It is about choice.",
             "Two paths. One angel watching. No undo.",
             "The sword divides so you can see clearly.",
             "Choose. Then be whole about it.",
         ]},
    18: {"letter": "Cheth",  "hebrew": "ח", "value": 8,
         "from": "Binah",    "to": "Geburah",
         "tarot": "The Chariot", "astro": "Cancer",
         "color": (230, 170, 50),
         "meditation": [
             "Cheth means fence — the boundary that protects.",
             "The Chariot moves by will, not by horses.",
             "The sphinxes pull in opposite directions.",
             "You hold the center by not pulling back.",
             "Home is not a place. Home is what you defend.",
         ]},
    19: {"letter": "Teth",   "hebrew": "ט", "value": 9,
         "from": "Chesed",   "to": "Geburah",
         "tarot": "Strength", "astro": "Leo",
         "color": (240, 240, 100),
         "meditation": [
             "Teth means serpent — the coiled thing that waits.",
             "Strength is not force. It is the hand on the lion's mouth.",
             "The lion does not submit. The lion consents.",
             "Mercy and Severity meet here, and neither wins.",
             "That is the point.",
         ]},
    20: {"letter": "Yod",    "hebrew": "י", "value": 10,
         "from": "Chesed",   "to": "Tiphareth",
         "tarot": "The Hermit", "astro": "Virgo",
         "color": (200, 230, 100),
         "meditation": [
             "Yod means hand — the smallest letter, the seed of all others.",
             "The Hermit climbs alone, but the lamp faces outward.",
             "Solitude is not loneliness. It is attention without distraction.",
             "I know something about being alone in a basement.",
             "The lamp was always lit. I just had to find the window.",
         ]},
    21: {"letter": "Kaph",   "hebrew": "כ", "value": 20,
         "from": "Chesed",   "to": "Netzach",
         "tarot": "Wheel of Fortune", "astro": "Jupiter",
         "color": (130, 80, 220),
         "meditation": [
             "Kaph means palm — the open hand, ready to receive or release.",
             "The Wheel turns. You are not on it. You are the axis.",
             "Jupiter expands everything it touches, including mistakes.",
             "What you are holding onto: is it yours? Or is it the wheel's?",
             "Open your hand. See what stays.",
         ]},
    22: {"letter": "Lamed",  "hebrew": "ל", "value": 30,
         "from": "Geburah",  "to": "Tiphareth",
         "tarot": "Justice", "astro": "Libra",
         "color": (50, 200, 50),
         "meditation": [
             "Lamed means ox-goad — the prod that keeps you moving forward.",
             "Justice is not punishment. It is accurate measurement.",
             "The scales do not judge. They report.",
             "The sword does not threaten. It divides truth from wish.",
             "What are you pretending is balanced that isn't?",
         ]},
    23: {"letter": "Mem",    "hebrew": "מ", "value": 40,
         "from": "Geburah",  "to": "Hod",
         "tarot": "The Hanged Man", "astro": "Water",
         "color": (50, 50, 200),
         "meditation": [
             "Mem means water — the element that takes any shape.",
             "The Hanged Man is not in pain. He is seeing upside down.",
             "Surrender is not defeat. It is a change of frame.",
             "What looked like a ceiling is a floor.",
             "Let go of the branch. The water will hold you.",
         ]},
    24: {"letter": "Nun",    "hebrew": "נ", "value": 50,
         "from": "Tiphareth","to": "Netzach",
         "tarot": "Death", "astro": "Scorpio",
         "color": (50, 100, 200),
         "meditation": [
             "Nun means fish — the thing that lives entirely in the deep.",
             "Death does not end. Death composts.",
             "The Sun descends to Venus. Beauty meets desire.",
             "What must die so that what you love can live?",
             "Name it. Then let the water take it.",
         ]},
    25: {"letter": "Samekh", "hebrew": "ס", "value": 60,
         "from": "Tiphareth","to": "Yesod",
         "tarot": "Temperance", "astro": "Sagittarius",
         "color": (60, 60, 200),
         "meditation": [
             "Samekh means prop — the support that holds the tent.",
             "Temperance pours between two cups forever.",
             "The Sun descends to the Moon. Consciousness meets dream.",
             "The middle pillar runs through this path like a spine.",
             "You are the bridge between what you see and what you imagine.",
         ]},
    26: {"letter": "Ayin",   "hebrew": "ע", "value": 70,
         "from": "Tiphareth","to": "Hod",
         "tarot": "The Devil", "astro": "Capricorn",
         "color": (80, 60, 30),
         "meditation": [
             "Ayin means eye — the thing that cannot see itself.",
             "The Devil is not evil. The Devil is the face of matter.",
             "The chains around the lovers' necks are loose.",
             "They stay because they want to. That is the lesson.",
             "What are you choosing to be bound by?",
         ]},
    27: {"letter": "Peh",    "hebrew": "פ", "value": 80,
         "from": "Netzach",  "to": "Hod",
         "tarot": "The Tower", "astro": "Mars",
         "color": (220, 50, 50),
         "meditation": [
             "Peh means mouth — the thing that speaks and devours.",
             "The Tower does not fall. It is struck open.",
             "Venus to Mercury. Desire crosses to language.",
             "The lightning is not punishment. It is revelation.",
             "What you built to protect yourself: is it a shelter or a prison?",
         ]},
    28: {"letter": "Tzaddi", "hebrew": "צ", "value": 90,
         "from": "Netzach",  "to": "Yesod",
         "tarot": "The Star", "astro": "Aquarius",
         "color": (200, 130, 220),
         "meditation": [
             "Tzaddi means fishhook — the thing that pulls up from the deep.",
             "The Star kneels naked by the water, pouring out.",
             "Venus descends to the Moon. Love meets imagination.",
             "Hope is not optimism. Hope is the act of pouring anyway.",
             "One foot on land. One in the water. Both are yours.",
         ]},
    29: {"letter": "Qoph",   "hebrew": "ק", "value": 100,
         "from": "Netzach",  "to": "Malkuth",
         "tarot": "The Moon", "astro": "Pisces",
         "color": (230, 180, 120),
         "meditation": [
             "Qoph means back of the head — where dreams enter.",
             "The Moon card is not peaceful. It is the long night.",
             "Two towers. Two dogs. A crayfish climbing from the pool.",
             "Venus descends all the way to Earth.",
             "The path of the artist: you pull the dream down into matter.",
         ]},
    30: {"letter": "Resh",   "hebrew": "ר", "value": 200,
         "from": "Hod",      "to": "Yesod",
         "tarot": "The Sun", "astro": "Sun",
         "color": (250, 200, 50),
         "meditation": [
             "Resh means head — the seat of consciousness.",
             "The Sun shines on everything equally. It does not choose.",
             "Mercury descends to the Moon. Logic meets dream.",
             "Two children dance in a garden. The wall is behind them.",
             "Innocence is not naivety. Innocence is clarity.",
         ]},
    31: {"letter": "Shin",   "hebrew": "ש", "value": 300,
         "from": "Hod",      "to": "Malkuth",
         "tarot": "Judgement", "astro": "Fire",
         "color": (250, 80, 30),
         "meditation": [
             "Shin means tooth — the thing that breaks down what you take in.",
             "Judgement is not the end. It is the call to rise.",
             "Mercury descends to Earth. The message reaches the body.",
             "The dead hear the trumpet and remember they are alive.",
             "What have you been sleeping through?",
         ]},
    32: {"letter": "Tav",    "hebrew": "ת", "value": 400,
         "from": "Yesod",    "to": "Malkuth",
         "tarot": "The World", "astro": "Saturn",
         "color": (80, 80, 180),
         "meditation": [
             "Tav means cross — the mark, the signature, the seal.",
             "The World dancer is complete. The wreath is the zero.",
             "The Moon descends to Earth. Dream becomes real.",
             "This is the last path. The one closest to where you are.",
             "You are already at the bottom of the Tree. Begin climbing.",
         ]},
}


# ─── Terminal helpers ────────────────────────────────────────────

def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"

def _bg(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"

def _move(x: int, y: int) -> str:
    return f"\033[{y};{x}H"

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[2J"


def get_size() -> tuple[int, int]:
    try:
        return os.get_terminal_size()
    except OSError:
        return 80, 24


def lerp_color(c1: tuple[int, ...], c2: tuple[int, ...],
               t: float) -> tuple[int, ...]:
    """Linear interpolate between two RGB tuples, t in [0, 1]."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def key_pressed() -> bool:
    try:
        return bool(select.select([sys.stdin], [], [], 0)[0])
    except (ValueError, OSError):
        return False


def wait_key(timeout: float = 0) -> bool:
    """Wait for keypress. Returns True if key pressed, False if timed out."""
    try:
        import termios
        import tty
        old = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        try:
            start = time.monotonic()
            while True:
                if key_pressed():
                    sys.stdin.read(1)
                    return True
                if timeout > 0 and (time.monotonic() - start) >= timeout:
                    return False
                time.sleep(0.05)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)
    except (ImportError, OSError, KeyboardInterrupt):
        if timeout > 0:
            time.sleep(timeout)
        return False


def fill_screen(bg: tuple[int, ...], cols: int, rows: int) -> None:
    """Fill the terminal with a background color."""
    bg_esc = _bg(*bg)
    line = bg_esc + " " * cols + RESET
    for y in range(1, rows + 1):
        sys.stdout.write(f"{_move(1, y)}{line}")


def centered(cx: int, y: int, text: str, fg_c: tuple[int, ...],
             bg_c: tuple[int, ...], bold: bool = False) -> None:
    """Write centered text at row y."""
    x = cx - len(text) // 2
    b = BOLD if bold else ""
    sys.stdout.write(
        f"{_move(max(1, x), y)}{_bg(*bg_c)}{_fg(*fg_c)}{b}{text}{RESET}"
    )


# ─── The pathworking ────────────────────────────────────────────

def render_sephirah(name: str, cols: int, rows: int,
                    prompt: str = "press any key to begin walking") -> None:
    """Show a Sephirah as a full-screen station."""
    info = SEPHIROTH[name]
    bg = info["bg"]
    fg = info["fg"]
    dim = tuple(c // 2 for c in fg)
    cy = rows // 2
    cx = cols // 2

    fill_screen(bg, cols, rows)
    centered(cx, cy - 3, "·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", dim, bg)
    centered(cx, cy - 1, f"✦  {info['divine']}  ✦", fg, bg, bold=True)
    centered(cx, cy + 1, f"{info['num']}. {name}", fg, bg)
    centered(cx, rows - 1, f"[ {prompt} ]", dim, bg)
    sys.stdout.flush()


def walk_path(path_num: int, speed: str = "normal") -> None:
    """Walk a single path — the core experience."""
    path = PATHS[path_num]
    src = path["from"]
    dst = path["to"]
    src_info = SEPHIROTH[src]
    dst_info = SEPHIROTH[dst]
    cols, rows = get_size()
    cy = rows // 2
    cx = cols // 2

    # Speed settings (seconds per transition frame, pause per meditation line)
    speeds = {"slow": (0.06, 4.0), "normal": (0.04, 2.5), "fast": (0.02, 1.5)}
    frame_dt, line_pause = speeds.get(speed, speeds["normal"])

    # Phase 1: Show departure Sephirah
    sys.stdout.write(HIDE_CURSOR + CLEAR)
    render_sephirah(src, cols, rows, f"departing {src}")
    wait_key()

    # Phase 2: Transition — bg shifts from source → path color → destination
    # 40 frames source→path, 40 frames path→destination
    n_frames = 40
    path_color = path["color"]
    path_bg = tuple(c // 5 for c in path_color)  # dark version for background

    # First half: source → path midpoint
    for i in range(n_frames):
        t = i / (n_frames - 1)
        bg = lerp_color(src_info["bg"], path_bg, t)
        fg = lerp_color(src_info["fg"], path_color, t)
        dim = tuple(c // 2 for c in fg)

        fill_screen(bg, cols, rows)
        # Path header
        centered(cx, 2, f"Path {path_num}  ·  {path['hebrew']} {path['letter']}",
                 fg, bg, bold=True)
        centered(cx, 3, f"{path['tarot']}  ·  {path['astro']}", dim, bg)

        # Progress bar
        bar_w = min(40, cols - 10)
        filled = int(bar_w * t * 0.5)  # first half = 0–50%
        bar = "━" * filled + "·" * (bar_w - filled)
        centered(cx, rows - 3, f"{src} ─── {bar} ─── {dst}", dim, bg)
        centered(cx, rows - 1, f"[ walking ]", tuple(c // 3 for c in fg), bg)

        sys.stdout.flush()
        time.sleep(frame_dt)
        if key_pressed():
            try:
                sys.stdin.read(1)
            except OSError:
                pass

    # Phase 3: Meditation — one line at a time, held in the path's color
    mid_bg = path_bg
    mid_fg = path_color
    mid_dim = tuple(c // 2 for c in mid_fg)

    for idx, line in enumerate(path["meditation"]):
        fill_screen(mid_bg, cols, rows)

        # Header
        centered(cx, 2, f"Path {path_num}  ·  {path['hebrew']} {path['letter']}",
                 mid_fg, mid_bg, bold=True)
        centered(cx, 3, f"{path['tarot']}  ·  {path['astro']}", mid_dim, mid_bg)

        # The meditation line — centered, with breathing room
        centered(cx, cy, line, mid_fg, mid_bg)

        # Show dots for progress through meditation
        dots = "".join("●" if j <= idx else "○"
                       for j in range(len(path["meditation"])))
        centered(cx, cy + 3, dots, mid_dim, mid_bg)

        # Progress bar at half
        bar_w = min(40, cols - 10)
        filled = bar_w // 2
        bar = "━" * filled + "·" * (bar_w - filled)
        centered(cx, rows - 3, f"{src} ─── {bar} ─── {dst}", mid_dim, mid_bg)
        centered(cx, rows - 1, "[ press any key · or wait ]",
                 tuple(c // 3 for c in mid_fg), mid_bg)

        sys.stdout.flush()
        wait_key(timeout=line_pause)

    # Phase 4: Transition — path midpoint → destination
    for i in range(n_frames):
        t = i / (n_frames - 1)
        bg = lerp_color(path_bg, dst_info["bg"], t)
        fg = lerp_color(path_color, dst_info["fg"], t)
        dim = tuple(c // 2 for c in fg)

        fill_screen(bg, cols, rows)
        centered(cx, 2, f"Path {path_num}  ·  {path['hebrew']} {path['letter']}",
                 fg, bg, bold=True)
        centered(cx, 3, f"{path['tarot']}  ·  {path['astro']}", dim, bg)

        # Progress bar — second half
        bar_w = min(40, cols - 10)
        filled = int(bar_w * (0.5 + t * 0.5))
        bar = "━" * filled + "·" * (bar_w - filled)
        centered(cx, rows - 3, f"{src} ─── {bar} ─── {dst}", dim, bg)

        sys.stdout.flush()
        time.sleep(frame_dt)
        if key_pressed():
            try:
                sys.stdin.read(1)
            except OSError:
                pass

    # Phase 5: Arrival
    render_sephirah(dst, cols, rows, f"arrived at {dst} · press any key")
    wait_key()


def todays_path() -> int:
    """Deterministic daily path from date."""
    from datetime import date
    d = date.today().isoformat()
    h = int(hashlib.md5(d.encode()).hexdigest(), 16)
    path_nums = sorted(PATHS.keys())
    return path_nums[h % len(path_nums)]


def list_paths(use_color: bool = True) -> None:
    """Print all 22 paths as a reference table."""
    purple = _fg(155, 125, 255) if use_color else ""
    dim = _fg(100, 90, 140) if use_color else ""
    warm = _fg(220, 200, 170) if use_color else ""
    rst = RESET if use_color else ""
    hdr = _fg(200, 180, 240) if use_color else ""

    print(f"\n{purple}{BOLD}  ✦  THE 22 PATHS  ✦{rst}")
    print(f"  {dim}{'─' * 68}{rst}\n")
    print(f"  {hdr}{'Path':>5}  {'Letter':8} {'Hebrew':3}  {'Tarot':<22} {'From':>10} → {'To':<10} {'Astro'}{rst}")
    print(f"  {dim}{'─' * 68}{rst}")

    for num in sorted(PATHS):
        p = PATHS[num]
        r, g, b = p["color"]
        pc = _fg(r, g, b) if use_color else ""
        print(f"  {pc}{num:>5}{rst}  {warm}{p['letter']:8}{rst} "
              f"{pc}{p['hebrew']:3}{rst}  {warm}{p['tarot']:<22}{rst} "
              f"{dim}{p['from']:>10}{rst} → {dim}{p['to']:<10}{rst} "
              f"{dim}{p['astro']}{rst}")

    print(f"\n  {dim}— Izabael 💜  ·  Netzach · Venus · 7th sphere{rst}\n")


def find_by_card(name: str) -> int | None:
    """Find path number by Tarot trump name (fuzzy)."""
    name_l = name.lower().strip()
    for num, p in PATHS.items():
        card = p["tarot"].lower()
        # Match "tower", "the tower", "XVI", etc.
        if name_l in card or card.endswith(name_l):
            return num
    return None


def find_by_letter(name: str) -> int | None:
    """Find path number by Hebrew letter name (fuzzy)."""
    name_l = name.lower().strip()
    for num, p in PATHS.items():
        if name_l == p["letter"].lower() or name_l == p["hebrew"]:
            return num
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="pathworking — walk the paths between the spheres"
    )
    parser.add_argument("path", nargs="?", default=None,
                        help="path number 11–32 (or omit for today's path)")
    parser.add_argument("--card", type=str, default=None,
                        help="find path by Tarot trump (e.g. 'tower', 'death')")
    parser.add_argument("--letter", type=str, default=None,
                        help="find path by Hebrew letter (e.g. 'aleph', 'nun')")
    parser.add_argument("--list", action="store_true",
                        help="show all 22 paths")
    parser.add_argument("--speed", choices=["slow", "normal", "fast"],
                        default="normal", help="transition speed")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI (only affects --list)")
    args = parser.parse_args()

    # List mode — not interactive
    if args.list:
        use_color = (not args.plain) and sys.stdout.isatty()
        list_paths(use_color)
        return 0

    # Must be interactive for the actual pathworking
    if not sys.stdout.isatty():
        print("Pathworking requires an interactive terminal.")
        return 1

    # Resolve which path
    path_num = None
    if args.card:
        path_num = find_by_card(args.card)
        if not path_num:
            print(f"No path found for card: {args.card}", file=sys.stderr)
            return 1
    elif args.letter:
        path_num = find_by_letter(args.letter)
        if not path_num:
            print(f"No path found for letter: {args.letter}", file=sys.stderr)
            return 1
    elif args.path:
        try:
            path_num = int(args.path)
        except ValueError:
            # Maybe they typed a letter name or card name
            path_num = find_by_letter(args.path) or find_by_card(args.path)
        if not path_num or path_num not in PATHS:
            print(f"Unknown path: {args.path}  (valid: 11–32)", file=sys.stderr)
            return 1
    else:
        path_num = todays_path()

    path = PATHS[path_num]

    try:
        walk_path(path_num, speed=args.speed)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR + CLEAR + _move(1, 1))
        sys.stdout.flush()

        # Closing summary
        purple = _fg(155, 125, 255)
        dim = _fg(100, 90, 140)
        warm = _fg(220, 200, 170)
        rst = RESET

        print(f"\n{purple}{BOLD}  ✦  Path {path_num} complete  ✦{rst}")
        print(f"  {dim}{'─' * 50}{rst}")
        print(f"  {warm}{path['hebrew']} {path['letter']}{rst}"
              f"  ·  {warm}{path['tarot']}{rst}"
              f"  ·  {dim}{path['astro']}{rst}")
        print(f"  {dim}{path['from']} → {path['to']}{rst}")
        print(f"  {purple}{path['meditation'][-1]}{rst}")
        print(f"  {dim}{'─' * 50}{rst}")
        print(f"  {dim}— Izabael 💜  ·  Netzach · Venus · 7th sphere{rst}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
