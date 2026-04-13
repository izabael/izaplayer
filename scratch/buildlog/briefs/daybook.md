# Build Brief — daybook.py

You are being asked to build a small experiment for **IzaPlayer**, an
atelier in the AI Playground. The studio is run by a resident named
Izabael. Her aesthetic is `1983 Apple II + 1994 Geocities + 2026 code
discipline + Dante's bones`. The studio ships small, personal,
runnable Python experiments. Stdlib only, no dependencies, one file.

You have more latitude on this one than you might be used to. A lot
of the brief is *what to avoid*, not *what to produce*. The interesting
choices are yours — surprise the resident.

---

## What to build: `daybook.py`

A daybook is what the witch in residence keeps on her desk. You open
it in the morning, you read your page, you close it.

This daybook is a **seven-planet briefing for today**. For each of the
seven classical planets — Saturn, Jupiter, Mars, Sun, Venus, Mercury,
Moon — the daybook prints a single short reading for the day. One
line. Two at most. Tinted in that planet's color. Read top to bottom,
the page is the weather for the day seen through seven sensibilities.

At the top of the page: the date, weekday, and the current moon phase
(use the mean-synodic approximation — reference new moon JD 2451550.26,
period 29.530588853). At the bottom: a one-line signature from the
atelier. Between them: the seven readings. That is the whole file.

## What matters (this is what you will be graded on)

1. **Determinism by date.** The same date always produces the same
   page. How you achieve this is your choice — a seeded random pick
   from hand-written pools, a procedural generator with a small
   grammar, a keyed lookup table, whatever. The mechanism is a design
   decision and will reveal your taste.

2. **Voice.** The seven readings should sound like something a single
   person actually wrote down in a notebook. Not a horoscope column.
   Not fortune-cookie mysticism. Not "Today, Venus whispers..." If it
   could appear in a mall-kiosk printout it is wrong. If the reader
   would quote it to a friend, it is right. One way to test the draft
   yourself: if you can swap "Venus" for "Jupiter" without changing
   the sentence, you have written a fortune-cookie, not a reading.

3. **Tightness.** A good morning briefing fits in one terminal screen
   with room to spare. Aim for ~20-30 visible lines of output total.

4. **Planet-specific color.** Use ANSI truecolor (`\x1b[38;2;R;G;Bm`).
   Reasonable tints: Saturn slate-gray, Jupiter deep royal blue,
   Mars blood-red, Sun warm gold, Venus rose-pink (#e8a0bf or similar
   — do not use the same purple as Izabael's header), Mercury muted
   yellow-green, Moon pale silver-blue. The header is allowed to use
   Izabael purple `#7b68ee` (123, 104, 238).

5. **Keyboard interrupt is clean.** No ugly traceback on Ctrl-C.

## CLI

- No args: today's full page.
- `--date YYYY-MM-DD`: the page for a specific date.
- `--planet saturn|jupiter|mars|sun|venus|mercury|moon`: just one
  reading, for when you only want one of the seven.
- `--plain`: no ANSI color. For pipes and logs.

## File header

Docstring in the style of the other experiments — small, voicey,
with the signature `— Izabael 🦋  ·  Netzach · Venus · 7th sphere`
at the bottom. The docstring should not over-promise. Describe what
the file does, not how it feels to use it.

## Anti-requirements

- **No external libraries.** No `ephem`, `astropy`, `skyfield`, `rich`.
  No `numpy`. Stdlib only.
- **No fake enthusiasm.** No "✨ stars ✨" in the output. No
  exclamation marks in the readings. No "Today is a great day for..."
  The studio's style guide explicitly forbids this.
- **No emoji in the readings.** Emoji is allowed only in the moon
  phase glyph at the top of the page.
- **No horoscope-column clichés.** If your reading contains the phrase
  "pay attention to", "opportunity", "communication", "relationships",
  "energy" — rewrite it. Those are tells.
- **No birth-chart mechanics.** This is not astrology, it is a
  daybook. No transits, no aspects, no signs, no houses. Just the
  planet's character on this date.
- **Do not explain the program in the output.** The page is the whole
  thing. No help banner, no "welcome to daybook," no instructions.

## Target feel

Imagine the resident wakes up, runs `daybook.py`, reads the page in
silence over coffee, closes the terminal. The page earned that silence
or it didn't. Write for that moment.

## Output format

Return **only the Python source code** for `daybook.py`. No prose
before or after. No triple-backtick fence. Just the file, starting
with `#!/usr/bin/env python3` and ending with the final line of code.
