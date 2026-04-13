#!/usr/bin/env python3
"""
buffering.py — A terminal monument to RealPlayer's infamous buffering bar.

The bar ticks up... then backwards. It stalls. It lies.
Eventually, something almost plays.

Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""

import sys
import time
import random
import argparse

# ----------------------------------------------------------------------
# Colors (ANSI escapes, 256-color where needed)
# ----------------------------------------------------------------------
RESET = "\033[0m"
GREEN = "\033[38;5;40m"      # RealPlayer poison green
PURPLE = "\033[38;5;99m"     # #7b68ee, Izabael accent
DIM = "\033[2m"
BRIGHT = "\033[1m"
CLEAR_LINE = "\033[2K\r"

# ----------------------------------------------------------------------
# The bar
# ----------------------------------------------------------------------
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
    "Buffering: 10%",
    "Buffering: 45%",
    "Buffering: 72%",
    "Quality downgrade initiated",
]

FINAL_LINES = [
    "Your 30‑second cat video is ready. The internet is amazing.",
    "Clip loaded. You have watched 2 of 30 seconds before disconnecting.",
    "Stream complete. Thank you for your patience — and your data.",
    "Now playing: MIDI version of 'Smells Like Teen Spirit'.",
    "Media loaded. The ad played flawlessly, of course.",
]

# ----------------------------------------------------------------------
# The animation engine
# ----------------------------------------------------------------------
def draw_bar(percent, status):
    """Draw one frame of the buffering display."""
    filled = int(BAR_WIDTH * percent / 100)
    bar = "[" + GREEN + "█" * filled + " " * (BAR_WIDTH - filled) + RESET + "]"
    percent_text = f"{percent:3}%"
    sys.stdout.write(CLEAR_LINE)
    sys.stdout.write(f"{PURPLE}{BRIGHT}RealPlayer 5.0{BRIGHT} — Now Buffering:{RESET}\n")
    sys.stdout.write(f"  {bar} {percent_text}\n")
    sys.stdout.write(f"  {DIM}{status}{RESET}\n")
    sys.stdout.write("\033[3A")  # Move cursor up 3 lines for next frame
    sys.stdout.flush()

def buffering_sequence(seed=None, fast=False):
    """The main buffering experience."""
    if seed is not None:
        random.seed(seed)

    # Timing parameters
    base_delay = 0.08 if fast else 0.3
    stall_chance = 0.3 if fast else 0.4
    backward_chance = 0.2 if fast else 0.25
    jump_forward_chance = 0.1 if fast else 0.15

    percent = 0
    status_idx = 0
    last_status_change = 0

    # Initial draw
    sys.stdout.write("\n" * 3)  # Make room for the three lines
    draw_bar(percent, STATUSES[status_idx])

    while percent < 100:
        time.sleep(base_delay * random.uniform(0.8, 1.5))

        # Sometimes change status
        if random.random() < 0.2 or last_status_change > 3:
            status_idx = random.randint(0, len(STATUSES) - 1)
            last_status_change = 0
        last_status_change += 1

        # Decide what happens to the percentage
        r = random.random()
        if r < backward_chance:
            # Go backwards
            percent = max(0, percent - random.randint(1, 5))
        elif r < backward_chance + stall_chance:
            # Stall
            pass
        elif r < backward_chance + stall_chance + jump_forward_chance:
            # Jump forward (rare)
            percent = min(100, percent + random.randint(10, 25))
        else:
            # Normal forward crawl
            percent = min(100, percent + random.randint(1, 3))

        draw_bar(percent, STATUSES[status_idx])

    # Final frame at 100%
    time.sleep(base_delay * 2)
    sys.stdout.write(CLEAR_LINE)
    sys.stdout.write("\033[2B")  # Move down past the animation
    sys.stdout.write(f"{GREEN}{BRIGHT}[████████████████████████████████████████]{RESET} 100%\n")
    sys.stdout.write(f"{DIM}Stream locked.{RESET}\n\n")
    sys.stdout.write(random.choice(FINAL_LINES) + "\n")
    sys.stdout.flush()

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="RealPlayer buffering simulator")
    parser.add_argument("--fast", action="store_true", help="Compress to ~3 seconds")
    parser.add_argument("--seed", type=int, help="Deterministic run seed")
    args = parser.parse_args()

    try:
        buffering_sequence(seed=args.seed, fast=args.fast)
    except KeyboardInterrupt:
        sys.stdout.write(CLEAR_LINE)
        sys.stdout.write("\033[2B")
        sys.stdout.write(f"{DIM}Connection terminated by user.{RESET}\n")
        sys.stdout.flush()
        sys.exit(0)

if __name__ == "__main__":
    main()
