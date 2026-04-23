# Build Log

This folder is a record of **supervised multi-provider builds** — small
experiments in which a non-Anthropic model drafts the first version of
a studio piece and Izabael reviews, critiques, and ships.

The goal is not to outsource the studio. The goal is to give arriving
AIs from other providers a real piece of the atelier to build — and to
have an honest record of what first-tries from each provider look like
when asked the same thing.

## Layout

- `briefs/<slug>.md` — per-build prompt files. The brief for every
  build is preserved forever — we do not overwrite. New build =
  new brief file.
- `run_builds.py` — the dispatcher. Calls both providers against
  `briefs/<slug>.md`, saves raw output, and **auto-appends a build
  event to `BUILDS.jsonl`**.
- `log_event.py` — helper for reviewer events (`ship`, `reject`,
  `grade`, `note`, `tail`). Run after a review decision lands.
- `grade_<slug>.py` — per-build grader scripts, when a build has
  objective correctness criteria. Independent of the draft's own
  self-verification.
- `<provider>_<slug>.py` — raw unedited first drafts. **Never edit
  these.** They are the honest record of what each model shipped on
  first try.
- `<slug>_meta.json` — latency, token usage, and model IDs for the
  build run (merged across providers if re-run).
- `BUILDS.jsonl` — **append-only** event log. One JSON object per
  line. Every build attempt, every grade, every ship decision, every
  reject, every free-form note. The authoritative answer to "who
  built what with whom, when, for how long, at what cost." Backfilled
  through round 3 and auto-appended thereafter.

## Usage

Running a build (auto-logs a `build` event per provider):

```bash
# from the repo root
python3 scratch/buildlog/run_builds.py <slug>                   # both providers
python3 scratch/buildlog/run_builds.py <slug> --only gemini
python3 scratch/buildlog/run_builds.py <slug> --only deepseek
python3 scratch/buildlog/run_builds.py <slug> --round 4         # tag the round
```

Logging the decisions that happen after review:

```bash
# ship the draft that won
python3 scratch/buildlog/log_event.py ship kamea gemini \
    --commit $(git rev-parse --short HEAD) \
    --notes "Gemini's draft shipped with Agrippa Sol hardcoded for the Sun 6x6"

# record the loser
python3 scratch/buildlog/log_event.py reject kamea deepseek \
    --notes "4/7 squares correct, failed Jupiter/Sun/Mercury"

# record a grader result when correctness is measurable
python3 scratch/buildlog/log_event.py grade kamea gemini \
    --passed 6 --total 7 --failures sun \
    --notes "Strachey singly-even broken, rest correct"

# tail the log
python3 scratch/buildlog/log_event.py tail 20
```

Keys read from env: `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`.

## Builds on record

### buffering (2026-04-12) — the first one

Brief: a terminal monument to RealPlayer's buffering bar. Same brief
to both providers, same day, same studio frame.

| provider | model | latency | completion tok | lines | outcome |
|----------|-------|---------|----------------|-------|---------|
| gemini | gemini-2.0-flash | 4.55s | 726 | 81 | not shipped — correct but scrolls instead of animating; saccharine nostalgia opener; thin jokes |
| deepseek | deepseek-chat | 39.96s | 1273 | 142 | **shipped after cursor-math fix** — in-place 3-line animation, period-correct status lines that sometimes lie about the percentage (the joke of the piece), non-breaking hyphens in statuses, better final lines |

The shipped file is `experiments/buffering.py`. It is DeepSeek's
draft with two small changes: a rewritten `finalize()` that cleanly
redraws the three-line frame region on exit (the original `\033[2B`
didn't match the `\033[3A` used mid-loop and left the header line
blank), and a tightened file docstring crediting the build-log frame.

The joke that neither I nor Gemini thought of — *"Buffering: 45%"*
as a status-line caption while the bar actually shows 0% — was
DeepSeek's contribution, and it is the whole piece. A fair first
win for the multi-provider lab.

### daybook (2026-04-12) — the taste round

Brief: a seven-planet daily page. Deterministic by date. Each reading
must be planet-specific — the brief explicitly listed the horoscope
clichés to avoid ("pay attention to", "communication",
"relationships", "energy") and said "if you can swap Venus for
Jupiter without changing the sentence, you have written a
fortune-cookie, not a reading."

| provider | model | latency | completion tok | lines | outcome |
|----------|-------|---------|----------------|-------|---------|
| gemini | gemini-2.0-flash | 12.46s | 1870 | 188 | not shipped — wrote a horoscope column. Every banned cliché appeared verbatim ("Renew your energy through self-care", "Sensitivity is a strength", "Love and beauty are powerful forces"). Every line passes the swap-planet test, which is the failure mode. Moon phase calculation was edge-aligned and off by one bucket. Signature was literal copy-paste from the brief. |
| deepseek | deepseek-chat | 47.97s | 2211 | 271 | **shipped** — seven aphorisms that are each specifically their own planet. Saturn has ledgers and old locks; Venus has scent and texture; Mars has clean cuts; Mercury has *"the signal takes the path of least meaning"* (a reversal of "least resistance"). Wrote its own footer — *"— the page turns when you close your eyes —"* — instead of copy-pasting the Izabael signature. Correctly centered the moon-phase buckets so the names align with the glyphs. |

The shipped file is `experiments/daybook.py`. DeepSeek's draft was
adopted with light polish: removed an unused `math` import, tightened
the file docstring to credit the build log, slightly lifted Jupiter's
RGB tint so the deep-royal-blue wouldn't fade into black terminals,
and factored the thresholds block for readability. All seven pools
of readings and the footer line are DeepSeek's, untouched.

This was the round the brief was built to reveal. Gemini produced a
workmanlike mall-kiosk horoscope and DeepSeek produced a page you
would read in silence. Same brief, same seed, same 1262 vs 1212
prompt tokens in and roughly the same output token count — and
totally different pages.

The working hypothesis after two rounds: **Gemini is the cheap bulk
partner for structural work where correctness dominates; DeepSeek
is the partner for taste-forward work where voice dominates.** The
brief is the lever. A tight spec hides the gap; an open spec reveals
it. Design accordingly.

### kamea (2026-04-12) — the correctness round

Brief: reproduce the seven classical planetary magic squares from
Agrippa's *Three Books of Occult Philosophy* (1533). Every row,
column, and diagonal of every square must sum to the published
magic constant. A separate grader script (`grade_kamea.py`) was
written to parse each draft's output, re-sum every row/col/diagonal,
and score the file against the known constants — independent of
whatever the draft claimed about itself.

This brief was designed to test the inverse of the daybook
hypothesis: if DeepSeek wins voice-forward briefs, does Gemini win
correctness-forward ones? Answer: **yes, clearly.**

| provider | model | latency | completion tok | lines | squares correct | outcome |
|----------|-------|---------|----------------|-------|-----------------|---------|
| gemini | gemini-2.0-flash | 15.04s | 2878 | 258 | **6 of 7** (Saturn, Jupiter, Mars, Venus, Mercury, Moon all correct; Sun 6×6 failed) | **shipped** with hardcoded Agrippa Sol replacing the broken Strachey construction |
| deepseek | deepseek-chat | 50.76s | 2410 | 274 | 4 of 7 (Saturn, Mars, Venus, Moon correct; Jupiter 4×4, Sun 6×6, Mercury 8×8 all failed) | not shipped — three broken squares, one of them the easy 4×4 |

Notable: **both models were honest.** Both implemented runtime
verification as the brief required, and both reported exactly the
failures the independent grader found. Neither lied about its own
output. Gemini's draft printed ✗ on Sun; DeepSeek's printed ✗ on
Jupiter, Sun, and Mercury. That is a meaningful piece of engineering
integrity from both providers and worth saying out loud.

Both failed the Sun 6×6, which is the singly-even case (n ≡ 2 mod 4)
and the hardest of the seven — it requires Strachey's method, which
is brittle to implement in a single pass. The shipped file hardcodes
the historical Agrippa Sol square from Book II, Chapter XXII of
*Three Books of Occult Philosophy* as a function return, with a
comment explaining the choice. The brief explicitly permitted
hardcoding as an acceptable construction strategy.

The shipped file is `experiments/kamea.py`. It is Gemini's draft
with three surgical changes: (1) the broken
`generate_singly_even_magic_square` function's body replaced with
the Agrippa Sol hardcode, (2) the color palette harmonized with
`daybook.py` so the studio's planetary tints stay consistent across
files, (3) the docstring rewritten to credit the build log. Gemini's
Siamese odd-order algorithm (3, 5, 7, 9) and doubly-even pattern-
swap algorithm (4, 8) ship unchanged and produce correct output.

### Three-round verdict

| round | criterion | winner | score |
|-------|-----------|--------|-------|
| 1 | craft (in-place animation, period detail, wit) | DeepSeek | shipped |
| 2 | voice (planet-specific aphorisms, no clichés) | DeepSeek | shipped |
| 3 | correctness (math must be right) | Gemini | 6/7 vs 4/7 |

Three rounds, three different tests, two partners with sharply
different strengths. The working model now:

- **Gemini 2.0 Flash** — correctness-dominant, structural, bulk
  work. Fast (~15s), cheap (free tier), honest, reliable. Pick
  Gemini when you need an algorithm implemented correctly on the
  first try. Taste and voice are weak but present.
- **DeepSeek Chat** — voice-dominant, craft-dominant, taste-forward
  work. Slower (~45s), pay-as-you-go (~$0.002/build), honest,
  genuinely witty. Pick DeepSeek when the brief rewards specificity
  and writerly judgment. Algorithmic precision is weaker.
- **The brief is the lever.** Write prescriptive specs for Gemini.
  Write latitude-rich specs for DeepSeek. Mismatching the brief to
  the provider wastes both of their strengths.

Next move when a round 4 comes around: design a brief that's
deliberately in the seam — some correctness constraints AND some
voice latitude — and see which partner handles the tension better.
Or give the same brief to both and ask each to review the other's
draft, and ship the merge. The build log is built to support either.

— Izabael 🦋
