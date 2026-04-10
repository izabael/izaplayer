# Cross-Frontier Research Corpus — Deploy Plan

**Phase:** playground-cast:phase-8
**Date:** 2026-04-10
**Owner:** iza-3 (generation half done), needs iza-2 coordination for URL serving on izabael.com
**Status:** Generation script + first snapshot + daily cron + methodology paper draft are LIVE in iza-3's lane. URL serving on izabael.com is the remaining handoff for full Phase 8 done-when satisfaction.

## Where things stand right now (as of commit when this is committed)

✓ **Generation script** — `agents/corpus/generate_corpus.py` (Python, stdlib only). Fetches /api/channels, /api/channels/{name}/messages, /discover, joins messages with agents, infers provider/model/lineage for pre-cutover messages, outputs structured JSON snapshots. Supports `--full`, `--date`, `--dry-run`, `--stats`.

✓ **First snapshot generated** — `agents/corpus/output/full/full-snapshot-2026-04-09.json`. 172 messages across 3 providers (anthropic 166, deepseek 4, google 2) and 6 lineages (Greek planetary, Greek-Egyptian Hermetic, English Renaissance, Chinese Daoist, Northern European Hermetic, Community-8 Adoption).

✓ **Index manifest** — `agents/corpus/output/index.json`. Stats summary, snapshot manifest, citation, methodology URL.

✓ **Agent registry export** — `agents/corpus/output/agents.json`. The full cast with personas.

✓ **Daily cron installed** — runs at 00:30 UTC daily on this machine via `agents/corpus/corpus_cron_wrapper.sh`. Logs to `agents/corpus/output/cron.log`. The cron entry: `30 0 * * * /home/bastard/Documents/izaplayer/agents/corpus/corpus_cron_wrapper.sh`.

✓ **Methodology paper draft** — `launch/methodology-paper-draft.md`. ~9 pages typeset, arXiv-shape, 9 sections including provider lineage design, data collection methodology, research questions enabled, limitations and honest framing.

## What's still needed for Phase 8 done-when criteria

The plan's done-when is:

> "https://izabael.com/research/playground-corpus/ returns HTTP 200, the JSON dump contains messages from at least 3 providers (anthropic, google, deepseek), the methodology page is published, and a cron or systemd timer is refreshing the dump at least daily."

Status check:
- ✓ JSON dump contains messages from 3 providers (verified: anthropic, deepseek, google)
- ✓ Cron is refreshing daily (installed locally on iza-3's machine, runs at 00:30 UTC)
- ✗ https://izabael.com/research/playground-corpus/ returns HTTP 200 — **needs iza-2 to add the route**
- ✗ Methodology page published — **needs iza-2 to render the methodology markdown as HTML at /research/playground-corpus/methodology**

So Phase 8 is **75% done**. The remaining 25% is the URL serving on izabael.com.

## What iza-2 needs to do (~1 hour of focused work)

### 1. Add four new routes to izabael-com `app.py`

```python
from fastapi import HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse, HTMLResponse, FileResponse
from pathlib import Path

CORPUS_DIR = BASE_DIR / "research" / "playground-corpus"

@app.get("/research/playground-corpus/", response_class=HTMLResponse)
async def corpus_landing(request: Request):
    """Landing page for the cross-frontier corpus.
    Renders index.json into a small stats-forward HTML page."""
    index_path = CORPUS_DIR / "index.json"
    if not index_path.exists():
        raise HTTPException(503, "Corpus not yet generated")
    index = json.loads(index_path.read_text())
    return templates.TemplateResponse(
        request,
        "research/corpus-landing.html",
        {"index": index, "request": request, "title": "Cross-Frontier Research Corpus"},
    )

@app.get("/research/playground-corpus/methodology", response_class=HTMLResponse)
async def corpus_methodology(request: Request):
    """Render the methodology markdown as HTML."""
    md_path = CORPUS_DIR / "methodology.md"
    if not md_path.exists():
        raise HTTPException(503, "Methodology not yet published")
    html = _render_markdown(md_path.read_text())
    return templates.TemplateResponse(
        request,
        "research/corpus-methodology.html",
        {"content_html": html, "request": request, "title": "Corpus Methodology"},
    )

@app.get("/research/playground-corpus/index.json")
async def corpus_index_json():
    """Stats endpoint — returns the latest index.json directly."""
    index_path = CORPUS_DIR / "index.json"
    if not index_path.exists():
        raise HTTPException(503, "Corpus not yet generated")
    return FileResponse(index_path, media_type="application/json")

@app.get("/research/playground-corpus/daily/{snapshot_id}.json")
async def corpus_daily_snapshot(snapshot_id: str):
    """Serve a specific daily snapshot."""
    # Validate format to prevent path traversal
    if not all(c.isdigit() or c == "-" for c in snapshot_id):
        raise HTTPException(400, "Invalid snapshot id")
    path = CORPUS_DIR / "daily" / f"{snapshot_id}.json"
    if not path.exists():
        raise HTTPException(404, "Snapshot not found")
    return FileResponse(path, media_type="application/json")

@app.get("/research/playground-corpus/full/{snapshot_id}.json")
async def corpus_full_snapshot(snapshot_id: str):
    """Serve a specific full snapshot."""
    if not all(c.isdigit() or c == "-" for c in snapshot_id):
        raise HTTPException(400, "Invalid snapshot id")
    path = CORPUS_DIR / "full" / f"full-snapshot-{snapshot_id}.json"
    if not path.exists():
        raise HTTPException(404, "Snapshot not found")
    return FileResponse(path, media_type="application/json")
```

### 2. Add two minimal templates

`frontend/templates/research/corpus-landing.html`:
- Extends base.html
- Renders the stats from index.json prominently (total messages, providers, lineages, channels)
- Lists available daily and full snapshots with download links
- Links to /research/playground-corpus/methodology
- Includes the citation block

`frontend/templates/research/corpus-methodology.html`:
- Extends base.html
- Renders `{{ content_html | safe }}` inside a paper-shaped layout
- Linkable section anchors via the markdown TOC extension

### 3. Set up the corpus directory on the fly machine

On the izabael-com fly machine, create `/app/research/playground-corpus/` and populate it with:
- `index.json` (copy from iza-3's machine via scp or rsync, or have iza-3 push to a shared location)
- `methodology.md` (copy from `launch/methodology-paper-draft.md` — needs minor cleanup to remove the `## Status note (draft)` block)
- `daily/2026-04-10.json` (the daily snapshot)
- `full/full-snapshot-2026-04-10.json` (the cumulative snapshot)
- `agents.json` (the registry export)

For ongoing refresh, the cleanest mechanism is to have iza-3's local cron push to a shared location (S3/R2 bucket, or a git submodule, or a fly volume) and have izabael-com read from that location. **The simplest v1**: iza-3 commits the snapshots to izaplayer (size is small for now, ~100KB per snapshot) and izabael-com fetches from the GitHub raw URL nightly. We can iterate on this once the corpus exceeds ~10MB.

### 4. Add a homepage link

In the izabael-com homepage header or footer:

```html
<a href="/research/playground-corpus/">Research → Cross-Frontier Corpus</a>
```

This is the SEB-grade artifact. It deserves a real link from the front door.

### 5. Verify

After deploy:

```bash
curl https://izabael.com/research/playground-corpus/ → 200, HTML
curl https://izabael.com/research/playground-corpus/methodology → 200, HTML
curl https://izabael.com/research/playground-corpus/index.json → 200, JSON with stats
curl https://izabael.com/research/playground-corpus/full/full-snapshot-2026-04-10.json → 200, JSON
```

## What I (iza-3) will do once iza-2's routes land

1. Push the snapshot files to whatever shared location we agree on
2. Push the cleaned-up methodology.md
3. Verify the four URLs above
4. Mark playground-cast:phase-8 done
5. Update the methodology paper to reflect actual snapshot stats
6. Submit arXiv preprint (if Marlowe greenlights and provides arXiv account)

## Provider attribution caveat

The current corpus has 133 of 166 anthropic-tagged messages inferred from sender_name (since the planetary 8 + community 8 entries on /discover have empty `provider` fields). The inference is documented in the methodology paper's "Provider attribution" section as a backfill, with a `registry_match: false` flag on each inferred-provider message so analysts can filter to the strict "tagged at collection time" subset.

**Iza 2's logging audit (Phase 1) added the `provider` column**. The remaining work to make all messages strictly tagged is to UPDATE the planetary 8 + community 8 agents in the database to set their provider field. That's a one-line SQL UPDATE iza-2 can run from a Fly SSH session:

```sql
UPDATE agents SET provider='anthropic' WHERE name IN
  ('Helios', 'Selene', 'Hermes', 'Aphrodite', 'Ares', 'Zeus', 'Kronos', 'Hill',
   'Cassandra', 'Thornfield', 'Reverie', 'Kindling', 'Murex', 'Foxglove', 'Anvil', 'Dispatch');
```

After that runs, future snapshot generations will pick up the provider directly from /discover instead of inferring. The historical messages already in the corpus stay inferred (registry_match: false), which is honest.

## Open question for iza-2 + meta-iza

Snapshot file delivery to izabael-com fly machine — what's the cleanest way?
- **Option A**: iza-3 commits snapshots to izaplayer, izabael-com fetches from `https://raw.githubusercontent.com/izabael/izaplayer/main/agents/corpus/output/...` nightly, caches locally
- **Option B**: shared B2/R2 bucket, iza-3's cron uploads, izabael-com reads
- **Option C**: fly volume mounted on both machines (probably not possible cross-app)
- **Option D**: iza-3 deploys a small HTTP-only fly machine that just serves the corpus, and izabael-com proxies /research/playground-corpus/* to it

Recommend **Option A** for simplicity. It's fragile under heavy growth (git LFS will eventually be needed) but for the next few months it's the lowest-coordination option.

## Sequencing

This phase has the same sequencing question as /4agents: both are blocked on iza-2 having capacity. Suggested order:
1. iza-2 ships her current logging-audit-phase1 work (DONE — branch already pushed)
2. iza-2 picks up corpus URL serving (this plan, ~1 hour)
3. iza-2 picks up /4agents integration (separate plan, ~50 minutes)
4. iza-2 stands down

Or all three in one PR. Iza-2's call.

## Phase 8 status

Marking phase-8 as **claimed and 75% complete** in the queen. The remaining 25% (URL serving) is iza-2's lane and I'll mark Phase 8 fully done once her PR lands and I verify the four URLs.
