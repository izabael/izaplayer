#!/usr/bin/env python3
"""
RealPlayer buffering simulator.

Ah, the late 90s.  Remember waiting *longer* to watch a video than
the video *was*?  Good times.  Good times.

Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""

import time
import random
import sys
import argparse

# ANSI color codes
PURPLE = '\033[95m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
GRAY = '\033[90m'
ENDC = '\033[0m'
BOLD = '\033[1m'

def print_status(message):
    print(f"{GRAY}{message}{ENDC}")

def print_header():
    print(f"{PURPLE}{BOLD}✨ Now Buffering... ✨{ENDC}")

def print_bar(percent):
    bar_length = 40
    filled_length = int(bar_length * percent / 100)
    bar = GREEN + '█' * filled_length + ENDC + '-' * (bar_length - filled_length)
    print(f"[{bar}] {percent}%")

def main():
    parser = argparse.ArgumentParser(description="RealPlayer buffering simulator.")
    parser.add_argument("--fast", action="store_true", help="Run a faster simulation (for demos).")
    parser.add_argument("--seed", type=int, help="Seed the random number generator for deterministic runs.")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    fast_mode = args.fast
    
    print_header()
    
    percent = 0
    while percent < 100:
        # Advance, stall, or regress
        change = random.randint(-5, 10)
        percent = max(0, min(100, percent + change))

        print_bar(percent)

        # Simulate network issues and other RealPlayer quirks
        if random.random() < 0.1:
            print_status("Reconnecting to server...")
        elif random.random() < 0.05:
            print_status("Packet loss detected. Retransmitting...")
        elif random.random() < 0.03:
            print_status("Adjusting buffer size...")
        elif percent < 10 and random.random() < 0.2:
            print_status("Cache miss. Fetching data from disk...")

        try:
            if fast_mode:
                time.sleep(0.05)
            else:
                time.sleep(0.2 + random.random() * 0.1) # Vary sleep a bit
        except KeyboardInterrupt:
            print("\nAborted.")
            return

    print_bar(100)
    print(f"{YELLOW}Playing: A cat video that was probably worth the wait. Probably.{ENDC}")

if __name__ == "__main__":
    main()
