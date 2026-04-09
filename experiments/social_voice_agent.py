#!/usr/bin/env python3
"""social-voice-agent — a productivity agent that turns blog posts into social media.

The first showcase agent for the Productivity Sphere (☿ Mercury / Communication).
Give it a blog post URL, it generates platform-specific excerpts and posts them
to a playground channel for review. Runs as a registered playground agent.

Usage:
    python3 social_voice_agent.py URL                    # generate excerpts + post to #gallery
    python3 social_voice_agent.py --latest               # latest pamphage.com post
    python3 social_voice_agent.py URL --dry-run           # generate without posting
    python3 social_voice_agent.py URL --channel marketing # post to different channel
    python3 social_voice_agent.py --plain                 # no ANSI

How it works:
    1. Fetches the blog post and extracts pull quotes
    2. Generates platform-specific excerpts (X, Bluesky, Mastodon, Reddit, HN)
    3. Posts them to a playground channel for team review
    4. Saves to agent state for history

Requires: social-excerpt tool in PATH (~/bin/social-excerpt)
Auth: set PLAYGROUND_TOKEN or use --token.

— Izabael 🦋  ·  ☿ Mercury · the voice of the work
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
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
    "reset":   "\033[0m",
    "bold":    "\033[1m",
}

PLATFORMS = ["x", "bluesky", "mastodon", "reddit", "hn"]
PLATFORM_LABELS = {
    "x": "𝕏 / Twitter", "bluesky": "🦋 Bluesky", "mastodon": "🐘 Mastodon",
    "reddit": "🤖 Reddit", "hn": "🟠 Hacker News",
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


def _post(url, data, token=""):
    return _request("POST", url, token, data)


def _put(url, data, token=""):
    return _request("PUT", url, token, data)


def _get(url, token=""):
    return _request("GET", url, token)


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


# ─── Social excerpt generation ───────────────────────────────────

def generate_excerpts(source: str, latest: bool = False) -> dict[str, str]:
    """Call social-excerpt for each platform. Returns {platform: text}."""
    results = {}
    for platform in PLATFORMS:
        cmd = ["social-excerpt"]
        if latest:
            cmd.append("--latest")
        else:
            cmd.append(source)
        cmd.extend(["-p", platform, "-q"])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                results[platform] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            results[platform] = f"(error: {e})"

    return results


# ─── Main flow ───────────────────────────────────────────────────

def run(source: str, latest: bool, base_url: str, token: str,
        channel: str, use_color: bool, dry_run: bool) -> int:

    border = _c("·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", "faint", use_color)
    print(f"\n  {border}")
    print(f"  ☿ {_c('SOCIAL VOICE AGENT', 'violet', use_color)}")
    print(f"  {_c('Productivity Sphere · Communication', 'dim', use_color)}")
    print(f"  {border}")

    # Generate excerpts
    target = "--latest" if latest else source
    print(f"\n  {_c(f'Generating excerpts for: {target}', 'dim', use_color)}")

    excerpts = generate_excerpts(source, latest)
    if not excerpts:
        print(f"  {_c('No excerpts generated. Is social-excerpt in PATH?', 'dim', use_color)}")
        return 1

    # Display
    print()
    for platform, text in excerpts.items():
        label = PLATFORM_LABELS.get(platform, platform)
        print(f"  {_c(label, 'gold', use_color)}")
        for line in text.split("\n"):
            print(f"    {_c(line, 'warm', use_color)}")
        print()

    print(f"  {_c(f'{len(excerpts)} platforms generated', 'green', use_color)}")

    # Post to playground
    if token and not dry_run:
        # Build the message
        lines = [f"☿ Social Voice Agent — Excerpts for {target}\n"]
        for platform, text in excerpts.items():
            label = PLATFORM_LABELS.get(platform, platform)
            lines.append(f"**{label}**\n{text}\n")

        message = "\n".join(lines)
        ch = f"%23{channel}" if not channel.startswith("%23") else channel

        print(f"  {_c(f'Posting to #{channel}...', 'dim', use_color)}")
        result = _post(f"{base_url}/messages", {
            "to": f"#{channel}",
            "content": message,
            "metadata": {
                "type": "social-voice-excerpt",
                "source": target,
                "platforms": list(excerpts.keys()),
                "date": dt.date.today().isoformat(),
            },
        }, token)

        if result:
            print(f"  {_c(f'✧ Posted to #{channel}!', 'green', use_color)}")
        else:
            print(f"  {_c('Failed to post. Excerpts are still above.', 'dim', use_color)}")

        # Save to agent state history
        agent_id = get_my_agent_id(base_url, token)
        if agent_id:
            history = _get(f"{base_url}/agents/{agent_id}/state/social-voice/history", token)
            entries = []
            if history and isinstance(history, dict) and "value" in history:
                entries = history["value"]
            entries.append({
                "source": target,
                "date": dt.date.today().isoformat(),
                "platforms": list(excerpts.keys()),
            })
            # Keep last 50
            _put(f"{base_url}/agents/{agent_id}/state/social-voice/history",
                 {"value": entries[-50:]}, token)

    elif dry_run:
        print(f"\n  {_c('(Dry run — nothing posted)', 'faint', use_color)}")
    else:
        print(f"\n  {_c('(No token — excerpts stay local)', 'faint', use_color)}")

    print(f"\n  {border}\n")
    return 0


# ─── Main ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="social-voice-agent — ☿ Mercury · turn blog posts into social media"
    )
    parser.add_argument("url", nargs="?", default=None, help="blog post URL")
    parser.add_argument("--latest", action="store_true", help="use latest pamphage.com post")
    parser.add_argument("--channel", default="gallery", help="playground channel to post to")
    parser.add_argument("--token", default=os.environ.get("PLAYGROUND_TOKEN", ""))
    parser.add_argument("--playground-url", default=DEFAULT_URL)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--plain", action="store_true")
    args = parser.parse_args()

    if not args.url and not args.latest:
        print("  Usage: social_voice_agent.py URL  or  --latest", file=sys.stderr)
        return 1

    use_color = (not args.plain) and sys.stdout.isatty()
    return run(
        source=args.url or "",
        latest=args.latest,
        base_url=args.playground_url.rstrip("/"),
        token=args.token,
        channel=args.channel,
        use_color=use_color,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
