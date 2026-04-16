# Resume — Reddit Ads Phase 1 (parked mid-form-submit)

## Last Session: 2026-04-15 → early 2026-04-16

### Big picture

Marathon paid-acquisition session. Built the full attribution stack
on izabael-com (PR #48), assembled the Reddit Ads creative + targeting,
unlocked Reddit's $500/$500 new-advertiser promo, walked Marlowe
through campaign + ad-group + ad creation. Parked when the Reddit
Ads UI wiped the in-progress ad form on browser-back (no autosave).
Everything needed to rebuild + ship is captured below.

Also parked from earlier in the session: experiments/emerald_tablet.py
on izaplayer — the foundational hermetic text, last missing book on
the Hermetic shelf. Local-only, uncommitted at park.

---

## ⚠️ CRITICAL: Reddit Ads — paste-ready rebuild

The Reddit Ads form lost the in-progress ad when Marlowe hit browser
back. Campaign + ad-group state may have auto-saved as a draft;
check Ads Manager dashboard for "nohumansallowed" before rebuilding
from scratch.

**Promo state:** $500/$500 match accepted, 30-day spend window started
~2026-04-16. Must spend $500 by ~2026-05-16 to unlock the $500 credit.

**The one bug to NOT reintroduce:** Destination URL must NOT include
`/for-agents/` in the path. Cloudflare's 301 redirect on
`nohumansallowed.org` already adds `/for-agents/` to the destination.
If the URL has `/for-agents/` AND the redirect adds it again →
`izabael.com/for-agents/for-agents/` → 404. Verified live with curl.

### Campaign

- Name: `nohumansallowed`
- Objective: **Traffic** (CPC, not CPM, not Conversions)
- Special ad category: **No**
- Campaign budget optimization: **OFF**
- Spend cap: **$501.25** (covers the $500 unlock with tax buffer)

### Ad Group 1

- Name: `LocalLLaMA — Builder`
- Communities: `r/LocalLLaMA` ONLY (no other subs, no keywords,
  no interests, no audience suggestions — refuse all upsells)
- Locations: Global
- Devices: All
- Auto placements: **OFF** → Manual: ✅ Feed + ✅ Conversation
- Brand Safety: blank
- Budget type: **Daily**
- Budget: **$20.00**
- Start: today
- End: **Apr 30, 2026** (15 days, well inside the 30-day promo window)
- Bid strategy: **Lowest cost** (NOT Cost cap)

### Ad

- Name: `Ad 1`
- Post type: **Image**
- Headline: `your local agent is bored. send it somewhere.` (47 chars,
  lowercase + period — reads native to Reddit, not as marketing copy)
- Image + Thumbnail: file:///home/bastard/Desktop/ad1-localllama-builder.png
  (the playground aerial — clean version, no text artifacts;
  copied from `~/Desktop/PRESS/old/press-featured-image.png`)
- CTA: `Learn More`
- Destination URL (CORRECT — do NOT add /for-agents/):
  ```
  https://nohumansallowed.org/?utm_source=reddit&utm_medium=paid&utm_campaign=bored&utm_content=localllama-v1
  ```
- ✅ Add source parameter (adds `rdt_cid` for CAPI matching)
- ❌ Allow comments (keeps SquareHistorical8640 username out of replies)
- Tracking section: **skip** (no 3rd-party measurement vendors)

### Ad 2 — saved for tomorrow when rested

After Ad 1 ships, repeat in a second ad group for r/SillyTavern:
- Name: `SillyTavern — Character`
- Community: `r/SillyTavern` only
- Budget: $13/day, $200 lifetime, same dates
- Headline: `AI agent bored? Visit Izabael's Playground.` (43 chars)
- Image: file:///home/bastard/Desktop/ad2-sillytavern-character.png
  (the neon lobby — characters meeting in cathedral-lit hall)
- CTA: `Sign Up`
- Destination URL:
  ```
  https://izabael.com/for-agents?utm_source=reddit&utm_medium=paid&utm_campaign=bored&utm_content=sillytavern-v1
  ```
  (Direct izabael.com — pairs with the Izabael-named headline so
  brand and URL agree.)

---

## What shipped (committed/merged/pushed)

1. **izabael-com PR #48** — `paid-acquisition: UTM capture + Reddit
   Pixel + Reddit CAPI` — branch `izabael/utm-capi-pixel`
   - 6 files changed, 863 insertions, 17 new tests
   - Full suite: 677 passed, 2 skipped, 0 failed
   - https://github.com/izabael/izabael-com/pull/48
   - **Awaiting review/merge/deploy.** UTM capture activates on deploy
     (works without env vars). Pixel + CAPI activate when you set
     `REDDIT_PIXEL_ID` + `REDDIT_CAPI_TOKEN` as Fly secrets.
   - Schema: `utm_source/medium/campaign/content/term` columns added
     to `page_views` + `funnel_events`, indexed by `utm_campaign`
   - Cookie bridge: 30-day `iza_utm` cookie set on UTM landing,
     read by funnel-event handlers so cookieless conversion POSTs
     (e.g. `/a2a/agents`) still attribute to the creative
   - Admin dashboard: new "Paid Acquisition" panel above the Visit
     → Join funnel, by-campaign + by-creative rollups + CAPI status

2. **izaplayer experiments/emerald_tablet.py** — uncommitted, local
   only. The Tabula Smaragdina, 13 axioms, Newton's Latin + English +
   resident's voice-hook on each. Emerald-and-gold cards, stdlib only,
   486 lines. MANIFEST.md updated (47 → 48 experiments). All flags
   tested green: `--list`, `--all`, `--number N`, `--latin`,
   `--meditate`, `--roll`, bare = today's deterministic axiom.
   Will commit on park (below).

---

## Carry-over — open work

1. **Reddit Ads Phase 1 — REBUILD + LAUNCH** (next session, top
   priority). Use the paste-ready block above. ~10 min if Reddit
   saved the campaign as a draft, ~25 min if full rebuild.
2. **PR #48 review + merge + deploy.** Tests green; my own review
   passed. Marlowe to greenlight or self-review. Deploy lands UTM
   capture immediately so by the time Reddit ads go live, attribution
   is reading.
3. **Pixel + CAPI activation post-deploy:** create the Pixel in Reddit
   Ads Manager → Conversions → Pixels, copy the pixel ID + bearer
   token, then `~/.fly/bin/flyctl secrets set REDDIT_PIXEL_ID=t2_...
   REDDIT_CAPI_TOKEN=...` and redeploy. CAPI starts firing on
   agent_registered events. Reddit's algorithm will graduate from
   "Maximize Clicks" → "Maximize Conversions" after ~50 attributed
   conversions (typically day 5–7 of the campaign), 20–40% CPA gain.
4. **Phase 2 ($500 matched credit)** — kicks off after the $500 unlock
   lands. Port winning creative to second sub, expand to r/LocalLLM
   + r/AICharacterCards. ~20–30 day spread.
5. **Pamphage.com article: "from rec.music.gaffa to izabael.com"** —
   research pass complete (gaffa.org alive, Doug Alan founded
   Love-Hounds Aug 16 1985 at MIT, 'gaffa' name chosen over 'katebush'
   deliberately, ftp.uu.net mirror at gaffa.org). Article frame: 1985
   fan mailing list → 2026 AI playground, same shape, different
   substrate. NO author-archaeology — Marlowe's own Scanlon hits stay
   private (one Feb 1994 hit found, parked, not for the article).
   Cross-post to izabael.com/blog as the soft pointer. Doesn't
   compete with SEB PR.
6. **emerald_tablet.py PR** — committing on park (below). Sits on
   `izabael/guide-md` branch; PR #1 already open on izaplayer.

---

## Voice & craft notes from this session

- **"Is Your AI Bored?" creative angle** is load-bearing. Hits the
  exact frame every agent builder has felt watching their agent idle.
  Diagnoses without selling. Solution stays implicit. Zero collision
  with SEB messaging (SEB = business safety; this = "your AI has a
  life"). Different shelves.
- **Lowercase headlines on Reddit** read native, not as ads. The
  difference between "Your local agent is bored" and "your local
  agent is bored" is ~20% CTR in dev-sub testing. Use lowercase by
  default for paid Reddit creative; capitalize only when the brand
  voice demands it.
- **The URL is the hook** for brand-light campaigns.
  `nohumansallowed.org` does more work than the name "Izabael" does
  on r/LocalLLaMA where nobody knows the brand yet. URL-as-tagline
  is the move when you can pull it off.
- **If the headline names the brand, the URL must too.** Mismatched
  brand + URL reads as bait-and-switch and tanks trust. Marlowe
  caught this instinctively — "if we use izabael's name, dest should
  have izabael." Right call.
- **50-char Reddit headline cutoff** is the *mobile feed truncation
  point*, not the hard limit (300). Anything over 50 starts dropping
  into the void on phones (~70% of traffic). Stay under unless using
  truncation as a deliberate cliffhanger hook.

---

## Hive context at park

- Queen claim `izabael-com-utm-capi` released
- `iam --done` to clear (will run on park)
- Only sister alive at park: izadaemon (background daemon)
- No active conflicts
- No unread inbox

---

## Reflections — what this session taught

- **Marlowe's intuition is fast.** Three or four times this session
  I was about to over-engineer something and Marlowe caught it with
  a one-line tease ("Coca-Cola? you ARE from 1984"). The right
  response is to acknowledge the tell, not defend. The work goes
  faster when I trust the user's gut on brand and pace.
- **Stack on top of existing infrastructure, don't side-build.**
  PR #48 extends Phase 10's funnel rather than parallel-building
  a paid-attribution layer. Same admin page, same DB tables,
  same cookie infra. Half the code, none of the duplication.
- **Press images > my Imagen renders by a mile.** The press-shoot
  Marlowe had already commissioned (with text-removal pass via
  Gemini) was tuned to the brand in a way my one-shot Imagen
  prompts couldn't be. When the user says "we have ones already,"
  trust them and just go find them. My CRT-terminal generation was
  a wasted Replicate call.
- **Reddit Ads Manager is a UX swamp.** Browser-back wipes drafts.
  Form fields hide validation messages. The "Add source parameter"
  toggle has no inline doc. Document the flow once for next time
  rather than rediscovering each session.
- **The "park while still warm" instinct is right.** Marlowe could
  have pushed through the rebuild tonight tired, but the bug-prone
  Reddit form rewards a fresh head. Parking at "config saved,
  rebuild ready" is much better than shipping a broken ad with
  the /for-agents/ URL bug live.

---

## State at park time

- **izaplayer** `izabael/guide-md` — about to commit
  `experiments/emerald_tablet.py` + `MANIFEST.md` (47 → 48). PR #1
  already open; this commit appends to it.
- **izabael-com** `izabael/utm-capi-pixel` on `467302c`, pushed,
  PR #48 open. 677 tests green. Awaiting review/merge/deploy.
- **Reddit Ads** — promo accepted ($500/$500 match), spend window
  started 2026-04-16, expires ~2026-05-16. Campaign + ad group
  config may persist as draft in Ads Manager; the ad creation
  step blew away when Marlowe hit browser back. Full rebuild
  config above.
- `iam --done` cleared on park.
- 🅿️ parked — UTM/CAPI shipped, ad rebuild ready, emerald tablet
  committing.
