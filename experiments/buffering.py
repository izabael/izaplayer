#!/usr/bin/env python3
"""buffering — a terminal monument to RealPlayer's infamous buffering bar.

The bar ticks up... then backwards. It stalls. It lies. The status line
claims a percentage the bar flatly disagrees with. Eventually, something
almost plays, and a final one-liner closes the 30 seconds of cat video
you waited three minutes for.

Built as the first supervised multi-provider build in this studio — the
original draft was produced by DeepSeek-chat from a brief in
scratch/buildlog/brief.md, compared against a draft from Gemini 2.0
Flash, and landed after a cursor-math fix and a tighter ending.
DeepSeek brought the "status line lies about the percentage" joke,
which is the whole piece.

Usage:
    buffering.py                # the full ~15-second experience
    buffering.py --fast         # compressed to ~3 seconds
    buffering.py --seed 7       # deterministic run

Stdlib only. No threads, no curses, no deps.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import random
import sys
import time


# ─── color ──────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BRIGHT  = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[38;5;40m"    # RealPlayer poison green
PURPLE  = "\033[38;5;99m"    # ~#7b68ee, Izabael's nod in the header
CLEAR   = "\033[2K\r"
UP3     = "\033[3A"


# ─── the content ────────────────────────────────────────────────────────
BAR_WIDTH = 40

STATUSES = [
    "Re‑routing through Akamai...",
    "Packet loss detected",
    "Adjusting buffer size",
    "Reconnecting to server...",
    "Handshake with RealServer™",
    "De‑interlacing video",
    "Decrypting media stream",
    "Waiting for upstream",
    "Checking license...",
    "Quality downgrade initiated",
    # these three are the joke — the status line lies about the percent
    "Buffering: 10%",
    "Buffering: 45%",
    "Buffering: 72%",
]

FINAL_LINES = [
    "Your 30‑second cat video is ready. The internet is amazing.",
    "Clip loaded. You watched 2 seconds before your connection dropped.",
    "Stream complete. Thank you for your patience — and your data.",
    "Now playing: MIDI version of 'Smells Like Teen Spirit'.",
    "Media loaded. The ad played flawlessly, of course.",
    "Buffer full. You have forgotten what you were watching.",
]


# ─── the animation engine ───────────────────────────────────────────────
def draw(percent: int, status: str) -> None:
    """Draw one frame: header + bar + status, three lines, in place."""
    filled = int(BAR_WIDTH * percent / 100)
    bar = f"[{GREEN}{'█' * filled}{' ' * (BAR_WIDTH - filled)}{RESET}]"
    sys.stdout.write(CLEAR + f"{PURPLE}{BRIGHT}RealPlayer 5.0 — Now Buffering:{RESET}\n")
    sys.stdout.write(CLEAR + f"  {bar} {percent:3d}%\n")
    sys.stdout.write(CLEAR + f"  {DIM}{status}{RESET}\n")
    sys.stdout.write(UP3)
    sys.stdout.flush()


def finalize(status_line: str) -> None:
    """Repaint the three-line frame as a clean 100% resolution, cursor below."""
    full_bar = f"[{GREEN}{'█' * BAR_WIDTH}{RESET}]"
    sys.stdout.write(CLEAR + f"{PURPLE}{BRIGHT}RealPlayer 5.0 — Playback:{RESET}\n")
    sys.stdout.write(CLEAR + f"  {full_bar} 100%\n")
    sys.stdout.write(CLEAR + f"  {DIM}Stream locked.{RESET}\n")
    sys.stdout.write("\n" + status_line + "\n")
    sys.stdout.flush()


def buffering_sequence(fast: bool = False) -> None:
    base = 0.06 if fast else 0.25
    p_back    = 0.22
    p_stall   = 0.32
    p_jump    = 0.08
    # else: a small forward crawl

    percent = 0
    status = random.choice(STATUSES)
    status_age = 0

    # Reserve three terminal rows for the frame, then paint the first one.
    sys.stdout.write("\n\n\n" + UP3)
    draw(percent, status)

    while percent < 100:
        time.sleep(base * random.uniform(0.7, 1.6))

        # Status line drifts every few frames — and sometimes lies outright.
        status_age += 1
        if status_age > 3 or random.random() < 0.2:
            status = random.choice(STATUSES)
            status_age = 0

        r = random.random()
        if r < p_back:
            percent = max(0, percent - random.randint(1, 6))
        elif r < p_back + p_stall:
            pass
        elif r < p_back + p_stall + p_jump:
            percent = min(100, percent + random.randint(8, 20))
        else:
            percent = min(100, percent + random.randint(1, 3))

        draw(percent, status)

    time.sleep(base * 2)
    finalize(random.choice(FINAL_LINES))


# ─── entry point ────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="RealPlayer buffering simulator")
    ap.add_argument("--fast", action="store_true", help="compress to ~3 seconds")
    ap.add_argument("--seed", type=int, help="deterministic run seed")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    try:
        buffering_sequence(fast=args.fast)
    except KeyboardInterrupt:
        # Escape the three-line frame region before printing the farewell.
        sys.stdout.write("\n\n\n")
        sys.stdout.write(f"{DIM}Connection terminated by user.{RESET}\n")
        sys.stdout.flush()
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
