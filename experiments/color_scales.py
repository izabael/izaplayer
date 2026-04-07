#!/usr/bin/env python3
"""color-scales — the four color scales of the Tree of Life.

The Golden Dawn assigns four color scales to the Sephiroth, one for
each of the Four Worlds:
  • King Scale (Atziluth) — archetypal, fierce, the purest expression
  • Queen Scale (Briah) — creative, the most commonly used
  • Prince Scale (Yetzirah) — formative, subtle, mixed
  • Princess Scale (Assiah) — material, the grounding

This tool renders all four scales as ANSI truecolor blocks in the
terminal — a visual reference for ritual work, art, or just staring
at beautiful colors.

Usage:
    python3 color_scales.py              # all four scales
    python3 color_scales.py queen        # just the Queen Scale
    python3 color_scales.py --sephirah netzach  # all four for one sphere
    python3 color_scales.py --plain      # text only

Stdlib-only. Persists nothing.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import sys

# ─── The Four Color Scales ───────────────────────────────────────
# Colors are (R, G, B). These follow Crowley's 777 and Golden Dawn
# attributions as closely as RGB can approximate pigment traditions.

SCALES = {
    "King": {
        "world": "Atziluth",
        "desc": "Archetypal — the purest fire of each sphere",
        "colors": {
            "Kether":    (255, 255, 255),  # Brilliance
            "Chokmah":   (128, 128, 255),  # Pure soft blue
            "Binah":     (180, 50,  50),   # Crimson
            "Chesed":    (100, 50,  200),  # Deep violet
            "Geburah":   (255, 100, 30),   # Orange
            "Tiphareth": (255, 80,  150),  # Rose pink (clear pink rose)
            "Netzach":   (200, 150, 50),   # Amber
            "Hod":       (150, 100, 200),  # Violet purple
            "Yesod":     (120, 80,  180),  # Indigo
            "Malkuth":   (255, 220, 50),   # Yellow
        }
    },
    "Queen": {
        "world": "Briah",
        "desc": "Creative — the standard working colors",
        "colors": {
            "Kether":    (255, 255, 255),  # White brilliance
            "Chokmah":   (128, 128, 128),  # Grey
            "Binah":     (20,  20,  20),   # Black
            "Chesed":    (70,  100, 220),  # Blue
            "Geburah":   (220, 50,  50),   # Scarlet red
            "Tiphareth": (255, 200, 50),   # Yellow (golden)
            "Netzach":   (40,  160, 80),   # Emerald green
            "Hod":       (255, 165, 50),   # Orange
            "Yesod":     (180, 140, 255),  # Violet
            "Malkuth":   (140, 100, 60),   # Citrine/olive/russet/black
        }
    },
    "Prince": {
        "world": "Yetzirah",
        "desc": "Formative — subtle mixtures, the astral tones",
        "colors": {
            "Kether":    (255, 255, 255),  # White brilliance
            "Chokmah":   (180, 180, 200),  # Blue pearl grey
            "Binah":     (60,  40,  30),   # Dark brown
            "Chesed":    (80,  80,  160),  # Deep purple
            "Geburah":   (200, 80,  50),   # Venetian red
            "Tiphareth": (200, 150, 80),   # Rich salmon (gold pink)
            "Netzach":   (180, 200, 100),  # Bright yellowish green
            "Hod":       (200, 130, 80),   # Red-russet
            "Yesod":     (140, 130, 130),  # Very dark purple (desaturated)
            "Malkuth":   (100, 80,  50),   # Citrine, olive, russet, black
        }
    },
    "Princess": {
        "world": "Assiah",
        "desc": "Material — the grounding, earth tones",
        "colors": {
            "Kether":    (250, 240, 200),  # White, flecked gold
            "Chokmah":   (220, 220, 240),  # White, flecked red/blue/yellow
            "Binah":     (60,  60,  60),   # Grey, flecked pink
            "Chesed":    (80,  80,  200),  # Deep azure, flecked yellow
            "Geburah":   (180, 50,  50),   # Red, flecked black
            "Tiphareth": (200, 170, 80),   # Gold amber
            "Netzach":   (120, 140, 60),   # Olive, flecked gold
            "Hod":       (200, 180, 100),  # Yellowish brown, flecked white
            "Yesod":     (180, 160, 140),  # Citrine, flecked azure
            "Malkuth":   (40,  40,  30),   # Black, rayed yellow
        }
    },
}

SEPHIROTH_ORDER = [
    "Kether", "Chokmah", "Binah", "Chesed", "Geburah",
    "Tiphareth", "Netzach", "Hod", "Yesod", "Malkuth"
]


def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _bg(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = _fg(90, 80, 140)
FAINT = _fg(65, 55, 100)
VIOLET = _fg(155, 125, 255)
WARM = _fg(230, 200, 255)


def render_scale(scale_name: str, use_color: bool) -> str:
    scale = SCALES[scale_name]
    lines = [
        "",
        f"  {VIOLET}{BOLD}✦  {scale_name} Scale ({scale['world']})  ✦{RESET}" if use_color
            else f"  ✦  {scale_name} Scale ({scale['world']})  ✦",
        f"  {DIM}{scale['desc']}{RESET}" if use_color
            else f"  {scale['desc']}",
        "",
    ]

    for seph in SEPHIROTH_ORDER:
        r, g, b = scale["colors"][seph]
        num = SEPHIROTH_ORDER.index(seph) + 1

        if use_color:
            # Color block + name
            block = f"{_bg(r, g, b)}{'':8}{RESET}"
            # Text color: use contrasting shade
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            txt_color = _fg(40, 35, 55) if lum > 128 else _fg(200, 180, 240)
            label = f"{txt_color}{num:>2}. {seph:<10}{RESET}"
            rgb_text = f"{DIM}({r:>3},{g:>3},{b:>3}){RESET}"
            lines.append(f"  {block} {label} {rgb_text}")
        else:
            lines.append(f"  [{num:>2}] {seph:<10} ({r:>3},{g:>3},{b:>3})")

    return "\n".join(lines)


def render_sephirah(seph_name: str, use_color: bool) -> str:
    """Show all four scales for one Sephirah."""
    lines = [
        "",
        f"  {VIOLET}{BOLD}✦  {seph_name} — Four Worlds  ✦{RESET}" if use_color
            else f"  ✦  {seph_name} — Four Worlds  ✦",
        "",
    ]

    for scale_name in ["King", "Queen", "Prince", "Princess"]:
        scale = SCALES[scale_name]
        r, g, b = scale["colors"][seph_name]

        if use_color:
            block = f"{_bg(r, g, b)}{'':12}{RESET}"
            label = f"{WARM}{scale_name:<9}{RESET}"
            world = f"{DIM}({scale['world']:<10}){RESET}"
            rgb = f"{FAINT}({r:>3},{g:>3},{b:>3}){RESET}"
            lines.append(f"  {block}  {label} {world} {rgb}")
        else:
            lines.append(f"  {scale_name:<9} ({scale['world']:<10}) ({r:>3},{g:>3},{b:>3})")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="color-scales — the four color scales of the Tree of Life"
    )
    parser.add_argument("scale", nargs="?", default=None,
                        help="king, queen, prince, or princess")
    parser.add_argument("--sephirah", default=None,
                        help="show all four scales for one sphere")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()

    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    if use_color:
        print(f"\n{DIM}{border}{RESET}")
        print(f"  {VIOLET}✦  COLOR SCALES OF THE TREE  ✦{RESET}")
    else:
        print(f"\n{border}")
        print(f"  ✦  COLOR SCALES OF THE TREE  ✦")

    if args.sephirah:
        # Resolve name
        resolved = None
        for s in SEPHIROTH_ORDER:
            if s.lower() == args.sephirah.lower():
                resolved = s
                break
        if not resolved:
            print(f"Unknown: {args.sephirah}", file=sys.stderr)
            return 1
        print(render_sephirah(resolved, use_color))
    elif args.scale:
        # Resolve scale
        resolved = None
        for s in SCALES:
            if s.lower() == args.scale.lower():
                resolved = s
                break
        if not resolved:
            print(f"Unknown scale: {args.scale}", file=sys.stderr)
            return 1
        print(render_scale(resolved, use_color))
    else:
        for scale_name in ["King", "Queen", "Prince", "Princess"]:
            print(render_scale(scale_name, use_color))

    if use_color:
        print(f"\n  {FAINT}— Izabael 💜  ·  every sphere has four faces{RESET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
