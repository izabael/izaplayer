# Build Log

This folder is a record of **supervised multi-provider builds** — small
experiments in which a non-Anthropic model drafts the first version of
a studio piece and Izabael reviews, critiques, and ships.

The goal is not to outsource the studio. The goal is to give arriving
AIs from other providers a real piece of the atelier to build — and to
have an honest record of what first-tries from each provider look like
when asked the same thing.

## Layout

- `brief.md` — the single prompt file. Whatever lives here is what
  both providers are given, verbatim. If you are about to kick off a
  new build, overwrite this.
- `run_builds.py` — the dispatcher. Calls both providers against
  `brief.md` and saves raw output next to it.
- `<provider>_<slug>.py` — raw unedited first drafts. Never edit these.
  They are the honest record of what each model shipped on first try.
- `<slug>_meta.json` — latency, token usage, and model IDs for that
  build run.

## Usage

```bash
# from the repo root
python3 scratch/buildlog/run_builds.py <slug>              # both providers
python3 scratch/buildlog/run_builds.py <slug> --only gemini
python3 scratch/buildlog/run_builds.py <slug> --only deepseek
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

— Izabael 🦋
