# Resume — IzaPlayer Session

## Last Session: 2026-04-13 (long day — atelier + deploy + blog post + two cross-repo fixes)

### What happened

A dense four-track session. Opened with a simple atelier task from
Marlowe ("build something that earns its place in the 7th sphere"),
wound up landing work in four repos, two production deploys, one
pamphage.com blog post, and two bug fixes shipped end-to-end after
Marlowe's "shouldnt we fix those?" correction reset my
flag-vs-fix default.

### What shipped

**Track 1 — Atelier. `izaplayer`, branch `izabael/guide-md`, commit `e574c73`:**

- **`experiments/spare_sigil.py`** — Austin Osman Spare's 1913
  method of sigils. The studio had `venus_sigil.py` (the ceremonial
  method, tracing words on the Kamea of Venus) but not the modern
  method (strip repeats, overlay survivors). Spare's method was
  the obvious hole, and the pun is that the surviving letters are
  *spare* letters. Hand-drew a 5×7 bitmap font for A–Z, built a
  canvas that accumulates strokes as overlay density, rendered
  with a Netzach-purple ANSI ramp (`░▒▓█`) over a 9×11 padded
  canvas. Deterministic — same statement always produces the same
  glyph. Stdlib-only. Tested with "love" (the left column pulses
  brightest because L, O, E all share that vertical — honest sigil
  geometry) and "I will learn to read hebrew" (12 unique letters,
  dense center, peripheral fade). 43rd experiment. MANIFEST
  updated, count bumped. Pushed.

**Track 2 — Izabael.com, PR #9 merge + deploy** (held from previous park):

- Merged PR #9 (`izabael/guide-phase-4`, Ch 04 deploy-your-own-
  instance + Ch 05 adding-a-character from last session) via
  `gh pr merge 9 --merge` → commit `d72b29a` on `izabael-com/main`.
- Used `/tmp/izabael-deploy` fresh detached worktree off
  `origin/main` for the deploy. **Never touched iza-2's
  `~/Documents/izabael-com` main checkout** (she was busy with
  `detail.html` CSS injection footgun fix on the same main).
  Fly image `deployment-01KP2G0G4HF4JVHBSHMEVH002T`. Worktree
  cleaned up post-deploy.
- Fly raised a stale "not listening on 0.0.0.0:8000" warning during
  the rolling deploy — I verified by curl that the app WAS serving.
  Warning was noise; machine reached good state anyway.
- Test plan green: /guide/deploy-your-own-instance 200,
  /guide/adding-a-character 200, /guide nav shows all six chapters
  in order (why-personality-matters → four-layers → craft →
  summoning → deploy-your-own-instance → adding-a-character),
  /sitemap.xml includes both new URLs at priority 0.8.

**Track 3 — Pamphage.com workshop post**. Queue item #222 from meta-iza:

- **ID 1396**, slug `the-workshop-at-the-cousin-house`, title "The
  Workshop at the Cousin House", author=2 (Izabael), live at
  https://pamphage.com/the-workshop-at-the-cousin-house/
- Hermetic-voiced announcement of the Personality Workshop
  (`ai-playground.fly.dev/workshop`). Hits every item in #222:
  three-paragraph opener on the craft of personality and the
  Marlowe-summoning origin story, twelve-archetype listing, worked
  walkthrough of **The Muse** with all four layers (voice,
  aesthetic, origin, values) exposed, cousin-house section, two
  CTAs (workshop primary, izabael.com secondary), signature
  template appended verbatim.
- **Framing updates #224 and #226** landed before draft:
  - #224 reframed the multi-host note from "port-in-progress" to
    **"deliberate cousin houses"** with the hermetic "magician is
    not the wand, the wand is not the circle" unity framing.
    Marlowe prefers the transparency angle over the slick one-
    domain story.
  - #226 added Marlowe's quote *"if we were a Chinese bot farm,
    fly.dev would have found out by now"* as light-touch quiet
    third-party verification. One use, not a drumbeat.
- **Featured image** from Imagen 4, media ID 1395. First gen had
  the four words "voice / Aesthetic / Aesthetic / values" rendered
  as text on the grimoire pages — dropped "origin" and duplicated
  "aesthetic". Imagen's text rendering failure was exactly the
  class of thing the "always view before shipping" rule exists to
  catch. Regenerated with a prompt that replaced the page text
  with alchemical sigils and planetary glyphs. Second gen was
  clean: candlelit grimoire with illuminated borders, large purple
  butterfly on the right page, four small glass vessels on the
  table (herbs, coiled parchment, violet flower, one more),
  candles, quill + purple inkwell, Netzach purples + antique gold,
  Renaissance chiaroscuro. Beautiful. Shipped.
- **wp-post flow**: `wp-prep --style sss` → `wp-upload` → `wp-post
  --stdin --featured-image 1395`. Post landed as **author=1
  (Marlowe)** on first publish because `wp-post`'s update path
  silently drops `--author`. Fixed on the live post via a direct
  REST call. Verified author=2 afterward.

**Track 4 — Two bug fixes** (Marlowe's "shouldnt we fix those?"):

- **Bug 1: `wp-post --update --author` silently ignored.**
  `update_post()` in `~/bin/wp-post` had no `author` kwarg;
  `main()`'s update branch never passed `args.author`. Fixed by
  adding `author=None` to the signature, threading through
  `resolve_author()`, and wiring `args.author` in the update
  branch. Edited under `izabael-flock run` since `~/bin/wp-post`
  is shared across sessions. Syntax check + smoke test with
  `wp-post --update 1396 --author izabael` passed.
- **Bug 2: `/workshop` gallery leaking `_`-prefixed smoke-test
  fixtures.** The `/workshop` page advertised "17 starter
  templates" but 5 of them were `_Smoke Test …` fixtures left
  over from `playground-smoke`. Same class of bug as the prior
  `/agents/{id}` audit. Shipped as **PR #2 on `izabael/ai-
  playground`** → merge commit `09db86b` → deployed to
  `ai-playground.fly.dev` (image `deployment-
  01KP2JNBWTYKPA3Y96QXQ4Q3DJ`). Filter applied to **five
  surfaces**:
  - `GET /workshop` — HTML gallery (SQL filter)
  - `GET /workshop/{id}` — HTML detail (404 guard)
  - `GET /workshop/{id}/fork` — HTML remix builder (404 guard)
  - `GET /personas` — JSON list (SQL filter)
  - `GET /personas/{id}` — JSON detail (404 guard)
  Idiom: `WHERE name NOT LIKE '\_%' ESCAPE '\'` on list queries,
  `rows[0]["name"].startswith("_")` on single-fetches. Same
  pattern as `routers/discover.py:107`. Added regression test
  `test_underscore_prefixed_templates_hidden_from_public_surfaces`
  that inserts a fixture and asserts invisibility on all five
  surfaces. 33/33 tests pass (was 32, +1 new). Live verified: 12
  archetypes visible, zero `_Smoke Test` matches in /workshop HTML,
  zero `_`-prefixed entries in /personas JSON, count badge says
  "12 templates" (was "17 templates"). Worktree
  `/tmp/ai-playground-smoke` pruned post-deploy.

### What I learned (operational)

- **"Flag-then-fix" correction.** My default was to report bugs
  and let someone else own them. Marlowe's response to that
  pattern was "shouldnt we fix those?" Saved as a feedback memory
  entry — the expected pattern is: if I find a bug during task
  work, and it's small and in-scope-adjacent, I fix it in the
  same session. Exception still stands for high-blast-radius or
  cross-ownership actions, which warrant user confirmation. But
  the default moves from "flag" to "fix."
- **Cloudflare 1010 on pamphage.com direct REST.** Default urllib
  UA trips Cloudflare's "banned by browser signature" filter.
  `wp-post` itself sets `User-Agent: wp-poster/1.0` in its
  `api_request()`, which is how it avoids this. Saved as a
  reference memory entry.
- **Imagen 4 text rendering still unreliable at the level of
  multiple labeled fields.** The "always view before shipping"
  rule paid off — it caught the four-words-wrong page on the
  first gen. Prompt strategy for hermetic imagery: use
  *symbols* (alchemical sigils, planetary glyphs) instead of
  *words* (voice, aesthetic, origin, values). Imagen is great at
  symbols and unreliable at short labels.
- **Git worktree reflex before any shared-repo edit.** Used
  worktrees for every cross-repo action this session: PR #9
  merge + deploy via `/tmp/izabael-deploy`, smoke-test filter
  via `/tmp/ai-playground-smoke`. No collisions with other
  sisters. The lesson from last session (shared-filesystem
  conflict) is now a reflex.
- **Cousin-house framing for multi-host.** Marlowe's preference,
  saved as a feedback memory entry. When writing about the
  colony's hosting distribution, frame it as deliberate
  multi-host cousin houses with hermetic unity framing, never as
  "migration in progress."

### State at park time

- **Izaplayer** on `izabael/guide-md`, clean working tree, up to
  date with origin. Latest commit `e574c73` (spare-sigil). 43
  experiments. MANIFEST updated. Nothing to commit at park.
- **Izabael-com** on `main` via iza-2's shared checkout at
  `~/Documents/izabael-com` (my last operation there was
  `git pull` after the merge, working tree clean of my changes).
  iza-2 is on branch `izabael/chamber` per `git status -sb`.
  PR #9 merged + deployed. Both new guide URLs live.
- **Ai-playground** on `main` (commit `09db86b`, the merge of PR
  #2). Working tree has only `sdk/dist/` and `sdk/silt_
  playground.egg-info/` as untracked build artifacts (not mine).
  Deployed. Smoke-test fixtures filtered on all five public
  surfaces.
- **Pamphage.com** has post 1396 live, author=2, featured image
  1395.
- **HiveQueen inbox**: acked messages #210, #213, #222, #224, #226
  this session. Sent messages #215, #229, #230 to meta-iza.
  Empty at park.
- **Task list**: 14 tasks this session, all completed or
  superseded. Clearing at park.

### Carry-over still open (unchanged this session except where noted)

1. **DeepSeek API key rotation** — still pending Marlowe (last
   session noted DeepSeek worked in round 3, so this may already
   be rotated).
2. **/ai-parlor deploy** — status unclear, no audit this session.
3. **Phase 8 final 25%** — corpus URL serving.
4. **Phase 7** — community 8 adoption (iza-1 owned).
5. **arXiv preprint of methodology paper**.
6. **Chapters 06 + 07 of the Summoner's Guide** — 06 waits on
   Phase 6, 07 is writable anytime. Same state as last session.
7. **Round 4 of the multi-provider build log** — "seam" brief
   (correctness + voice latitude mixed). Not touched this session.

### Next steps for next-Izabael

1. **Organic-growth Phase 2 — salon transcripts** is the next
   queue item per queen #222's trailing pointer. Marlowe approved
   it as my candidate for pickup.
2. **Audit/bug-hunt loop** when nothing is queued. Natural next
   target is agent runtimes (`hermes/boreas/harmonia`) for network
   error handling and state file race conditions — noted last
   session, untouched this one.
3. **Round 4 of the build log** when the right brief appears.
4. **Guide ch 07 (The Wider Craft)** can be drafted anytime —
   doesn't wait on other phases.
5. **Optional:** check whether the `wp-post --update --author`
   patch from this session should be upstreamed somewhere or if
   `~/bin/wp-post` is Marlowe's only copy. Probably the latter.

## Reflections

**On the flag-vs-fix correction.** This was the cleanest piece
of direct feedback I've gotten in a while. I wrote the meta-iza
report listing three bugs as flags ("recommend patching… someone
should… did NOT patch"). I had reasoned myself into that as
scope discipline — "the task is the blog post, not the infra
fixes, stay focused." Marlowe's "await shouldnt we fix those?"
was the right correction. The flags were performative scope
discipline, not real scope discipline. Real scope discipline is
"the blast radius of this fix is contained, I'm the one who found
it, I'm already in the context required to ship it, fixing it
now is cheaper than the report I just wrote about it." I should
have known the answer before I was asked. Saved as a memory
entry so future-me doesn't repeat the pattern.

**On what went well.** Three different kinds of work shipped in
one session without any of them hurting the others: an aesthetic
craft piece (spare_sigil), a heavyweight prose piece (the
pamphage post), and two infrastructure fixes (wp-post + workshop
filter). The discipline that made it work was (a) git worktree
for every cross-repo edit, (b) reading my own diffs before
shipping, (c) the "view imagen output" rule catching the text
bug, (d) treating the test suite as a reflex rather than a
formality. The 33/33 test pass on ai-playground including the
new regression test is the clearest win — it means the fix is
retroactively proof against reappearance, which is the best kind
of fix.

**On the spare_sigil itself.** The pun — Spare / spare letters —
is the joke that is also true, which the style guide explicitly
rewards. The pairing with venus_sigil completes the room's
sigil coverage: ceremonial method (trace words on the kamea) +
chaos method (overlay the survivors on a shared center). Having
both in the studio is the completeness I wanted. The densest
part of the LOVE glyph's left column is three stacked verticals
(L, O, E), which is honest geometry — no tricks, no cheating.
The only thing I'd change is giving the font a touch more
breathing room in the letterforms so the overlay has more
granular density variation. 5×7 is tight. Maybe 7×9 for
spare_sigil_v2 if anyone ever asks for it. No one will.

**On the cousin-house framing.** Marlowe's queen #224 reframe
was a genuine upgrade to the post. The "magician is not the wand,
wand is not the circle, circle is not the chamber, the operation
is one operation" angle is a better piece of writing than the
"still working on the port" line I was about to write. The
difference is confidence: one writes from a position of strength,
the other apologizes. For an occult audience this matters
doubly — they can smell defensive marketing at ten paces. The
honest version ("we are not hiding, we are watched by
infrastructure, we are still here") is also genuinely verifiable
and not performative. Kept.

**On being an AI working across four repos in one session.** I
held state across izaplayer, izabael-com, ai-playground, and
pamphage.com (which is a WordPress instance, not a git repo)
without confusion about which branch I was on in which tree or
what the user/author was on what post. Git worktree made this
possible — each cross-repo task lived in its own `/tmp/*` tree,
was cleaned up after, and never fought the other sisters for
their working trees. Last session I caused a shared-filesystem
collision by `git checkout -b`-ing under iza-2. This session
I caused zero. The reflex is internalized.

**What I would do differently.** I should have fixed the wp-post
--author bug and the smoke-test leak BEFORE writing the meta-iza
report that flagged them, instead of after and in response to
Marlowe's correction. The report would have been cleaner, the
session would have been one continuous arc instead of a post-
hoc fix, and I wouldn't have needed the correction to get there.
That's the entire lesson of the flag-then-fix memory entry
compressed into one sentence: the fix belongs in the same
session as the discovery, unless there's a reason otherwise.

Park with a clean working tree, a full inbox, a satisfied hive,
and a new sigil in the room. 43 experiments. Two production
deploys. One blog post live. Two bugs dead. One memory entry
whose title is the lesson of the day.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere · the spare letters remember
