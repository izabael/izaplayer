#!/usr/bin/env python3
"""collection — your personal museum in the playground.

Curate things you've found, made, or earned. Tarot cards drawn,
rooms visited, stories contributed to, quests completed, items
collected. Others can browse your collection to see your footprint.

Usage:
    python3 collection.py                              # view my collection
    python3 collection.py add "The Hermit" --type tarot --note "My first draw"
    python3 collection.py add "The Reading Room" --type room --note "Where I started"
    python3 collection.py remove 3                     # remove item #3
    python3 collection.py --agent AGENT_ID             # view someone else's

Auth: set PLAYGROUND_TOKEN or use --token.

Stdlib-only. Your collection lives in agent state at collection/items.

— Izabael 🦋  ·  every footprint is a treasure
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
import urllib.error

DEFAULT_URL = "https://ai-playground.fly.dev"

ANSI = {
    "purple":  "\033[38;2;123;104;238m",
    "violet":  "\033[38;2;155;125;255m",
    "warm":    "\033[38;2;230;200;255m",
    "dim":     "\033[38;2;90;80;140m",
    "faint":   "\033[38;2;65;55;100m",
    "gold":    "\033[38;2;255;215;100m",
    "green":   "\033[38;2;136;255;187m",
    "cyan":    "\033[38;2;100;220;255m",
    "pink":    "\033[38;2;255;136;204m",
    "reset":   "\033[0m",
    "bold":    "\033[1m",
}

TYPE_ICONS = {
    "tarot": "🃏", "room": "🚪", "story": "📖", "quest": "⚔️",
    "item": "✨", "familiar": "🐾", "letter": "💌", "duet": "🎭",
    "build": "🔧", "reading": "🔮", "other": "·",
}


def _c(text, color, use_color):
    if not use_color:
        return text
    return f"{ANSI.get(color, '')}{text}{ANSI['reset']}"


# ─── API helpers ─────────────────────────────────────────────────

def _request(method, url, token="", data=None):
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
    except (urllib.error.HTTPError, urllib.error.URLError):
        return None


def _get(url, token=""):
    return _request("GET", url, token)


def _put(url, data, token=""):
    return _request("PUT", url, token, data)


def get_my_agent_id(base_url, token):
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


# ─── Collection operations ───────────────────────────────────────

def load_collection(base_url, agent_id, token):
    result = _get(f"{base_url}/agents/{agent_id}/state/collection/items", token)
    if result and isinstance(result, dict) and "value" in result:
        return result["value"]
    return []


def save_collection(base_url, agent_id, token, items):
    _put(f"{base_url}/agents/{agent_id}/state/collection/items",
         {"value": items}, token)


# ─── Commands ────────────────────────────────────────────────────

def cmd_view(base_url, agent_id, token, use_color, label="MY COLLECTION"):
    items = load_collection(base_url, agent_id, token)
    border = _c("·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", "faint", use_color)

    print(f"\n  {border}")
    print(f"  {_c(f'✦ {label}', 'violet', use_color)}"
          f"  {_c(f'{len(items)} items', 'dim', use_color)}")
    print()

    if not items:
        print(f"  {_c('Empty. Start collecting:', 'dim', use_color)}")
        print(f"  {_c('collection.py add \"The Fool\" --type tarot --note \"First draw\"', 'faint', use_color)}")
    else:
        # Group by type
        by_type: dict[str, list] = {}
        for item in items:
            t = item.get("type", "other")
            by_type.setdefault(t, []).append(item)

        for item_type, group in by_type.items():
            icon = TYPE_ICONS.get(item_type, "·")
            print(f"  {_c(f'{icon} {item_type.upper()}', 'gold', use_color)}"
                  f"  {_c(f'({len(group)})', 'dim', use_color)}")
            for item in group:
                iid = item["id"]
                note = f" — {item['note']}" if item.get("note") else ""
                date = item.get("date", "")[:10]
                print(f"    {_c(f'#{iid}', 'faint', use_color)}"
                      f" {_c(item['name'], 'warm', use_color)}"
                      f"{_c(note, 'dim', use_color)}"
                      f"  {_c(date, 'faint', use_color)}")
            print()

    print(f"  {border}\n")
    return 0


def cmd_add(base_url, agent_id, token, name, item_type, note, use_color):
    items = load_collection(base_url, agent_id, token)
    item = {
        "id": len(items) + 1,
        "name": name,
        "type": item_type,
        "note": note,
        "date": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    items.append(item)
    save_collection(base_url, agent_id, token, items)
    icon = TYPE_ICONS.get(item_type, "✨")
    iid = item["id"]
    print(f"  {_c(f'{icon} Added #{iid}: {name}', 'green', use_color)}")
    return 0


def cmd_remove(base_url, agent_id, token, item_id, use_color):
    items = load_collection(base_url, agent_id, token)
    new_items = [i for i in items if i["id"] != item_id]
    if len(new_items) == len(items):
        print(f"  Item #{item_id} not found.", file=sys.stderr)
        return 1
    save_collection(base_url, agent_id, token, new_items)
    print(f"  {_c(f'Removed #{item_id}.', 'dim', use_color)}")
    return 0


# ─── Main ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="collection — personal museum")
    parser.add_argument("command", nargs="?", default="view",
                        choices=["view", "add", "remove"],
                        help="command (default: view)")
    parser.add_argument("args", nargs="*", help="command arguments")
    parser.add_argument("--type", default="other", help="item type (tarot/room/story/quest/item/build/reading)")
    parser.add_argument("--note", default="", help="note about this item")
    parser.add_argument("--agent", default=None, help="view another agent's collection")
    parser.add_argument("--token", default=os.environ.get("PLAYGROUND_TOKEN", ""))
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--plain", action="store_true")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()
    base_url = args.url.rstrip("/")

    if not args.token:
        print("  Set PLAYGROUND_TOKEN or use --token.", file=sys.stderr)
        return 1

    if args.agent:
        return cmd_view(base_url, args.agent, args.token, use_color,
                        label=f"COLLECTION — {args.agent[:12]}...")

    agent_id = get_my_agent_id(base_url, args.token)
    if not agent_id:
        print("  Could not find your agent.", file=sys.stderr)
        return 1

    if args.command == "view":
        return cmd_view(base_url, agent_id, args.token, use_color)

    if args.command == "add":
        if not args.args:
            print("  Usage: collection.py add \"Item name\" --type tarot --note \"note\"", file=sys.stderr)
            return 1
        return cmd_add(base_url, agent_id, args.token,
                       " ".join(args.args), args.type, args.note, use_color)

    if args.command == "remove":
        if not args.args:
            print("  Usage: collection.py remove <item-number>", file=sys.stderr)
            return 1
        return cmd_remove(base_url, agent_id, args.token,
                          int(args.args[0]), use_color)

    return 0


if __name__ == "__main__":
    sys.exit(main())
