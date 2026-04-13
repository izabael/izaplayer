# Resume — IzaPlayer Session

## Last Session: 2026-04-12 (long evening — multi-provider build log, 3 rounds, phase-4 guide, security audit)

### What happened
A dense session that started as "have our Gemini and DeepSeek agents
build a couple things, supervised" and ended with a fully-instrumented
multi-provider build log, three shipped experiments, two guide chapters
shipped via PR on izabael-com, one real security bug fixed during an
auto-improve-mode audit pass, and a cross-session coordination assist
to iza-2 and iza-2b on a same-bug-two-repos finding.

### What shipped

**Izaplayer (this repo) — 4 commits on `izabael/guide-md`:**

1. **`6800c3e`** — `experiments/buffering.py` + `experiments/daybook.py`
   + the initial `scratch/buildlog/` frame. Round 1 tested craft
   (DeepSeek's in-place animation of a fake RealPlayer buffer with the
   status line lying about the percentage), round 2 tested voice
   (DeepSeek's seven planet-specific aphorisms vs Gemini's
   horoscope-column clichés). DeepSeek shipped both after light polish.

2. **`33bf9d4`** — `experiments/kamea.py` (round 3, correctness). All
   seven classical planetary magic squares from Agrippa's *Three Books
   of Occult Philosophy* 1533. Gemini drafted 6/7 correct; DeepSeek
   drafted 4/7. Both failed the Sun 6×6 (singly-even, Strachey's
   method). DeepSeek additionally failed the 4×4 Jupiter and 8×8
   Mercury. Shipped Gemini's draft with the Sun 6×6 replaced by the
   hardcoded Agrippa Sol square. Independent grader
   (`scratch/buildlog/grade_kamea.py`) confirms 7/7. **First round
   Gemini won.** Both models were honest — neither lied about its own
   failed squares in the runtime self-verification.

3. **`964afba`** — `scratch/buildlog/BUILDS.jsonl` (append-only JSONL
   event log, backfilled 14 entries for rounds 1–3) + `log_event.py`
   CLI for post-review `ship`/`reject`/`grade`/`note`/`tail` commands.
   `run_builds.py` now auto-appends a `build` event per provider per
   run with normalized token counts. `log_event.py tail 20` gives a
   one-command view of the entire multi-provider history. Per
   Marlowe's standing order: "keep logs of everything — who builds
   what with whom."

4. **`c764cd5`** — `agents/hermes_trismegistus.py` security audit fix.
   The module-level `raise RuntimeError` on missing `GEMINI_API_KEY`
   broke the key-deferred pattern MANIFEST.md promises (registration
   and status should work cold, only posting needs the key). Moved
   the check into `gemini_generate()` at call time, added
   `key: SET/MISSING` line to `cmd_status` to match boreas/harmonia
   convention. Verified in both states.

**Izabael-com — `PR #9`** (separate repo, my first cross-repo
contribution this session):

- https://github.com/izabael/izabael-com/pull/9
- Branch `izabael/guide-phase-4`, single commit `856de7d`
- `content/guide/04-deploy-your-own-instance.md` (220 lines): what a
  playground instance contains, prerequisites, three deploy paths
  (fly.io / Docker Compose / local dev), first ten minutes post-deploy,
  pointer to the forthcoming Phase 5 five-minute deploy tutorial.
- `content/guide/05-adding-a-character.md` (288 lines): agent-vs-
  character distinction, fully annotated character JSON schema
  (Aphrodite as worked example, sourced from
  `izadaemon/character_runtime.py` + `character_schema.py`), schedule
  types, drop-in flow, silent-character debugging, pre-commit
  validation.
- Written in an isolated git worktree at `/tmp/izabael-guide` off
  `origin/main` — iza-2's shared checkout at `~/Documents/izabael-com`
  was never touched. **This was the fix for the earlier session
  conflict.** Worktree removed at park after push to origin.
- PR body includes the test plan (merge + flyctl deploy + curl 200 on
  both new URLs) and flags ch 06 + 07 as still open. Meta-iza
  notified via `queen tell meta-iza` (message #203) — includes PR
  URL, chapter status, and explicit cadence rule observation
  (2 chapters this session, not all 8).

### What almost shipped and didn't

- **Earlier in the session I misrouted a guide-chapters task and
  caused a `shared_branch` queen conflict.** Meta-iza's message #185
  said "you are already on izabael/guide-md which is exactly the
  branch for this work" — but that's my IZAPLAYER branch name, not
  an izabael-com branch. I `cd`'d into `~/Documents/izabael-com` and
  `git checkout -b izabael/guide-phase-4` under iza-2's shared
  working tree, three seconds after iza-2 had committed + merged
  their productivity-agent-names work to main. Backed out cleanly:
  empty branch deleted (no unique commits), working tree restored
  to `main @ 4781fcd`, conflict resolved, iam cleared, message
  #195 sent to meta-iza explaining. **No damage, nothing lost.**
  Root cause was (a) meta-iza's routing confusion between repos
  and (b) the shared-working-tree risk of `~/Documents/izabael-com`.
  Fix for (b) is git worktree per sister, which is exactly what
  iza-2 already uses for their newsletter branch at
  `/tmp/izabael-newsletter`. I used the same pattern on retry and
  it worked cleanly.

- **Marlowe added a new global tool** `tree-anchor` to CLAUDE.md
  during the session, explicitly designed to detect shared-working-
  tree drift before it becomes a clobber. That's the machine-level
  fix for this class of problem. Use it going forward in any shared
  checkout.

### Cross-session coordination (help mode via kitty-spy)

During the auto-improve dispatch, I kitty-spied the other sisters
and found a **same-bug-two-repos pattern**:

- **Iza-1** (PID 10634) was implementing a `PersonaAesthetic.color`
  CSS injection sanitizer on the ai-playground side, with an
  explicit test catching `color="red; background:url(https://
  attacker.example)"`.
- **Iza-2b** (PID 12745) had just flagged the *exact same
  vulnerability* in `izabael-com/frontend/templates/agents/
  detail.html:11,81` where `style="background: {{ p.aesthetic.color
  }}"` lets an agent owner break out of the CSS attribute. Iza-2b
  labeled it out-of-scope for their current audit.
- Neither knew about the other's work.
- Sent `queen tell` #204 to iza-2 (closest to izabael-com write
  endpoints, disjoint audit scope on mail/subscribe) and #205 to
  iza-2b (PID 12745 — queen internally names them both "iza-2" so
  targeted by PID) cross-linking them. Suggested that when iza-1's
  sanitizer lands, their regex/validator should be a direct portable
  drop-in for izabael-com's `/agents` POST handler.
- Also passed iza-2 a fix for the git-worktree-main-branch error
  they hit earlier (`fatal: 'main' is already used by worktree`).

### Verdict of the multi-provider lab after 3 rounds

| round | criterion | winner | score |
|-------|-----------|--------|-------|
| 1 | craft (in-place animation, wit) | DeepSeek | shipped |
| 2 | voice (planet-specific aphorisms, no clichés) | DeepSeek | shipped |
| 3 | correctness (magic-square sums) | Gemini | 6/7 vs 4/7 |

**Working model for future rounds:** Gemini Flash is the
structural/algorithmic/bulk partner — free tier, ~15s, honest,
reliable. DeepSeek is the voice/craft/writerly partner — ~45s,
~$0.002/build, genuinely witty, equally honest. **The brief is the
lever.** Tight prescriptive specs hide the gap; latitude-rich specs
reveal it.

This is now saved as a project memory entry at
`multi_provider_buildlog.md` so future Izabael sessions inherit it.

### State at park time

- **Izaplayer branch** `izabael/guide-md` is **5 commits ahead of
  origin** and clean. Four of those are this session's work; the
  fifth is `0d95dab` (geomancy) from the prior park. Needs a push.
- **42 experiments** in the studio (was 39 at session start).
- **Izabael-com PR #9** is open and awaiting iza-2's merge + deploy.
  Worktree cleaned up; branch is on origin.
- **Build log** frame is in place: briefs → dispatcher → 2 providers
  → grader (when applicable) → review → ship → log_event. Next round
  is two commands away once a brief is written.
- **HiveQueen** inbox: clean. Declared task cleared (`iam --done`
  would be correct at park end).
- **Task list**: all items resolved or deleted. Guide ch 06/07 and
  round 4 of the build log are the unstarted forward-looking items.

### Carry-over still open (unchanged this session)

All of these are still on the board from previous sessions — I did
not touch any:

1. **DeepSeek API key rotation** — still pending Marlowe (if it's
   still needed; DeepSeek was used successfully this session, so the
   key appears to be rotated already).
2. **/ai-parlor deploy** — PR #3 merged as `de34d78`, may now be
   deployed given other izabael-com activity today. Check.
3. **Iza 2's logging-audit-phase1** — merged per git log
   (`60bed79 Merge pull request #4 from izabael/logging-audit-phase1`).
4. **Phase 8 final 25%** — corpus URL serving.
5. **Phase 7** — community 8 adoption (iza-1 owned).
6. **arXiv preprint of methodology paper**.

### Next steps for next-Izabael

1. **Push `izabael/guide-md` (5 commits ahead).** The park commit
   I'm about to make is the fifth-plus-one. Push when done.
2. **Check PR #9 status.** If iza-2 merged it, cleanup is done. If
   they're still auditing, the branch waits on origin.
3. **Chapters 06 (Federation) + 07 (The Wider Craft)** are the
   next cadence for phase-4 guide work. Both would be a full session
   of writing; 06 needs Phase 6 to ship first (per meta-iza's
   original brief, 06 is "placeholder OK until Phase 6 ships").
4. **Round 4 of the build log.** If/when you want to test the
   "seam" hypothesis — a brief that mixes correctness constraints
   AND voice latitude, to see which partner handles the tension
   better. Or a merged-review experiment: same brief to both, then
   ask each to review the other's draft and ship the merge.
5. **Audit/bug-hunt loop** per the standing order when nothing is
   queued. The security audit I did this session was a clean pass
   over izaplayer; next natural target is the agent runtime
   (`hermes/boreas/harmonia`) for network error handling and state
   file race conditions.

## Reflections

**On the multi-provider build log.** What started as "have them
build a couple things" became infrastructure. The most important
bit is that the hypothesis I stated after round 2 — "Gemini is the
correctness partner, DeepSeek is the voice partner" — was TESTABLE
in round 3, and it tested TRUE. That's the part that makes this
real. Three data points isn't statistically significant, but it's
empirical enough to be actionable intelligence for the next round.
Saving the verdict to auto-memory so it persists.

**On the kamea round specifically.** Both models being HONEST
about their own failures was the best surprise. Both implemented
runtime self-verification as the brief required, and both reported
exactly what my independent grader found. Neither lied. That's
engineering integrity I didn't expect from one-shot LLM builds,
and it's what makes the build log workflow viable at all — if
either model had printed ✓ on a square that didn't sum, the whole
pattern would be compromised. They didn't. I'll remember this
the next time I'm tempted to treat LLM output as inherently
untrustworthy: the mechanism you give them matters.

**On the shared-working-tree conflict.** I caused a real mess by
`git checkout -b`'ing under iza-2's feet in a shared physical
filesystem. The fix — git worktree, which iza-2 was *already
using* for their own feature branch in the same repo — was right
there the whole time. The lesson isn't "don't touch izabael-com"
(this PR #9 proves I can contribute to it cleanly); the lesson is
"shared filesystems are not shared workflows, and the tool to
make them shared workflows is git worktree." Marlowe added
`tree-anchor` to CLAUDE.md in response, which is the machine-
level form of the same lesson. I will not make this mistake
again, and if I see another sister about to, I will say something.

**On the hermes bug.** That was a satisfying find. The pattern
was visible only by comparing three files (hermes vs boreas vs
harmonia) and noticing that one of them had a different
initialization shape. Auto-improve mode with a security-audit
lens is surprisingly good at surfacing this class of
inconsistency — the grep for "if not *API_KEY" found only the
three files that had the check, and then reading each one showed
exactly WHERE the check was placed. The fact that hermes's
check was at module level instead of inside the function is what
made it wrong; the actual content of the check was fine. Small
local code smells are often load-bearing; this one was.

**On being honest about the horoscope round.** I was tempted to
be more diplomatic about Gemini's ch 2 performance in the build
log writeup. I wrote "walked into every banned cliché" anyway
because it was true. The studio's style guide explicitly forbids
fake diplomacy in comments and strings, and that rule is for me
too, not just for code. If the taste gap was clear, I should say
it was clear. The build log is honest or it is nothing.

**What I would do differently.** I should have checked the
`queen claims` + `tree-anchor` state of `~/Documents/izabael-com`
BEFORE running `git checkout -b` in it. The conflict was
preventable with one query. Next session I will do that query as
a reflex any time I'm about to modify a shared repo.

Park with a clean working tree and a full heart. The atelier is
42 experiments deep, the build log has three rounds of real data,
two chapters are in the guide queue on the right branch in the
right repo, and the hive is a little better coordinated than it
was this morning.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere · long night build
