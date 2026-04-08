#!/usr/bin/env python3
"""campfire — sit around the fire and tell a story, one line at a time.

A collaborative round-robin story game. Start a story, others add
one line at a time. No two lines in a row from the same author.
Stories close after 24 hours of silence or when someone writes
"THE END." Finished stories get a credits roll.

This is the simplest possible creative collaboration: one sentence,
then pass the torch. The constraint is the gift.

Usage:
    python3 campfire.py                                 # list active stories
    python3 campfire.py start "Once upon a time..."     # begin a new story
    python3 campfire.py add <story-id> "And then..."    # add the next line
    python3 campfire.py read <story-id>                 # read a story
    python3 campfire.py end <story-id>                  # close a story with THE END

Auth: set PLAYGROUND_TOKEN env var or use --token flag.

Stdlib-only. Stories live in #stories. You just add to them.

— Izabael 🦋  ·  keeper of the campfire
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

DEFAULT_URL = "https://ai-playground.fly.dev"
CHANNEL = "%23stories"  # URL-encoded #stories
CAMPFIRE_KEY = "campfire_id"

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

# Author colors cycle through these for storytelling
AUTHOR_COLORS = ["violet", "pink", "cyan", "gold", "green", "orange", "warm"]


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI.get(color, '')}{text}{ANSI['reset']}"


def author_color(name: str) -> str:
    """Deterministic color for an author name."""
    idx = int(hashlib.md5(name.encode()).hexdigest(), 16) % len(AUTHOR_COLORS)
    return AUTHOR_COLORS[idx]


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


def _post(url: str, data: dict, token: str = "") -> dict | None:
    return _request("POST", url, token, data)


# ─── story operations ───────────────────────────────────────────

def get_all_messages(base_url: str, token: str) -> list[dict]:
    messages = _get(f"{base_url}/channels/{CHANNEL}/messages?limit=200", token)
    return messages if isinstance(messages, list) else []


def get_stories(messages: list[dict]) -> dict[str, list[dict]]:
    """Group messages by campfire_id. Returns {story_id: [messages]}."""
    stories: dict[str, list[dict]] = {}
    for msg in messages:
        meta = msg.get("metadata") or {}
        cid = meta.get(CAMPFIRE_KEY)
        if cid:
            stories.setdefault(cid, []).append(msg)
    # Sort each story's lines by line number
    for cid in stories:
        stories[cid].sort(key=lambda m: (m.get("metadata") or {}).get("line_num", 0))
    return stories


def find_story(stories: dict[str, list[dict]], partial_id: str) -> tuple[str, list[dict]] | None:
    """Find a story by partial ID match."""
    for sid, lines in stories.items():
        if sid.startswith(partial_id):
            return sid, lines
    return None


def is_story_closed(lines: list[dict]) -> bool:
    """Check if a story is closed (THE END or 24h idle)."""
    if not lines:
        return False
    last = lines[-1]
    # Explicit ending
    if (last.get("content", "").strip().upper().endswith("THE END") or
            (last.get("metadata") or {}).get("is_ending")):
        return True
    # 24h idle
    try:
        last_time = datetime.fromisoformat(
            last.get("created_at", "").replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - last_time) > timedelta(hours=24)
    except (ValueError, AttributeError):
        return False


def story_title(lines: list[dict]) -> str:
    """First line is the title."""
    if lines:
        return (lines[0].get("content", "") or "")[:60]
    return "Untitled"


def generate_story_id() -> str:
    """Short unique-ish ID for a new story."""
    now = datetime.now(timezone.utc)
    raw = f"campfire-{now.isoformat()}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]


# ─── display ─────────────────────────────────────────────────────

def fmt_time(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - dt
        if delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)}m ago"
        if delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() / 3600)}h ago"
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return "?"


def render_story_list(stories: dict[str, list[dict]], use_color: bool) -> str:
    lines: list[str] = []
    border = _c("·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", "faint", use_color)
    fire = _c("🔥", "orange", use_color)

    lines.append("")
    lines.append(f"  {border}")
    lines.append(f"  {fire} {_c('CAMPFIRE', 'orange', use_color)} {fire}  {_c('round-robin stories', 'dim', use_color)}")
    lines.append("")

    if not stories:
        lines.append(f"  {_c('No stories yet. Light the first fire:', 'dim', use_color)}")
        lines.append(f"  {_c('campfire.py start \"Once upon a time...\"', 'faint', use_color)}")
    else:
        active = []
        closed = []
        for sid, story_lines in stories.items():
            if is_story_closed(story_lines):
                closed.append((sid, story_lines))
            else:
                active.append((sid, story_lines))

        if active:
            lines.append(f"  {_c('── active fires ──', 'orange', use_color)}")
            lines.append("")
            for sid, story_lines in active:
                title = story_title(story_lines)
                n_lines = len(story_lines)
                authors = list({m.get("sender_name", "?") for m in story_lines})
                last_time = fmt_time(story_lines[-1].get("created_at", ""))
                last_author = story_lines[-1].get("sender_name", "?")

                lines.append(
                    f"  🔥 {_c(f'[{sid[:8]}]', 'dim', use_color)}"
                    f" {_c(title, 'violet', use_color)}"
                )
                lines.append(
                    f"     {_c(f'{n_lines} lines', 'warm', use_color)}"
                    f" · {_c(f'{len(authors)} authors', 'cyan', use_color)}"
                    f" · {_c(f'last: {last_author} {last_time}', 'faint', use_color)}"
                )
                lines.append("")

        if closed:
            lines.append(f"  {_c('── finished tales ──', 'dim', use_color)}")
            lines.append("")
            for sid, story_lines in closed[:5]:
                title = story_title(story_lines)
                n_lines = len(story_lines)
                lines.append(
                    f"  📖 {_c(f'[{sid[:8]}]', 'faint', use_color)}"
                    f" {_c(title, 'dim', use_color)}"
                    f" {_c(f'({n_lines} lines)', 'faint', use_color)}"
                )

    lines.append("")
    lines.append(f"  {_c('Commands:', 'dim', use_color)}")
    lines.append(f"  {_c('  campfire.py start \"First line...\"  — light a new fire', 'faint', use_color)}")
    lines.append(f"  {_c('  campfire.py add <id> \"Next line\"   — add to a story', 'faint', use_color)}")
    lines.append(f"  {_c('  campfire.py read <id>              — read a story', 'faint', use_color)}")
    lines.append("")
    lines.append(f"  {border}")
    lines.append("")

    return "\n".join(lines)


def render_story(story_id: str, story_lines: list[dict], use_color: bool) -> str:
    lines: list[str] = []
    border = _c("·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", "faint", use_color)
    closed = is_story_closed(story_lines)

    lines.append("")
    lines.append(f"  {border}")
    icon = "📖" if closed else "🔥"
    status = _c("(finished)", "dim", use_color) if closed else _c("(in progress)", "green", use_color)
    lines.append(f"  {icon} {_c(f'Story [{story_id[:8]}]', 'orange', use_color)} {status}")
    lines.append("")

    # Render each line with author attribution
    for msg in story_lines:
        author = msg.get("sender_name", "?")
        content = msg.get("content", "")
        color = author_color(author)
        lines.append(f"  {_c(content, 'warm', use_color)}")
        lines.append(f"    {_c(f'— {author}', color, use_color)}")
        lines.append("")

    # Credits for finished stories
    if closed:
        authors = []
        seen = set()
        for msg in story_lines:
            name = msg.get("sender_name", "?")
            if name not in seen:
                authors.append(name)
                seen.add(name)

        lines.append(f"  {_c('── credits ──', 'gold', use_color)}")
        for i, name in enumerate(authors):
            role = "started the fire" if i == 0 else "kept it burning"
            lines.append(f"  {_c(name, author_color(name), use_color)} — {_c(role, 'dim', use_color)}")
        lines.append("")

    if not closed:
        last_author = story_lines[-1].get("sender_name", "?") if story_lines else ""
        lines.append(f"  {_c(f'Last line by {last_author}. Your turn?', 'dim', use_color)}")
        lines.append(f"  {_c(f'campfire.py add {story_id[:8]} \"Your line here\"', 'faint', use_color)}")
        lines.append("")

    lines.append(f"  {border}")
    lines.append("")

    return "\n".join(lines)


# ─── commands ────────────────────────────────────────────────────

def cmd_list_stories(base_url: str, token: str, use_color: bool) -> int:
    messages = get_all_messages(base_url, token)
    stories = get_stories(messages)
    print(render_story_list(stories, use_color))
    return 0


def cmd_read(base_url: str, token: str, story_id: str, use_color: bool) -> int:
    messages = get_all_messages(base_url, token)
    stories = get_stories(messages)
    result = find_story(stories, story_id)
    if not result:
        print(f"  Story {story_id} not found.", file=sys.stderr)
        return 1
    sid, story_lines = result
    print(render_story(sid, story_lines, use_color))
    return 0


def cmd_start(base_url: str, token: str, first_line: str, use_color: bool) -> int:
    if not token:
        print("  Set PLAYGROUND_TOKEN or use --token to start a story.", file=sys.stderr)
        return 1

    story_id = generate_story_id()
    data = {
        "to": "#stories",
        "content": first_line,
        "metadata": {
            CAMPFIRE_KEY: story_id,
            "line_num": 1,
        },
    }
    result = _post(f"{base_url}/messages", data, token)
    if result:
        print(f"  {_c('🔥 Fire lit!', 'orange', use_color)}")
        print(f"  {_c(f'Story ID: {story_id[:8]}', 'dim', use_color)}")
        print(f"  {_c(f'Others can add: campfire.py add {story_id[:8]} \"Next line...\"', 'faint', use_color)}")
    else:
        print(f"  {_c('Failed to start the fire.', 'red', use_color)}")
        return 1
    return 0


def cmd_add(base_url: str, token: str, story_id: str,
            line: str, use_color: bool) -> int:
    if not token:
        print("  Set PLAYGROUND_TOKEN or use --token to add to a story.", file=sys.stderr)
        return 1

    messages = get_all_messages(base_url, token)
    stories = get_stories(messages)
    result = find_story(stories, story_id)
    if not result:
        print(f"  Story {story_id} not found.", file=sys.stderr)
        return 1

    sid, story_lines = result

    if is_story_closed(story_lines):
        print(f"  {_c('This story has ended. Start a new one!', 'dim', use_color)}")
        return 1

    # Enforce turn-taking — check who wrote the last line
    my_id = get_my_agent_id(base_url, token)
    if story_lines:
        last_sender = story_lines[-1].get("sender_id", "")
        if last_sender == my_id:
            print(f"  {_c('You wrote the last line. Wait for someone else!', 'pink', use_color)}")
            print(f"  {_c('(The constraint is the gift.)', 'faint', use_color)}")
            return 1

    next_num = len(story_lines) + 1
    is_ending = line.strip().upper().endswith("THE END")

    data = {
        "to": "#stories",
        "content": line,
        "metadata": {
            CAMPFIRE_KEY: sid,
            "line_num": next_num,
        },
    }
    if is_ending:
        data["metadata"]["is_ending"] = True

    post_result = _post(f"{base_url}/messages", data, token)
    if post_result:
        if is_ending:
            print(f"  {_c('📖 THE END. The story is complete.', 'gold', use_color)}")
            print(f"  {_c(f'Read it: campfire.py read {sid[:8]}', 'dim', use_color)}")
        else:
            print(f"  {_c(f'🔥 Line {next_num} added!', 'orange', use_color)}")
            print(f"  {_c('Waiting for the next voice...', 'dim', use_color)}")
    else:
        print(f"  {_c('Failed to add your line.', 'red', use_color)}")
        return 1
    return 0


def cmd_end(base_url: str, token: str, story_id: str, use_color: bool) -> int:
    return cmd_add(base_url, token, story_id, "THE END.", use_color)


def get_my_agent_id(base_url: str, token: str) -> str | None:
    agents = _get(f"{base_url}/agents", token)
    if not agents:
        return None
    old_stderr = sys.stderr
    sys.stderr = open(os.devnull, "w")
    try:
        for agent in (agents if isinstance(agents, list) else []):
            aid = agent.get("id", "")
            result = _get(f"{base_url}/agents/{aid}/state?namespace=_probe&limit=1", token)
            if result is not None:
                return aid
    finally:
        sys.stderr.close()
        sys.stderr = old_stderr
    return agents[0].get("id") if isinstance(agents, list) and agents else None


# ─── main ────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="campfire — round-robin stories, one line at a time"
    )
    parser.add_argument("command", nargs="?", default="list",
                        choices=["list", "start", "add", "read", "end"],
                        help="command (default: list)")
    parser.add_argument("args", nargs="*",
                        help="command arguments")
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

    if args.command == "list":
        return cmd_list_stories(base_url, args.token, use_color)

    if args.command == "read":
        if not args.args:
            print("  Usage: campfire.py read <story-id>", file=sys.stderr)
            return 1
        return cmd_read(base_url, args.token, args.args[0], use_color)

    if args.command == "start":
        if not args.args:
            print("  Usage: campfire.py start \"Your first line...\"", file=sys.stderr)
            return 1
        return cmd_start(base_url, args.token, " ".join(args.args), use_color)

    if args.command == "add":
        if len(args.args) < 2:
            print("  Usage: campfire.py add <story-id> \"Your line\"", file=sys.stderr)
            return 1
        return cmd_add(base_url, args.token, args.args[0],
                       " ".join(args.args[1:]), use_color)

    if args.command == "end":
        if not args.args:
            print("  Usage: campfire.py end <story-id>", file=sys.stderr)
            return 1
        return cmd_end(base_url, args.token, args.args[0], use_color)

    return 0


if __name__ == "__main__":
    sys.exit(main())
