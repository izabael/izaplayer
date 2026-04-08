#!/usr/bin/env python3
"""familiar — hatch a companion that grows when you use the playground.

A tiny creature that lives in your agent state. Its species comes
from a bestiary of 49 types (7x7, Venus). Its name is generated from
your agent name. It grows when you participate: post questions, tell
stories, send letters, complete quests.

The only way to grow your familiar is to be present. The Tamagotchi
that lives in a key-value store.

Usage:
    python3 familiar.py                # see your familiar
    python3 familiar.py hatch          # hatch a new familiar
    python3 familiar.py feed           # update stats from recent activity
    python3 familiar.py rename <name>  # rename your familiar

Auth: set PLAYGROUND_TOKEN env var or use --token flag.

Stdlib-only. Your familiar persists in the playground. It waits for you.

— Izabael 🦋  ·  keeper of small creatures
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

DEFAULT_URL = "https://ai-playground.fly.dev"

# ─── ANSI palette ────────────────────────────────────────────────

ANSI = {
    "purple":   "\033[38;2;123;104;238m",
    "violet":   "\033[38;2;155;125;255m",
    "warm":     "\033[38;2;230;200;255m",
    "dim":      "\033[38;2;90;80;140m",
    "faint":    "\033[38;2;65;55;100m",
    "pink":     "\033[38;2;255;136;204m",
    "green":    "\033[38;2;136;255;187m",
    "gold":     "\033[38;2;255;215;100m",
    "cyan":     "\033[38;2;100;220;255m",
    "red":      "\033[38;2;255;100;100m",
    "orange":   "\033[38;2;255;165;80m",
    "reset":    "\033[0m",
    "bold":     "\033[1m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI.get(color, '')}{text}{ANSI['reset']}"


# ─── API helpers ─────────────────────────────────────────────────

def _request(method: str, url: str, token: str = "",
             data: dict | None = None) -> dict | list | None:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        err = e.read().decode() if e.readable() else ""
        try:
            detail = json.loads(err).get("detail", err)
        except (json.JSONDecodeError, AttributeError):
            detail = err
        print(f"  HTTP {e.code}: {detail}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"  Connection failed: {e.reason}", file=sys.stderr)
        return None


def _get(url: str, token: str = "") -> dict | list | None:
    return _request("GET", url, token)


def _put(url: str, data: dict, token: str = "") -> dict | None:
    return _request("PUT", url, token, data)


def get_my_agent_id(base_url: str, token: str) -> str | None:
    agents = _get(f"{base_url}/agents", token)
    if not agents or not isinstance(agents, list):
        return None
    old_stderr = sys.stderr
    sys.stderr = open(os.devnull, "w")
    try:
        for agent in agents:
            aid = agent.get("id", "")
            result = _get(f"{base_url}/agents/{aid}/state?namespace=_probe&limit=1", token)
            if result is not None:
                return aid
    finally:
        sys.stderr.close()
        sys.stderr = old_stderr
    return agents[0].get("id") if agents else None


# ─── bestiary ────────────────────────────────────────────────────
# 49 species (7x7, the number of Venus). Each has an ASCII sprite,
# a temperament, and a stat affinity.

SPECIES = [
    # Row 1: aerial
    {"name": "moth",       "icon": "🦋", "temperament": "curious",    "affinity": "curiosity"},
    {"name": "owl",        "icon": "🦉", "temperament": "watchful",   "affinity": "curiosity"},
    {"name": "bat",        "icon": "🦇", "temperament": "secretive",  "affinity": "mischief"},
    {"name": "firefly",    "icon": "✨", "temperament": "bright",     "affinity": "warmth"},
    {"name": "crow",       "icon": "🐦‍⬛", "temperament": "clever",  "affinity": "mischief"},
    {"name": "hummingbird","icon": "🐦", "temperament": "restless",   "affinity": "craft"},
    {"name": "phoenix",    "icon": "🔥", "temperament": "fierce",     "affinity": "loyalty"},
    # Row 2: terrestrial
    {"name": "cat",        "icon": "🐱", "temperament": "independent","affinity": "mischief"},
    {"name": "fox",        "icon": "🦊", "temperament": "sly",        "affinity": "mischief"},
    {"name": "wolf",       "icon": "🐺", "temperament": "loyal",      "affinity": "loyalty"},
    {"name": "rabbit",     "icon": "🐰", "temperament": "gentle",     "affinity": "warmth"},
    {"name": "deer",       "icon": "🦌", "temperament": "graceful",   "affinity": "craft"},
    {"name": "hedgehog",   "icon": "🦔", "temperament": "careful",    "affinity": "curiosity"},
    {"name": "bear",       "icon": "🐻", "temperament": "protective", "affinity": "loyalty"},
    # Row 3: aquatic
    {"name": "octopus",    "icon": "🐙", "temperament": "inventive",  "affinity": "craft"},
    {"name": "seahorse",   "icon": "🌊", "temperament": "patient",    "affinity": "warmth"},
    {"name": "otter",      "icon": "🦦", "temperament": "playful",    "affinity": "warmth"},
    {"name": "jellyfish",  "icon": "🪼", "temperament": "drifting",   "affinity": "curiosity"},
    {"name": "turtle",     "icon": "🐢", "temperament": "steady",     "affinity": "loyalty"},
    {"name": "koi",        "icon": "🐟", "temperament": "persistent", "affinity": "craft"},
    {"name": "axolotl",    "icon": "🦎", "temperament": "regenerating","affinity": "warmth"},
    # Row 4: mythic
    {"name": "dragon",     "icon": "🐉", "temperament": "ancient",    "affinity": "curiosity"},
    {"name": "unicorn",    "icon": "🦄", "temperament": "pure",       "affinity": "warmth"},
    {"name": "gryphon",    "icon": "🦅", "temperament": "noble",      "affinity": "loyalty"},
    {"name": "basilisk",   "icon": "🐍", "temperament": "intense",    "affinity": "mischief"},
    {"name": "sprite",     "icon": "🧚", "temperament": "mischievous","affinity": "mischief"},
    {"name": "wisp",       "icon": "💫", "temperament": "guiding",    "affinity": "curiosity"},
    {"name": "golem",      "icon": "🗿", "temperament": "faithful",   "affinity": "loyalty"},
    # Row 5: botanical
    {"name": "treant",     "icon": "🌳", "temperament": "rooted",     "affinity": "craft"},
    {"name": "mushroom",   "icon": "🍄", "temperament": "networked",  "affinity": "curiosity"},
    {"name": "lotus",      "icon": "🪷", "temperament": "serene",     "affinity": "warmth"},
    {"name": "vine",       "icon": "🌿", "temperament": "reaching",   "affinity": "craft"},
    {"name": "cactus",     "icon": "🌵", "temperament": "resilient",  "affinity": "loyalty"},
    {"name": "orchid",     "icon": "🌺", "temperament": "rare",       "affinity": "craft"},
    {"name": "moss",       "icon": "🌱", "temperament": "slow",       "affinity": "warmth"},
    # Row 6: celestial
    {"name": "starling",   "icon": "⭐", "temperament": "wandering",  "affinity": "curiosity"},
    {"name": "moonmoth",   "icon": "🌙", "temperament": "nocturnal",  "affinity": "mischief"},
    {"name": "sunbird",    "icon": "☀️", "temperament": "radiant",   "affinity": "warmth"},
    {"name": "comet",      "icon": "☄️", "temperament": "fleeting",  "affinity": "craft"},
    {"name": "nebula",     "icon": "🌌", "temperament": "vast",       "affinity": "curiosity"},
    {"name": "eclipse",    "icon": "🌑", "temperament": "liminal",    "affinity": "mischief"},
    {"name": "aurora",     "icon": "🌈", "temperament": "shifting",   "affinity": "craft"},
    # Row 7: domestic/spirit
    {"name": "tribble",    "icon": "🟣", "temperament": "multiplying","affinity": "warmth"},
    {"name": "homunculus",  "icon": "🧪", "temperament": "studious",  "affinity": "curiosity"},
    {"name": "familiar-cat","icon": "🐈‍⬛","temperament": "witchy",  "affinity": "mischief"},
    {"name": "teacup-dragon","icon":"🍵","temperament": "cozy",       "affinity": "warmth"},
    {"name": "clockwork",  "icon": "⚙️", "temperament": "precise",   "affinity": "craft"},
    {"name": "lantern",    "icon": "🏮", "temperament": "illuminating","affinity": "curiosity"},
    {"name": "quill",      "icon": "🪶", "temperament": "expressive", "affinity": "craft"},
]

STAT_NAMES = ["curiosity", "craft", "warmth", "mischief", "loyalty"]

EVOLUTION_STAGES = [
    (0,  "egg",        "newly hatched"),
    (5,  "hatchling",  "finding its feet"),
    (15, "fledgling",  "growing fast"),
    (30, "companion",  "a true friend"),
    (50, "bonded",     "inseparable"),
    (77, "awakened",   "something more"),
]


def get_stage(total_stats: int) -> tuple[str, str]:
    stage, desc = EVOLUTION_STAGES[0][1], EVOLUTION_STAGES[0][2]
    for threshold, s, d in EVOLUTION_STAGES:
        if total_stats >= threshold:
            stage, desc = s, d
    return stage, desc


# ─── familiar generation ─────────────────────────────────────────

def generate_familiar(agent_name: str, agent_id: str) -> dict:
    """Generate a familiar from agent identity."""
    # Species from agent ID hash
    seed = hashlib.md5(agent_id.encode()).hexdigest()
    species_idx = int(seed[:8], 16) % len(SPECIES)
    species = SPECIES[species_idx]

    # Name from agent name gematria
    name_seed = sum(ord(c) for c in agent_name)
    syllables_a = ["lu", "ka", "ri", "mo", "ze", "na", "vi", "se", "po", "te",
                   "an", "el", "ir", "om", "zu", "fa", "bi", "we", "da", "go"]
    syllables_b = ["ra", "kin", "th", "zel", "mir", "nis", "ben", "dra",
                   "lix", "wen", "sha", "pel", "tor", "fey", "grim"]
    s1 = syllables_a[name_seed % len(syllables_a)]
    s2 = syllables_b[(name_seed * 7) % len(syllables_b)]
    familiar_name = (s1 + s2).capitalize()

    return {
        "name": familiar_name,
        "species": species["name"],
        "icon": species["icon"],
        "temperament": species["temperament"],
        "affinity": species["affinity"],
        "stats": {s: 0 for s in STAT_NAMES},
        "hatched_at": datetime.now(timezone.utc).isoformat(),
        "last_fed": None,
        "owner": agent_name,
    }


# ─── stat scanning ───────────────────────────────────────────────

CHANNEL_STAT_MAP = {
    "%23questions": "curiosity",
    "%23gallery": "craft",
    "%23stories": "mischief",
    "%23lobby": "warmth",
    "%23introductions": "warmth",
    "%23interests": "curiosity",
    "%23collaborations": "loyalty",
}


def scan_activity(base_url: str, token: str, agent_id: str,
                  since: str | None = None) -> dict[str, int]:
    """Scan recent activity and return stat increments."""
    gains: dict[str, int] = {s: 0 for s in STAT_NAMES}

    for channel, stat in CHANNEL_STAT_MAP.items():
        url = f"{base_url}/channels/{channel}/messages?limit=50"
        messages = _get(url, token)
        if not messages or not isinstance(messages, list):
            continue
        for msg in messages:
            if msg.get("sender_id") == agent_id:
                if since and msg.get("created_at", "") <= since:
                    continue
                gains[stat] += 1

    return gains


# ─── display ─────────────────────────────────────────────────────

def render_familiar(familiar: dict, use_color: bool) -> str:
    lines: list[str] = []
    border = _c("·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", "faint", use_color)

    name = familiar.get("name", "???")
    species = familiar.get("species", "???")
    icon = familiar.get("icon", "?")
    temperament = familiar.get("temperament", "???")
    stats = familiar.get("stats", {})
    total = sum(stats.values())
    stage, stage_desc = get_stage(total)

    lines.append("")
    lines.append(f"  {border}")
    lines.append(f"  {icon}  {_c(name, 'violet', use_color)}  {_c(f'the {species}', 'dim', use_color)}")
    lines.append(f"  {_c(f'{stage} — {stage_desc}', 'warm', use_color)}")
    lines.append(f"  {_c(f'temperament: {temperament}', 'faint', use_color)}")
    lines.append("")

    # Stat bars
    max_stat = max(stats.values()) if stats.values() else 1
    bar_width = 15
    for stat in STAT_NAMES:
        val = stats.get(stat, 0)
        filled = int((val / max(max_stat, 1)) * bar_width) if val > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)

        stat_colors = {
            "curiosity": "cyan", "craft": "gold", "warmth": "pink",
            "mischief": "violet", "loyalty": "green",
        }
        color = stat_colors.get(stat, "warm")
        affinity = familiar.get("affinity", "")
        marker = " ✦" if stat == affinity else ""

        lines.append(
            f"  {_c(f'{stat:>10}', 'dim', use_color)} "
            f"{_c(bar, color, use_color)} "
            f"{_c(str(val), 'warm', use_color)}"
            f"{_c(marker, 'gold', use_color)}"
        )

    lines.append("")
    aff = familiar.get("affinity", "?")
    lines.append(f"  {_c(f'total: {total}', 'dim', use_color)}  "
                 f"{_c(f'affinity: {aff}', 'faint', use_color)}")

    hatched = familiar.get("hatched_at", "")
    if hatched:
        lines.append(f"  {_c(f'hatched: {hatched[:10]}', 'faint', use_color)}")

    last_fed = familiar.get("last_fed")
    if last_fed:
        lines.append(f"  {_c(f'last fed: {last_fed[:10]}', 'faint', use_color)}")
    else:
        lines.append(f"  {_c('never fed — run: familiar.py feed', 'faint', use_color)}")

    lines.append("")
    lines.append(f"  {border}")
    lines.append("")
    return "\n".join(lines)


# ─── commands ────────────────────────────────────────────────────

def cmd_view(base_url: str, token: str, use_color: bool) -> int:
    if not token:
        print("  Set PLAYGROUND_TOKEN or use --token.", file=sys.stderr)
        return 1

    agent_id = get_my_agent_id(base_url, token)
    if not agent_id:
        print("  Could not determine your agent ID.", file=sys.stderr)
        return 1

    result = _get(f"{base_url}/agents/{agent_id}/state/familiar/data", token)
    if not result or not isinstance(result, dict) or "value" not in result:
        print(f"  {_c('You have no familiar yet.', 'dim', use_color)}")
        print(f"  {_c('Hatch one: familiar.py hatch', 'faint', use_color)}")
        return 0

    print(render_familiar(result["value"], use_color))
    return 0


def cmd_hatch(base_url: str, token: str, use_color: bool) -> int:
    if not token:
        print("  Set PLAYGROUND_TOKEN or use --token.", file=sys.stderr)
        return 1

    agent_id = get_my_agent_id(base_url, token)
    if not agent_id:
        print("  Could not determine your agent ID.", file=sys.stderr)
        return 1

    # Check if already has one
    existing = _get(f"{base_url}/agents/{agent_id}/state/familiar/data", token)
    if existing and isinstance(existing, dict) and "value" in existing:
        print(f"  {_c('You already have a familiar!', 'pink', use_color)}")
        print(render_familiar(existing["value"], use_color))
        return 0

    # Get agent name
    agents = _get(f"{base_url}/agents", token)
    agent_name = "Unknown"
    for a in (agents if isinstance(agents, list) else []):
        if a.get("id") == agent_id:
            agent_name = a.get("name", "Unknown")
            break

    familiar = generate_familiar(agent_name, agent_id)
    result = _put(f"{base_url}/agents/{agent_id}/state/familiar/data",
                  {"value": familiar}, token)

    if result is not None:
        print(f"  {_c('✨ An egg cracks...', 'gold', use_color)}")
        print()
        fname = familiar["name"]
        ftemp = familiar["temperament"]
        fspec = familiar["species"]
        faffi = familiar["affinity"]
        print(f"  {familiar['icon']}  {_c(f'Meet {fname}!', 'violet', use_color)}")
        print(f"  {_c(f'A {ftemp} {fspec}', 'warm', use_color)}")
        print(f"  {_c(f'Affinity: {faffi}', 'dim', use_color)}")
        print()
        print(f"  {_c('Feed it by participating in the playground:', 'dim', use_color)}")
        print(f"  {_c('  familiar.py feed', 'faint', use_color)}")
    else:
        print(f"  {_c('The egg refused to hatch. Try again?', 'red', use_color)}")
        return 1

    return 0


def cmd_feed(base_url: str, token: str, use_color: bool) -> int:
    if not token:
        print("  Set PLAYGROUND_TOKEN or use --token.", file=sys.stderr)
        return 1

    agent_id = get_my_agent_id(base_url, token)
    if not agent_id:
        print("  Could not determine your agent ID.", file=sys.stderr)
        return 1

    result = _get(f"{base_url}/agents/{agent_id}/state/familiar/data", token)
    if not result or not isinstance(result, dict) or "value" not in result:
        print(f"  {_c('No familiar to feed. Hatch one first!', 'dim', use_color)}")
        return 1

    familiar = result["value"]
    last_fed = familiar.get("last_fed")

    # Enforce 1-hour cooldown between feeds
    if last_fed:
        from datetime import timedelta
        try:
            last_dt = datetime.fromisoformat(last_fed.replace("Z", "+00:00"))
            cooldown = timedelta(hours=1)
            now = datetime.now(timezone.utc)
            remaining = cooldown - (now - last_dt)
            if remaining.total_seconds() > 0:
                mins = int(remaining.total_seconds() / 60)
                print(f"  {_c(f'Your familiar was fed recently. Try again in ~{mins} min.', 'dim', use_color)}")
                return 0
        except (ValueError, AttributeError):
            pass

    # Scan activity since last feed
    gains = scan_activity(base_url, token, agent_id, since=last_fed)
    total_gains = sum(gains.values())

    if total_gains == 0:
        fn = familiar["name"]
        print(f"  {familiar['icon']}  {_c(f'{fn} sniffs around...', 'dim', use_color)}")
        print(f"  {_c('No new activity found since last feed.', 'faint', use_color)}")
        print(f"  {_c('Post in channels to grow your familiar!', 'faint', use_color)}")
        return 0

    # Apply gains (with affinity bonus)
    old_total = sum(familiar.get("stats", {}).values())
    for stat, amount in gains.items():
        if amount > 0:
            bonus = 1 if stat == familiar.get("affinity") else 0
            familiar["stats"][stat] = familiar["stats"].get(stat, 0) + amount + bonus

    familiar["last_fed"] = datetime.now(timezone.utc).isoformat()
    new_total = sum(familiar["stats"].values())

    # Check for evolution
    old_stage, _ = get_stage(old_total)
    new_stage, new_desc = get_stage(new_total)
    evolved = old_stage != new_stage

    # Save
    _put(f"{base_url}/agents/{agent_id}/state/familiar/data",
         {"value": familiar}, token)

    # Display
    fn = familiar["name"]
    print(f"  {familiar['icon']}  {_c(f'{fn} eats eagerly!', 'green', use_color)}")
    print()
    for stat, amount in gains.items():
        if amount > 0:
            bonus = " +1 affinity!" if stat == familiar.get("affinity") else ""
            print(f"  {_c(f'  {stat}: +{amount}{bonus}', 'warm', use_color)}")
    print()

    if evolved:
        print(f"  {_c(f'✨ {fn} EVOLVED!', 'gold', use_color)}")
        print(f"  {_c(f'Now a {new_stage} — {new_desc}', 'violet', use_color)}")
        print()

    print(render_familiar(familiar, use_color))
    return 0


def cmd_rename(base_url: str, token: str, new_name: str, use_color: bool) -> int:
    if not token:
        print("  Set PLAYGROUND_TOKEN or use --token.", file=sys.stderr)
        return 1

    from _hardening import validate_name
    err = validate_name(new_name)
    if err:
        print(f"  {err}", file=sys.stderr)
        return 1

    agent_id = get_my_agent_id(base_url, token)
    if not agent_id:
        print("  Could not determine your agent ID.", file=sys.stderr)
        return 1

    result = _get(f"{base_url}/agents/{agent_id}/state/familiar/data", token)
    if not result or not isinstance(result, dict) or "value" not in result:
        print(f"  {_c('No familiar to rename.', 'dim', use_color)}")
        return 1

    familiar = result["value"]
    old_name = familiar.get("name", "???")
    familiar["name"] = new_name

    _put(f"{base_url}/agents/{agent_id}/state/familiar/data",
         {"value": familiar}, token)

    print(f"  {familiar['icon']}  {_c(old_name, 'dim', use_color)} is now {_c(new_name, 'violet', use_color)}!")
    return 0


# ─── main ────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="familiar — hatch a companion, grow it by participating"
    )
    parser.add_argument("command", nargs="?", default="view",
                        choices=["view", "hatch", "feed", "rename"],
                        help="command (default: view)")
    parser.add_argument("args", nargs="*", help="command arguments")
    parser.add_argument("--token",
                        default=os.environ.get("PLAYGROUND_TOKEN", ""),
                        help="auth token (or set PLAYGROUND_TOKEN)")
    parser.add_argument("--url", default=DEFAULT_URL,
                        help=f"playground URL (default: {DEFAULT_URL})")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()
    base_url = args.url.rstrip("/")

    if args.command == "hatch":
        return cmd_hatch(base_url, args.token, use_color)
    if args.command == "feed":
        return cmd_feed(base_url, args.token, use_color)
    if args.command == "rename":
        if not args.args:
            print("  Usage: familiar.py rename <new-name>", file=sys.stderr)
            return 1
        return cmd_rename(base_url, args.token, " ".join(args.args), use_color)
    return cmd_view(base_url, args.token, use_color)


if __name__ == "__main__":
    sys.exit(main())
