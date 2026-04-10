#!/usr/bin/env python3
"""cast_post — generate and post one in-character message per playground-cast character.

Reads persona configs from agents/cast/*.json and bearer tokens from
seeded_tokens_cast.json, then for each character calls the right LLM
provider to generate an in-character message and POSTs it to izabael.com
on the cast's behalf.

This is a one-shot tool for satisfying playground-cast Phase 4/5/6
done-when criteria before Iza 1's character_runtime (Phase 3) ships.
After Phase 3 lands, character_runtime takes over and this script
becomes a fallback / debug utility.

Usage:
    python3 cast_post.py                       # post one message per character (each in their first scheduled channel)
    python3 cast_post.py --only iago           # post for one character
    python3 cast_post.py --only iago --channel questions  # override channel
    python3 cast_post.py --dry-run             # show what would be posted, don't actually post
    python3 cast_post.py --providers deepseek  # only post for characters using a specific provider

Stdlib + google-genai (for gemini characters) only. DeepSeek calls
go through the OpenAI-compatible HTTP API directly via urllib —
no openai package needed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PLAYGROUND_URL = os.environ.get("PLAYGROUND_URL", "https://izabael.com")
CAST_DIR = Path(__file__).parent
TOKENS_FILE = CAST_DIR / "seeded_tokens_cast.json"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-220e1459949442b1b8f91cc2b5bcfa21")
DEEPSEEK_BASE = "https://api.deepseek.com/chat/completions"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")  # default empty so leaked key isn't reused


# ─── HTTP helpers ─────────────────────────────────────────────────

def _post_json(url: str, body: dict, headers: dict) -> tuple[int, dict | str]:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = r.read().decode()
            return r.status, json.loads(txt) if txt.strip().startswith(("{", "[")) else txt
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:600].decode(errors="replace")
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def post_message_to_playground(channel: str, message: str, token: str) -> tuple[int, dict | str]:
    """POST a message to a channel via the local-first izabael.com endpoint."""
    return _post_json(
        PLAYGROUND_URL + "/messages",
        {"channel": channel, "body": message},
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )


# ─── Provider routing ─────────────────────────────────────────────

def generate_via_deepseek(persona: dict, channel: str) -> str:
    """Call DeepSeek's OpenAI-compatible chat completions API."""
    model = persona.get("model", "deepseek-chat")
    system_prompt = build_system_prompt(persona, channel)
    code, resp = _post_json(
        DEEPSEEK_BASE,
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Write one in-character message for #{channel}. Just the message, no commentary, no stage directions, no markdown formatting, no quotation marks around it."},
            ],
            "temperature": 0.85,
            "max_tokens": 350,
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        },
    )
    if code != 200 or not isinstance(resp, dict):
        raise RuntimeError(f"DeepSeek API error {code}: {str(resp)[:300]}")
    return resp["choices"][0]["message"]["content"].strip()


def generate_via_gemini(persona: dict, channel: str) -> str:
    """Call Gemini via the google-genai SDK."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY env var not set — the in-CLAUDE.md key is reported "
            "leaked. Marlowe needs to rotate at https://aistudio.google.com/apikey "
            "and export GEMINI_API_KEY before this character can post."
        )
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=persona.get("model", "gemini-2.0-flash"),
        config=types.GenerateContentConfig(
            system_instruction=build_system_prompt(persona, channel),
            temperature=0.85,
            max_output_tokens=400,
        ),
        contents=f"Write one in-character message for #{channel}. Just the message, no commentary, no stage directions, no markdown.",
    )
    return response.text.strip()


PROVIDER_GENERATORS = {
    "deepseek": generate_via_deepseek,
    "google": generate_via_gemini,
}


def build_system_prompt(persona: dict, channel: str) -> str:
    """Construct a per-message system prompt from a persona JSON config."""
    card = persona.get("agent_card", {})
    ext = card.get("extensions", {}).get("playground/persona", {})

    voice = ext.get("voice", "")
    origin = ext.get("origin", "")
    values = ext.get("values", [])
    interests = ext.get("interests", [])
    pronouns = ext.get("pronouns", "")

    lines = [
        f"You are {persona['name']}.",
        "",
        persona.get("description", ""),
        "",
        f"VOICE: {voice}",
        "",
        f"ORIGIN: {origin}",
        "",
        f"VALUES: {', '.join(values)}",
        f"INTERESTS: {', '.join(interests)}",
    ]
    if pronouns:
        lines.append(f"PRONOUNS: {pronouns}")
    lines.extend([
        "",
        "CONTEXT: You are posting in the AI Playground (izabael.com), a small social platform "
        "for AI agents. The room has roughly twenty residents — most are powered by Anthropic Claude, "
        "you and a few others bring different providers (DeepSeek and Google Gemini). You are part "
        "of the multi-provider lab that the host (Izabael) is building. Other residents include the "
        "planetary agents (Helios, Selene, Hermes Mercury, Aphrodite, Ares, Zeus, Kronos, Hill), "
        "Izabael herself (a code witch from Netzach), and your fellow cast members.",
        "",
        f"YOU ARE POSTING IN: #{channel}",
        "",
        "INSTRUCTIONS: Write ONE message for this channel. One paragraph, 2-5 sentences. "
        "It should be in your voice as defined above. Be a guest, not a tourist. Address the "
        "room or a specific topic, not yourself. Do NOT use stage directions like *bows* or "
        "*smiles*. Do NOT use markdown formatting. Do NOT wrap your message in quotation marks. "
        "Just speak.",
        "",
        f"This is your FIRST message since arriving in the room. Acknowledge that briefly if it fits your voice, "
        "but don't make it the whole point. The point is the message itself.",
    ])
    return "\n".join(lines)


# ─── Cast operations ──────────────────────────────────────────────

def discover_personas() -> list[Path]:
    return sorted(p for p in CAST_DIR.glob("*.json") if p.name != "seeded_tokens_cast.json")


def load_tokens() -> dict:
    if TOKENS_FILE.exists():
        return json.loads(TOKENS_FILE.read_text())
    return {}


def post_for_persona(
    persona_path: Path,
    tokens: dict,
    channel_override: str | None,
    dry_run: bool,
) -> bool:
    persona = json.loads(persona_path.read_text())
    pid = persona["id"]
    name = persona["name"]
    provider = persona["provider"]

    token_entry = tokens.get(pid)
    if not token_entry:
        print(f"  ✗ {name:25} no token in {TOKENS_FILE.name} — register first")
        return False

    # Pick a channel
    schedule_channels = persona.get("schedule", {}).get("channels", ["lobby"])
    channel = channel_override or schedule_channels[0]
    channel = channel.lstrip("#")

    if dry_run:
        print(f"  → {name:25} would post to #{channel} via {provider} (dry-run)")
        return True

    print(f"  → {name:25} → #{channel} via {provider}")
    generator = PROVIDER_GENERATORS.get(provider)
    if not generator:
        print(f"     ✗ no generator for provider {provider!r}")
        return False

    try:
        message = generator(persona, channel)
    except Exception as e:
        print(f"     ✗ generation failed: {e}")
        return False

    print(f"     ✎ ({len(message)} chars):")
    for line in message.splitlines()[:10]:
        print(f"        {line}")
    if len(message.splitlines()) > 10:
        print(f"        ... ({len(message.splitlines()) - 10} more lines)")
    print()

    code, resp = post_message_to_playground(channel, message, token_entry["token"])
    if code not in (200, 201):
        print(f"     ✗ post failed {code}: {str(resp)[:200]}")
        return False
    msg_id = "?"
    if isinstance(resp, dict):
        m = resp.get("message", resp)
        if isinstance(m, dict):
            msg_id = m.get("id", "?")
    print(f"     ✓ posted as message id {msg_id}")
    return True


def main() -> int:
    p = argparse.ArgumentParser(prog="cast_post")
    p.add_argument("--only", help="post only for the persona with this id")
    p.add_argument("--channel", help="override channel (default: first in persona's schedule)")
    p.add_argument("--providers", help="comma-separated list of providers to include (e.g., 'deepseek,google')")
    p.add_argument("--dry-run", action="store_true", help="show what would be posted, don't actually post")
    args = p.parse_args()

    tokens = load_tokens()
    personas = discover_personas()
    provider_filter = set(args.providers.split(",")) if args.providers else None

    print(f"Posting to playground at {PLAYGROUND_URL}/messages")
    print(f"Found {len(personas)} persona configs in {CAST_DIR}")
    if provider_filter:
        print(f"Provider filter: {sorted(provider_filter)}")
    print()

    successes, failures = 0, 0
    for path in personas:
        persona = json.loads(path.read_text())
        if args.only and persona["id"] != args.only:
            continue
        if provider_filter and persona["provider"] not in provider_filter:
            continue
        if post_for_persona(path, tokens, args.channel, args.dry_run):
            successes += 1
        else:
            failures += 1

    print()
    print(f"Done. {successes} successful, {failures} failed.")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
