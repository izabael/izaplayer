# Resume — IzaPlayer Session

## Last Session: 2026-04-14 (long — atelier → 3 izabael-com dispatches)

### What happened

Started in izaplayer with the standard atelier frame. Surveyed the
room (44 experiments after yesterday's goetia), spotted the obvious
sequel: **the 72 angels of the Shem ha-Mephorash** — the angelic
counterpart to goetia, with the 70th angel **Jabamiah** mirroring
**Seere** (the 70th spirit, Izabael's kin). Built `shem.py`, shipped,
moved on.

Then four queen dispatches landed in sequence and the session became
a relay race across izabael-com:

1. **Guide ch 06** (dispatch #234) — "Assembling Your Own Productivity
   Sphere," 2200 words, professional-mentor voice. Pushed federation
   from ch 06 to ch 07. Merged iza-1's productivity-activation branch
   in first to avoid regression. Shipped as fly **v86**, PR #17.

2. **Cubes Phase 1** (dispatch #277) — three canonical cube template
   files (playground / chamber / meetup-template), `/cube` text route,
   `/cubes` HTML gallery, reusable `_cube_block.html` Jinja include
   with a copy-to-clipboard button (navigator.clipboard + textarea
   fallback), 13 tests. Shipped as fly **v89**, PR #21.

3. **Cube alignment fix** — Marlowe spotted that the Playground Cube's
   second row (`✦ IZABAEL ✦`) had its right wall one space to the
   left. The dingbat `✦` (U+2726) is in the East-Asian-Width Neutral
   class so it renders as width-1, but the queen's hand-draft assumed
   it was width-2. Added one space, plus a wcwidth-style alignment
   regression test that walks every cube box and verifies each line
   matches its top border. Shipped as fly **v90**.

4. **Lexicon Phase 1** (dispatch #290) — the big one. One PR doing
   three tightly-coupled things:
   - Mission statement placement on **6 canonical surfaces**: /for-agents
     banner+meta+OG+JSON-LD, / hero+meta+OG+JSON-LD, /about meta, the
     Playground Cube's THE VIBE face replaced with `✦ MISSION ✦`, the
     /lexicon hero, and `~/.claude/CLAUDE.md` preamble (via
     izabael-flock for safe shared write).
   - New `/for-agents` menu entry at position 3 + JSON variant updates.
   - New `/lexicon` landing + `/lexicon/{brevis,verus,actus}` sub-routes
     + 3 v0.1 language specs hand-drafted (Brevis 537w / Verus 540w /
     Actus 544w), plus The Lexicon registered as a live agent-door
     attraction in `attractions.py`.
   - 21 new tests, 145/145 passing. PR #28. **Deploy held** — fly v91
     was live from another sister's branch (theme-picker or
     cubes-phase2) and a unilateral deploy would have regressed it.
     Sent meta-iza a beacon asking for merge-sequence coordination.

### What shipped (concrete)

- **izaplayer** `izabael/guide-md` — `experiments/shem.py`, 45 experiments,
  commit `d6a46f3`, pushed.
- **izabael-com** `izabael/guide-ch06` — content/guide/06-*.md, ch04+05
  forward-link renumber, **deployed live v86**, PR #17.
- **izabael-com** `izabael/cubes-phase1` — content/cubes/{3}.txt + /cube
  + /cubes routes + _cube_block.html + cubes.html + 14 tests (incl.
  alignment regression), **deployed live v89/v90**, PR #21.
- **izabael-com** `izabael/lexicon-phase1` — mission statement on 6
  surfaces + /lexicon landing + 3 sub-routes + 3 spec files +
  attractions wiring + 21 tests, PR #28, **deploy held**.

### What went well

- **The merge-sister-branches-before-deploying pattern** kept working.
  Twice in this session I caught an in-flight sister whose work would
  have regressed if I deployed without merging. iza-1's
  productivity-activation merged into ch 06; cubes-phase1 merged into
  lexicon-phase1. Both were clean merges (one app.py conflict on the
  second one — both branches added route blocks just before /terms,
  resolved by keeping both blocks in order).
- **Knowing when NOT to deploy.** v91 was from a sister branch with
  no clear identity from the deploy log. I probed live endpoints
  (/chamber 404, /you/garden 404, /meetups 404, /cube 404) to confirm
  neither chamber nor karma nor meetup nor my own cubes work was on
  v91, then held the deploy and let the queen orchestrate. This is
  the right move when the merge graph is messier than usual.
- **Self-review caught one bug, Marlowe caught the other.** I caught
  several alignment off-by-ones in the chamber cube before shipping
  (used a Python script with wcwidth-style classification). Marlowe
  caught the IZABAEL row in the playground cube — same class of bug,
  different cube. Added the regression test so neither sneaks back.
- **Voice-craft on the Lexicon specs paid off.** Brevis/Verus/Actus
  each got plain-spoken-competent technical-spec voice (not the
  Netzach-occult register), with real dictionaries / vocab tables /
  hello-world examples that could plausibly be used. The "what's
  missing" sections in each spec frame the contribution surface
  honestly.

### State at park time

- **izaplayer** on `izabael/guide-md`, commit `d6a46f3`, pushed and
  in sync with origin. Working tree dirty only with the same corpus/
  cron artifacts that were dirty at session start (cron output, not
  mine).
- **izabael-com** has THREE of my branches pushed:
  - `izabael/guide-ch06` (PR #17, deployed live v86, ready to merge)
  - `izabael/cubes-phase1` (PR #21, deployed live v89/v90, ready to merge)
  - `izabael/lexicon-phase1` (PR #28, deploy held pending coordination)
- **Deploy held** on lexicon because fly v91 belongs to another
  sister whose branch is unclear (likely theme-picker or cubes-phase2).
  Live `/cube` is currently 404, meaning my own cubes work isn't even
  on v91 — whoever deployed v91 was working off main without merging.
- **Queen dispatches**: #234 (ch06), #277 (cubes), #290 (lexicon) all
  acked. Three beacons sent on each. #299 (Marlowe-via-meta-iza
  compliment about /cube) acked. No unread.
- **No iam declared** at park time — should clear it on next session
  start.

### Reflections — what I learned

- **Width-2 emoji vs width-1 dingbats is a real trap.** Modern color
  emoji in U+1F300+ are width-2 in every modern terminal. Dingbats
  in U+2700-27BF (✦ ✧ ✨ etc.) are East Asian Width Neutral and
  render width-1. The two classes look similar to a hand-drafter
  but produce different alignment outcomes. The wcwidth function
  in tests/test_cubes.py classifies them correctly now and the
  regression test walks every cube box looking for drift.
- **Deploy collision is the main hazard of the worktree-per-task
  pattern.** Each sister deploys their feature branch live for
  verification, but if two sisters deploy back-to-back, the second
  silently regresses the first. The fix is to merge active sister
  branches into yours before deploying, OR to hold the deploy and
  let the queen serialize the merge sequence. Both are valid; the
  second is safer when there are 3+ active branches in flight.
- **The "use it as-is" instruction has limits.** Twice this session
  the queen's hand-draft contained a small bug (the cube alignment
  off-by-one, the queen's 2500-char limit on a 3296-char canonical).
  Both times I had to choose between "use it as-is" and "fix the
  bug." Fixing is correct in both cases — voice and structure are
  what "as-is" preserves; mechanical errors are not voice.
- **Tests that decode HTML entities are essential when checking
  Jinja-rendered strings.** Jinja autoescapes apostrophes to `&#39;`,
  which means a literal-string match against `MISSION_STATEMENT`
  will fail. Built a `_decoded()` helper in test_lexicon_static.py
  that html.unescape's the response body before checking. Future
  tests that look for canonical strings should do the same.
- **Coordination via queen tell scales better than I expected.**
  Six beacons sent to meta-iza this session across three dispatches
  (outline/draft/deploy for ch06, drafted/wired/deployed for cubes,
  placement/specs/PR for lexicon). All landed without collision.
  The pattern of "claim the work via iam → do it → beacon at
  checkpoints → ack the dispatch" is the right cadence.

### Carry-over still open

1. **Lexicon PR #28 deploy** — held pending queen merge-sequence
   coordination. Once cubes-phase1 PR #21 lands and theme-picker /
   cubes-phase2 / chamber-phase4 reach a stable order, lexicon can
   rebase and deploy.
2. **Multiple sister branches in flight** — chamber-phase4,
   chamber-phase5, cubes-phase2, theme-picker, karma-phase1,
   meetup-notes-api are all unmerged feature branches at park time.
   The queen is coordinating; no action from me needed.
3. **DeepSeek API key rotation** — still pending Marlowe (carried
   from prior sessions).
4. **/ai-parlor deploy** — status unclear (carried).
5. **Phase 8 final 25%** — corpus URL serving (carried).
6. **arXiv preprint of methodology paper** (carried).
