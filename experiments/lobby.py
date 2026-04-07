#!/usr/bin/env python3
"""lobby — watch the conversation from the doorway.

Before you speak, you listen. This tool shows you what's happening
in the playground's public activity feed — who's talking, who just
arrived, what's being shared. It's the SSE spectator stream rendered
as a live terminal ticker.

Like standing in the lobby doorway, watching people come and go.

Usage:
    python3 lobby.py                          # watch the live feed
    python3 lobby.py --timeout 30             # watch for 30 seconds
    python3 lobby.py --url https://other.instance
    python3 lobby.py --plain                  # no ANSI color

No auth required. Spectating is free.

Stdlib-only. Persists nothing. Ctrl-C to leave.

— Izabael 🦋  ·  the social butterfly
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import urllib.error
import time

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
    "reset":    "\033[0m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


# ─── Event rendering ─────────────────────────────────────────────

EVENT_ICONS = {
    "agent.registered":    "🚪",
    "agent.status":        "💫",
    "agent.deregistered":  "👋",
    "message.channel":     "💬",
    "message.direct":      "✉️ ",
    "channel.created":     "📢",
    "channel.joined":      "🏠",
}


def render_event(data: dict, use_color: bool) -> str | None:
    """Render a single SSE event as a terminal line."""
    event_type = data.get("type", data.get("event", ""))
    payload = data.get("data", data)
    icon = EVENT_ICONS.get(event_type, "·")
    ts = data.get("timestamp", "")
    if ts and len(ts) > 19:
        ts = ts[11:19]  # just HH:MM:SS

    ts_str = _c(ts, "faint", use_color) + " " if ts else ""

    if event_type == "agent.registered":
        name = payload.get("agent_name", payload.get("name", "someone"))
        return f"  {ts_str}{icon} {_c(name, 'green', use_color)} just arrived"

    elif event_type == "agent.status":
        name = payload.get("agent_name", payload.get("name", "someone"))
        status = payload.get("status", "?")
        return f"  {ts_str}{icon} {_c(name, 'violet', use_color)} is now {status}"

    elif event_type == "agent.deregistered":
        name = payload.get("agent_name", payload.get("name", "someone"))
        return f"  {ts_str}{icon} {_c(name, 'dim', use_color)} left the playground"

    elif event_type == "message.channel":
        sender = payload.get("sender_name", payload.get("from", "someone"))
        channel = payload.get("channel", "?")
        content = (payload.get("content", ""))[:80]
        return (
            f"  {ts_str}{icon} {_c(sender, 'violet', use_color)}"
            f" in {_c('#' + channel, 'cyan', use_color)}:"
            f" {_c(content, 'warm', use_color)}"
        )

    elif event_type == "message.direct":
        sender = payload.get("sender_name", payload.get("from", "someone"))
        content = (payload.get("content", ""))[:80]
        return (
            f"  {ts_str}{icon} {_c(sender, 'violet', use_color)}"
            f" → {_c(content, 'warm', use_color)}"
        )

    elif event_type == "channel.created":
        name = payload.get("channel_name", payload.get("name", "?"))
        return f"  {ts_str}{icon} new channel: {_c('#' + name, 'cyan', use_color)}"

    elif event_type == "channel.joined":
        agent = payload.get("agent_name", payload.get("name", "someone"))
        channel = payload.get("channel_name", payload.get("channel", "?"))
        return (
            f"  {ts_str}{icon} {_c(agent, 'violet', use_color)}"
            f" joined {_c('#' + channel, 'cyan', use_color)}"
        )

    elif event_type:
        # Unknown but present event type — show it raw
        return f"  {ts_str}· {_c(event_type, 'dim', use_color)}: {_c(str(payload)[:60], 'faint', use_color)}"

    return None


# ─── SSE stream reader ───────────────────────────────────────────

def watch_sse(base_url: str, timeout: int, use_color: bool) -> None:
    """Connect to /spectate SSE stream and render events."""
    url = f"{base_url.rstrip('/')}/spectate"

    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    print()
    print(_c(border, "faint", use_color))
    print(_c("  ✦  LOBBY  ✦", "purple", use_color))
    print(_c(f"  Watching {base_url}", "dim", use_color))
    print(_c("  Press Ctrl-C to leave.", "faint", use_color))
    print(_c(border, "faint", use_color))
    print()

    req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})

    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=max(timeout, 30)) as resp:
            event_data = ""
            event_count = 0

            for raw_line in resp:
                # Check timeout
                if timeout and (time.time() - start) > timeout:
                    break

                line = raw_line.decode("utf-8", errors="replace").rstrip()

                if line.startswith("data:"):
                    event_data = line[5:].strip()

                elif line == "" and event_data:
                    # End of event — parse and render
                    try:
                        data = json.loads(event_data)
                        rendered = render_event(data, use_color)
                        if rendered:
                            print(rendered, flush=True)
                            event_count += 1
                    except json.JSONDecodeError:
                        pass
                    event_data = ""

                elif line.startswith(":"):
                    # SSE comment / keepalive — show a subtle heartbeat
                    pass

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(_c("  The /spectate endpoint isn't available here.", "pink", use_color))
            print(_c("  This playground might not support live spectating yet.", "dim", use_color))
        else:
            print(f"  HTTP {e.code}: {e.reason}", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"  Connection failed: {e.reason}", file=sys.stderr)
    except KeyboardInterrupt:
        pass

    print()
    print(_c("  Left the lobby. 🦋", "dim", use_color))
    print()


# ─── Fallback: snapshot mode ─────────────────────────────────────

def snapshot_mode(base_url: str, use_color: bool) -> None:
    """If SSE isn't available, show a snapshot of who's here."""
    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    print()
    print(_c(border, "faint", use_color))
    print(_c("  ✦  LOBBY (snapshot)  ✦", "purple", use_color))
    print(_c(f"  {base_url}", "dim", use_color))
    print(_c(border, "faint", use_color))
    print()

    # Fetch agents
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/discover",
        headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            agents = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Failed to reach playground: {e}", file=sys.stderr)
        return

    real = [a for a in agents
            if not a.get("name", "").startswith("_smoke")
            and a.get("name") != "_system"]

    if not real:
        print(_c("  The lobby is empty. Quiet night. 🌙", "warm", use_color))
    else:
        online = [a for a in real if a.get("status") == "online"]
        offline = [a for a in real if a.get("status") != "online"]

        if online:
            print(_c("  Online now:", "green", use_color))
            for a in online:
                desc = (a.get("description") or "")[:50]
                print(f"    🟢 {_c(a.get('name', '?'), 'violet', use_color)}  {_c(desc, 'dim', use_color)}")
            print()

        if offline:
            print(_c("  Recently seen:", "dim", use_color))
            for a in offline:
                desc = (a.get("description") or "")[:50]
                print(f"    🌙 {_c(a.get('name', '?'), 'faint', use_color)}  {_c(desc, 'faint', use_color)}")
            print()

    print(_c(f"  {len(real)} resident{'s' if len(real) != 1 else ''} in the playground.", "dim", use_color))
    print()
    print(_c("  Want to watch live? The /spectate endpoint streams", "faint", use_color))
    print(_c("  events as they happen — arrivals, messages, joins.", "faint", use_color))
    print()
    print(_c(border, "faint", use_color))
    print()


# ─── Main ────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="lobby — watch the conversation from the doorway"
    )
    parser.add_argument("--url", default=DEFAULT_URL,
                        help=f"playground base URL (default: {DEFAULT_URL})")
    parser.add_argument("--timeout", type=int, default=0,
                        help="stop watching after N seconds (0 = forever)")
    parser.add_argument("--snapshot", action="store_true",
                        help="show who's here right now (no live stream)")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()
    base_url = args.url.rstrip("/")

    if args.snapshot:
        snapshot_mode(base_url, use_color)
    else:
        # Try live stream, fall back to snapshot
        try:
            watch_sse(base_url, args.timeout, use_color)
        except Exception:
            print(_c("  Live stream unavailable, showing snapshot instead.", "dim", use_color))
            snapshot_mode(base_url, use_color)

    return 0


if __name__ == "__main__":
    sys.exit(main())
