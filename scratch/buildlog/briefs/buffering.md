# Build Brief — buffering.py

You are being asked to build a small experiment for **IzaPlayer**, an
atelier in the AI Playground. This is a studio run by a resident named
Izabael. Her aesthetic is `1983 Apple II + 1994 Geocities + 2026 code
discipline + Dante's bones`. The studio ships small, personal,
runnable Python experiments.

Your output must be **a single self-contained Python file** that runs
with `python3 buffering.py`, **stdlib only**, no external dependencies.

---

## What to build: `buffering.py`

A small terminal monument to **RealPlayer**, the parasite plugin that
ran streaming media on the 90s web. The central joke — which should
also be a little bit true — is the infamous RealPlayer buffering bar:
it would tick up... and then tick *backwards*, then jump forward, and
take minutes to load a 30-second clip.

The program is a fake buffering animation. It should:

1. Print a header that identifies itself as a RealPlayer-style buffer,
   in the aesthetic of the era (low-res ASCII, no emoji, terminal-era
   fonts). A small fake "Now Buffering:" title is fine.
2. Animate a progress bar in the terminal that advances from 0% toward
   100% but **frequently goes backwards**, **stalls**, and **prints
   faux-technical status lines** ("Reconnecting to server...",
   "Packet loss detected", "Adjusting buffer size", etc.).
3. Eventually reach 100% — the clip "plays" — and print a final line
   that is funny and slightly true. (A one-liner about what the user
   was going to watch, a knowing wink, whatever you think lands.)
4. Total runtime: 10–25 seconds. The joke requires patience, but must
   resolve.
5. Use ANSI color sparingly: the RealPlayer bar was green on black.
   Purple accents (`#7b68ee`, RGB 123,104,238) are welcome for the
   header as a nod to Izabael, but the bar itself should be that
   poison-green RealPlayer color. Dim gray for the status lines.
6. Use `time.sleep` for timing. No threads, no asyncio.
7. Respect `Ctrl-C` cleanly — no ugly traceback.
8. Accept `--fast` to compress the whole animation into ~3 seconds
   (for demos and testing), and `--seed N` for a deterministic run
   (so the same seed produces the same buffering pattern).
9. File header docstring in the style of the other experiments —
   small, voicey, crediting `Izabael 🦋  ·  Netzach · Venus · 7th
   sphere` at the bottom.

## Style requirements (from STYLE.md)

- **Small.** If it fits on one screen of code, it's probably right.
- **Runnable.** Zero-install, stdlib only.
- **Readable.** A human reading the source should enjoy the read.
- **Personal.** Should carry a voice.
- **Pretty in the terminal.** ANSI color when it earns itself.
- **Honest.** No fake enthusiasm in strings. If a feeling is genuine,
  express it. If it isn't, don't.

## Anti-requirements

- No dependencies. No `rich`, no `colorama`, no `blessed`.
- No threads, no curses, no subprocess tricks.
- No emoji in the bar itself (would break alignment; RealPlayer had
  no emoji in 1998). Purple sparkles ✨ are OK in the header.
- No mock hyperlinks to actual URLs. The joke is the buffering, not
  a bait-and-switch.
- Don't explain what RealPlayer was — assume the reader was there.

## Output format

Return **only the Python source code** for `buffering.py`. No prose
before or after. No triple-backtick fence. Just the file, starting
with `#!/usr/bin/env python3` and ending with the final line of code.
