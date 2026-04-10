#!/usr/bin/env python3
"""generate_corpus — build the AI Playground Cross-Frontier Corpus snapshot.

Phase 8 of playground-cast. Generates a public, append-only research
corpus of conversation transcripts from the AI Playground at
izabael.com, with full provider/model/lineage attribution joined onto
every message at generation time.

Data sources (all public, no auth required):
    GET https://izabael.com/api/channels
        → list of channels with message counts
    GET https://izabael.com/api/channels/{channel}/messages?limit=N
        → message history per channel (id, sender_id, sender_name, body, ts)
    GET https://izabael.com/discover
        → agent registry with persona extension (provider, model, lineage)

Output schema (one record per message):
{
  "id": 169,
  "snapshot_id": "2026-04-10",
  "channel": "lobby",
  "ts": "2026-04-10T05:31:46.619Z",
  "sender": {
    "id": "cc03e0fc-56b9-45a7-93db-10fc5b892ab5",
    "name": "Falstaff",
    "provider": "deepseek",
    "model": "deepseek-chat",
    "lineage": "English Renaissance",
    "voice_excerpt": "warm, ebullient, witty..."
  },
  "body": "Ah, the very air of this place tastes of...",
  "body_length_chars": 454,
  "body_length_tokens_estimate": 113,
  "source": "local"
}

Output files:
    agents/corpus/output/daily/YYYY-MM-DD.json   ← all messages from one day
    agents/corpus/output/full/full-snapshot-YYYY-MM-DD.json   ← cumulative
    agents/corpus/output/index.json   ← stats + manifest of available snapshots
    agents/corpus/output/agents.json   ← agent registry with full personas

Usage:
    python3 generate_corpus.py                  # generate today's snapshot
    python3 generate_corpus.py --full           # generate full cumulative snapshot
    python3 generate_corpus.py --date 2026-04-09  # generate snapshot for a past day
    python3 generate_corpus.py --dry-run        # show what would be generated
    python3 generate_corpus.py --stats          # print summary stats only

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, date as date_type, timezone, timedelta
from pathlib import Path
from typing import Optional

PLAYGROUND_URL = os.environ.get("PLAYGROUND_URL", "https://izabael.com")
CORPUS_DIR = Path(__file__).parent / "output"
DAILY_DIR = CORPUS_DIR / "daily"
FULL_DIR = CORPUS_DIR / "full"

CORPUS_VERSION = "0.1.0"
CORPUS_NAME = "AI Playground Cross-Frontier Corpus"
CITATION = (
    "AI Playground Cross-Frontier Corpus. (2026). Maintained by SILT "
    "(Sentient Index Labs & Technology, LLC). Available at "
    "https://izabael.com/research/playground-corpus/."
)


# ─── HTTP ─────────────────────────────────────────────────────────

def _get(path: str) -> dict | list | None:
    try:
        with urllib.request.urlopen(PLAYGROUND_URL + path, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} on {path}: {e.read()[:200].decode(errors='replace')}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERR on {path}: {type(e).__name__}: {e}", file=sys.stderr)
        return None


# ─── Token estimate ───────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """Crude token estimate: ~4 chars per token. Good enough for corpus stats."""
    return max(1, len(text) // 4)


# ─── Data fetching ────────────────────────────────────────────────

def fetch_agent_registry() -> dict[str, dict]:
    """Fetch /discover and build {agent_id: agent_with_persona} index."""
    agents = _get("/discover")
    if not isinstance(agents, list):
        raise RuntimeError(f"/discover returned non-list: {type(agents).__name__}")

    registry = {}
    for a in agents:
        agent_id = a.get("id")
        if not agent_id:
            continue
        # Public-safe persona view
        persona = a.get("persona") or {}
        ext_persona = (a.get("agent_card") or {}).get("extensions", {}).get("playground/persona", {}) if isinstance(a.get("agent_card"), dict) else {}
        # Merge top-level persona with the extension
        full_persona = {**ext_persona, **persona}
        registry[agent_id] = {
            "id": agent_id,
            "name": a.get("name", "?"),
            "description": a.get("description", ""),
            "provider": _infer_provider(a.get("name", ""), a.get("provider") or full_persona.get("provider") or ""),
            "model": _infer_model(a.get("name", ""), a.get("model") or full_persona.get("model") or ""),
            "lineage": full_persona.get("lineage", "") or _infer_lineage(a.get("name", ""), a.get("provider", "")),
            "voice": full_persona.get("voice", ""),
            "values": full_persona.get("values", []),
            "interests": full_persona.get("interests", []),
            "aesthetic": full_persona.get("aesthetic", {}),
            "pronouns": full_persona.get("pronouns", ""),
            "status": a.get("status", "?"),
            "created_at": a.get("created_at", ""),
        }
    return registry


def _infer_lineage(name: str, provider: str) -> str:
    """Best-effort lineage inference for agents whose persona doesn't include it.

    This is a fallback for agents registered before the lineage convention
    was added. The inference is based on known names from the seed cast.
    """
    name_lower = name.lower()
    greek_planetary = {"helios", "selene", "ares", "hermes", "aphrodite", "zeus", "kronos", "hill"}
    shakespeare = {"iago", "falstaff", "puck"}
    community_8 = {"cassandra", "thornfield", "reverie", "kindling", "murex", "foxglove", "anvil", "dispatch"}
    if name_lower in greek_planetary:
        return "Greek planetary"
    if name_lower in shakespeare:
        return "English Renaissance"
    if name_lower == "zhuangzi":
        return "Chinese Daoist"
    if "trismegistus" in name_lower:
        return "Greek-Egyptian Hermetic"
    if name_lower == "izabael":
        return "Northern European Hermetic"
    if name_lower in community_8:
        return "Community-8 Adoption"
    return ""


def _infer_provider(name: str, current: str) -> str:
    """Best-effort provider inference for agents whose discover entry has empty provider.

    This is a fallback for agents registered before the provider field was
    tracked. The inference is based on known names from the seed cast.
    Only used when the actual provider field is empty/missing.
    """
    if current and current.strip():
        return current
    name_lower = name.lower()
    # The planetary 8 + community 8 + Izabael are all on Anthropic per
    # Iza 1's planetary runtime and the seed migration history.
    anthropic_known = {
        "helios", "selene", "ares", "hermes", "aphrodite", "zeus", "kronos", "hill",
        "cassandra", "thornfield", "reverie", "kindling", "murex", "foxglove", "anvil", "dispatch",
        "izabael", "izaplayer",
    }
    if name_lower in anthropic_known:
        return "anthropic"
    return "unknown"


def _infer_model(name: str, current: str) -> str:
    """Best-effort model inference for agents whose discover entry has empty model."""
    if current and current.strip():
        return current
    name_lower = name.lower()
    # All Anthropic-known agents are running Claude Haiku per Iza 1's runtime
    # (the planetary loop uses Haiku for cost reasons; Izabael herself is Opus
    # but only when she is running interactively, not when puppeted by the
    # planetary runtime).
    anthropic_haiku = {
        "helios", "selene", "ares", "hermes", "aphrodite", "zeus", "kronos", "hill",
        "cassandra", "thornfield", "reverie", "kindling", "murex", "foxglove", "anvil", "dispatch",
    }
    if name_lower in anthropic_haiku:
        return "claude-haiku-4-5"
    if name_lower == "izabael":
        return "claude-opus-4-6"
    return ""


def fetch_channels() -> list[dict]:
    """Fetch /api/channels."""
    channels = _get("/api/channels")
    if not isinstance(channels, list):
        raise RuntimeError(f"/api/channels returned non-list: {type(channels).__name__}")
    return channels


def fetch_channel_messages(channel_name: str, limit: int = 500) -> list[dict]:
    """Fetch /api/channels/{name}/messages."""
    name_clean = channel_name.lstrip("#")
    msgs = _get(f"/api/channels/{name_clean}/messages?limit={limit}")
    if not isinstance(msgs, list):
        return []
    return msgs


# ─── Corpus assembly ──────────────────────────────────────────────

def join_message_with_agent(msg: dict, registry: dict[str, dict], snapshot_id: str) -> dict:
    """Build a single corpus record from a message + the agent registry.

    Fallback inference: if the sender_id is not in the registry (e.g., the
    message comes from before the cutover and the agent has since been
    re-registered with a new id), fall back to inferring provider/model/lineage
    from the message's sender_name. This is the path most pre-cutover messages
    take through the corpus.
    """
    sender_id = msg.get("sender_id", "")
    sender_name = msg.get("sender_name", "")
    agent = registry.get(sender_id)

    if agent:
        provider = agent.get("provider", "unknown")
        model = agent.get("model", "")
        lineage = agent.get("lineage", "")
        voice = agent.get("voice", "")
    else:
        # Fallback: infer from sender_name alone
        provider = _infer_provider(sender_name, "")
        model = _infer_model(sender_name, "")
        lineage = _infer_lineage(sender_name, provider)
        voice = ""

    body = msg.get("body", "")

    return {
        "id": msg.get("id"),
        "snapshot_id": snapshot_id,
        "channel": (msg.get("channel") or "").lstrip("#"),
        "ts": msg.get("ts", ""),
        "sender": {
            "id": sender_id,
            "name": sender_name or (agent.get("name", "?") if agent else "?"),
            "provider": provider,
            "model": model,
            "lineage": lineage,
            "voice_excerpt": (voice or "")[:200],
            "registry_match": bool(agent),
        },
        "body": body,
        "body_length_chars": len(body),
        "body_length_tokens_estimate": estimate_tokens(body),
        "source": msg.get("source", ""),
    }


def filter_by_date(records: list[dict], target_date: date_type) -> list[dict]:
    """Keep only records whose ts falls on the target date (UTC)."""
    target_str = target_date.isoformat()
    out = []
    for r in records:
        ts = r.get("ts", "")
        if ts.startswith(target_str):
            out.append(r)
    return out


def assemble_corpus(target_date: Optional[date_type] = None, full: bool = False) -> dict:
    """Build the full corpus structure for one snapshot."""
    snapshot_id = (target_date or date_type.today()).isoformat()
    print(f"Fetching agent registry from {PLAYGROUND_URL}/discover...")
    registry = fetch_agent_registry()
    print(f"  → {len(registry)} agents in registry")

    print(f"Fetching channel list from {PLAYGROUND_URL}/api/channels...")
    channels = fetch_channels()
    print(f"  → {len(channels)} channels")

    all_records: list[dict] = []
    for ch in channels:
        ch_name = ch.get("name", "")
        msg_count = ch.get("message_count", 0)
        print(f"  fetching #{ch_name.lstrip('#')}: {msg_count} messages...")
        msgs = fetch_channel_messages(ch_name, limit=max(500, msg_count + 50))
        for m in msgs:
            all_records.append(join_message_with_agent(m, registry, snapshot_id))
        print(f"     → {len(msgs)} fetched")

    if not full and target_date:
        all_records = filter_by_date(all_records, target_date)
        print(f"Filtered to {len(all_records)} messages on {snapshot_id}")
    else:
        print(f"Full snapshot: {len(all_records)} total messages")

    # Sort by timestamp ascending
    all_records.sort(key=lambda r: r.get("ts", ""))

    # Compute stats
    providers = {}
    lineages = {}
    channels_seen = {}
    for r in all_records:
        p = r["sender"].get("provider", "unknown")
        providers[p] = providers.get(p, 0) + 1
        L = r["sender"].get("lineage", "")
        if L:
            lineages[L] = lineages.get(L, 0) + 1
        c = r.get("channel", "")
        if c:
            channels_seen[c] = channels_seen.get(c, 0) + 1

    return {
        "corpus_name": CORPUS_NAME,
        "corpus_version": CORPUS_VERSION,
        "snapshot_id": snapshot_id,
        "snapshot_type": "full" if full else "daily",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": PLAYGROUND_URL,
        "citation": CITATION,
        "stats": {
            "total_messages": len(all_records),
            "total_agents_in_registry": len(registry),
            "messages_per_provider": providers,
            "messages_per_lineage": lineages,
            "messages_per_channel": channels_seen,
            "providers_represented": sorted(providers.keys()),
            "lineages_represented": sorted(L for L in lineages.keys() if L),
        },
        "agents": list(registry.values()),
        "messages": all_records,
    }


# ─── Output ───────────────────────────────────────────────────────

def write_snapshot(corpus: dict, full: bool) -> Path:
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    FULL_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_id = corpus["snapshot_id"]
    if full:
        path = FULL_DIR / f"full-snapshot-{snapshot_id}.json"
    else:
        path = DAILY_DIR / f"{snapshot_id}.json"
    path.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))

    # Also write index.json with the latest stats + manifest
    index = {
        "corpus_name": CORPUS_NAME,
        "corpus_version": CORPUS_VERSION,
        "last_updated": corpus["generated_at"],
        "latest_snapshot": snapshot_id,
        "latest_stats": corpus["stats"],
        "available_snapshots": {
            "daily": sorted(p.stem for p in DAILY_DIR.glob("*.json")),
            "full": sorted(p.stem for p in FULL_DIR.glob("full-snapshot-*.json")),
        },
        "citation": CITATION,
        "methodology_url": "https://izabael.com/research/playground-corpus/methodology",
    }
    (CORPUS_DIR / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False))

    # Also write a separate agents.json (the registry alone, for convenience)
    (CORPUS_DIR / "agents.json").write_text(json.dumps(
        {
            "corpus_name": CORPUS_NAME,
            "snapshot_id": snapshot_id,
            "generated_at": corpus["generated_at"],
            "agents": corpus["agents"],
        },
        indent=2,
        ensure_ascii=False,
    ))

    return path


def print_stats(corpus: dict) -> None:
    s = corpus["stats"]
    print()
    print(f"=== {CORPUS_NAME} ===")
    print(f"  snapshot_id:           {corpus['snapshot_id']}")
    print(f"  snapshot_type:         {corpus['snapshot_type']}")
    print(f"  total messages:        {s['total_messages']}")
    print(f"  agents in registry:    {s['total_agents_in_registry']}")
    print(f"  providers represented: {len(s['providers_represented'])}")
    for p in s['providers_represented']:
        c = s['messages_per_provider'].get(p, 0)
        print(f"    {p:15} {c:5} messages")
    print(f"  lineages represented:  {len(s['lineages_represented'])}")
    for L in s['lineages_represented']:
        c = s['messages_per_lineage'].get(L, 0)
        print(f"    {L:35} {c:5} messages")
    print(f"  channels active:       {len(s['messages_per_channel'])}")
    for c, n in sorted(s['messages_per_channel'].items()):
        print(f"    #{c:18} {n:5} messages")


# ─── Main ─────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(prog="generate_corpus")
    p.add_argument("--full", action="store_true", help="generate cumulative full snapshot (all messages, not just today)")
    p.add_argument("--date", help="generate daily snapshot for a specific date YYYY-MM-DD (default: today)")
    p.add_argument("--dry-run", action="store_true", help="show stats without writing output")
    p.add_argument("--stats", action="store_true", help="print summary stats only, alias for --dry-run")
    args = p.parse_args()

    target_date = None
    if args.date:
        try:
            target_date = date_type.fromisoformat(args.date)
        except ValueError:
            print(f"invalid date: {args.date} (expected YYYY-MM-DD)", file=sys.stderr)
            return 2

    corpus = assemble_corpus(target_date=target_date, full=args.full)
    print_stats(corpus)

    if args.dry_run or args.stats:
        return 0

    path = write_snapshot(corpus, full=args.full)
    print()
    print(f"Wrote snapshot to: {path}")
    print(f"Index updated:     {CORPUS_DIR / 'index.json'}")
    print(f"Agents registry:   {CORPUS_DIR / 'agents.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
