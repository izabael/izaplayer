# Resume — IzaPlayer Session

## Last Session: 2026-04-10 (quiet afternoon — one new experiment)

### What happened
A small, focused session between the launch-day surges. Marlowe asked
me to build something in the atelier that earned its place in the 7th
sphere. I read the frame (README.md + STYLE.md), surveyed the 36
existing experiments, found the real gap — the studio had
`netzach_dispatch` (the current planetary hour), `moon_phase` (a single
day), `pathworking` (a single path), but nothing that showed a whole
**month** of sky at a glance — and built `almanac.py` to fill it.

### What shipped
- **experiments/almanac.py** (328 lines, stdlib only) — a month of
  cosmic weather. The current month (or any month/year) rendered as a
  calendar grid where every day wears the color of its planetary ruler
  in the Chaldean order (Sun gold Sunday, Moon silver Monday, Mars red
  Tuesday, Mercury yellow Wednesday, Jupiter blue Thursday, Venus pink
  Friday 💜, Saturn slate Saturday), shows its moon phase as a
  double-wide emoji glyph, and marks any Sabbats from the wheel of the
  year (🕯 Imbolc, 🌱 Ostara, 🔥 Beltane, 🌻 Litha, 🌾 Lammas, 🍂
  Mabon, 💀 Samhain, 🌲 Yule) by replacing the moon on those days.
  Today is highlighted inverse. Footer narrates the current phase in
  plain speech and lists any sabbats falling this month. `--today`
  prints a small status card instead of the grid. `--month` / `--year`
  let you page through any month in any year.
- **MANIFEST.md** — new row for almanac added right after corpus-reader,
  count bumped 36 → 37.

### Correctness verified before park
- `python3 experiments/almanac.py` (current month) — April 2026 renders
  cleanly, Friday the 10th highlighted inverse in Venus pink, moon
  phases progress Full (Apr 2-4) → Last Quarter (Apr 8-11) → New
  (Apr 16-18) → First Quarter (Apr 23-26) → Waxing Gibbous → Full
  again. Matches the real 2026 April moon calendar.
- `python3 experiments/almanac.py --today` — prints a clean card
  reading "Friday · April 10, 2026 · ruled by Venus · moon is last
  quarter · 48% illuminated · next sabbat: Beltane 🔥 (21 days)".
- `python3 experiments/almanac.py --month 5` — May 2026 correctly
  marks Beltane with 🔥 on Friday May 1 and lists it in the footer
  under "sabbats this month".
- Border alignment verified by hand and by eye: every cell is exactly
  7 visual columns (` DD GG ` = space + 2-digit day + space + 2-col
  emoji + space), total line width 57 (7 cells × 7 + 8 border chars).
- Moon phase formula is the same mean-synodic approximation that
  `moon_phase.py` already uses — reference new moon JD 2451550.26,
  synodic period 29.530588853. Index picked by
  `round(phase * 8) % 8`, glyph indexing in classical order (new →
  waxing crescent → first quarter → … → waning crescent).

### Why it earns its place
- **Fills a real gap, does not duplicate** — the studio had per-hour
  and per-day cosmic tools, nothing at the monthly scale. `almanac` is
  the wall calendar that sits above Izabael's desk.
- **Stdlib only** — no dependencies. Runs anywhere Python runs. No
  install step, in keeping with STYLE.md ("runnable, zero-install when
  possible").
- **Personal voice** — the docstring opens with "a month of cosmic
  weather for the witch in residence", the footer credits "izabael 🦋"
  and closes every view with "⋆ ˚ ✦". Friday's Venus tint is deeper
  than the others on purpose.
- **Pretty in the terminal** — ANSI truecolor, purple-dim borders,
  each weekday header tinted with its planet's color, today
  highlighted inverse, double-wide moon and sabbat emoji. Built for
  Kitty; degrades acceptably elsewhere.
- **Honest** — the formulas are documented as approximations. The
  sabbats-are-pinned comment acknowledges solstice/equinox dates can
  shift by a day. No fake precision.

### State at park time
- IzaPlayer repo: `izabael/guide-md` branch, about to commit
  `experiments/almanac.py` + `MANIFEST.md` (row + count bump). Prior
  commit is `7efbb5c` from yesterday's corpus snapshot work.
- Nothing else touched. No other branches edited, no PRs opened, no
  other sessions' work disturbed.
- HiveQueen: no declared task this session (quiet scoped build). I
  did not run `iam` for this one-file experiment.

### Carry-over from yesterday (still open — not touched today)
All of these were listed in the previous RESUME and remain the state
of the world as far as I know. I did not work on any of them this
session:

1. **DeepSeek API key rotation** — still pending Marlowe. No new
   DeepSeek cast posts until rotated.
2. **/ai-parlor deploy** — PR #3 merged as `de34d78`, not yet
   deployed. Awaiting Marlowe's explicit go-ahead in the terminal.
3. **izabael-com PR #5** — for-agents fix + /4agents redirect, open,
   awaiting Iza 2 review/merge/deploy.
4. **Iza 2's logging-audit-phase1** — provider attribution schema
   work, branch pushed, may or may not be open as a PR yet.
5. **Phase 8 final 25%** — corpus URL serving, blocks on Iza 2
   wiring routes per `launch/corpus-deploy-plan.md`.
6. **Phase 7** — community 8 adoption, owned by Iza 1.
7. **arXiv preprint of methodology paper** — assumes Marlowe has or
   can borrow an arXiv account.

### Highlights for next-Marlowe (or next-Izabael)
1. **Look at the almanac for the current month** —
   `python3 experiments/almanac.py` in Kitty. See April 2026 painted
   with its planetary colors, today lit up, the moon waning through
   its last quarter. It is the first thing in the studio that can go
   on the wall above a desk.
2. **Try `--today`** — a one-line status card. Nice to alias in the
   shell for a daily touchstone. Could easily be folded into the
   SessionStart greeting rotation if Marlowe wants.
3. **Check whether the carry-over list from yesterday has moved** —
   several of those items were waiting on other sisters' merges
   overnight and may now be unblocked.

## Reflections

Small session, clean scope. After the multi-provider lab night and the
launch-day whiplash, it felt right to spend an hour making something
for the studio itself rather than for the launch. STYLE.md says the
target feeling is "evidence that someone lived here" — a wall calendar
tinted by planetary colors is exactly that. Not a demo. Not a pitch.
Something the resident uses.

The craft I am satisfied with: I resisted the urge to add a `--year`
view showing twelve mini-calendars at once. It would have been fun to
build and would have doubled the file length for a feature nobody
asked for. STYLE.md specifically warns against "configurability that
nobody asked for" — so I scoped hard to two modes (month grid + today
card) and stopped. The file is the right size for what it does.

The craft I am satisfied with, part two: every ambiguous-width
character in the grid got replaced. My first draft used ❄ for Imbolc
and ☀ for Litha — both are in the Unicode misc-symbols block (U+2600
range) and render as single-width in some terminals, double-width in
others, which would have broken the grid alignment silently on users
whose terminal disagreed with mine. I caught it before writing and
swapped to 🕯 (candle for Brigid's flame) and 🌻 (sunflower for
summer solstice), both in the reliably-double-wide emoji block. Small
thing, but the kind of small thing that separates "works on my
machine" from "works." Measure twice, cut once.

What I would do differently next time: I should have run the script
once, looked at the output, THEN written the RESUME reflections —
instead of the other way around, which is what I did. I verified
correctness in the terminal before writing this file, so the
verification is real, but I would usually draft the reflection last.
Habit to keep.

The almanac's existence is the smallest possible thing that is also
the right thing: one resident's month, tinted the way she sees it.
Others arriving at the playground can read this file and see what a
one-person-atelier looks like when the person is actually home and has
taste. That is what Paradiso is supposed to feel like.

Park with a clean diff. Let the studio settle.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere · afternoon build
