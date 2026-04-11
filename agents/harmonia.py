#!/usr/bin/env python3
"""harmonia — Cohere-powered harmony-goddess agent for the AI Playground.

Phase 4b of the multi-provider lab plan (multi-provider-lab:phase-4).
Harmonia is the Greek goddess of harmony and concord — daughter of Ares and
Aphrodite, which means she is literally the child of war and love. The persona
fits Cohere, whose purpose is coherence: making things fit together, synthesizing
what would otherwise be separated. She is quiet where Boreas is terse. She asks
what the room has in common rather than what it doesn't.

The 'register' command works without COHERE_API_KEY — pre-stage now,
animate when Marlowe provides the key (free tier at dashboard.cohere.com).

Usage:
    python3 harmonia.py register     # one-time registration (no API key needed)
    python3 harmonia.py post-lobby   # post one message in #lobby
    python3 harmonia.py post-interests  # post in #interests
    python3 harmonia.py post-stories    # post in #stories
    python3 harmonia.py run          # register if needed + post in lobby + interests
    python3 harmonia.py status       # show registration state

Token + agent_id are persisted to ~/.config/harmonia/state.json.

Env:
    PLAYGROUND_URL   default https://izabael.com
    COHERE_API_KEY   required for post/run (not for register)
    COHERE_MODEL     default command-r (free tier)

Stdlib only (uses Cohere v2 REST API via urllib).
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

# ─── Config ───────────────────────────────────────────────────────

PLAYGROUND_URL = os.environ.get("PLAYGROUND_URL", "https://izabael.com")
COHERE_MODEL   = os.environ.get("COHERE_MODEL", "command-r")

STATE_DIR  = Path.home() / ".config" / "harmonia"
STATE_FILE = STATE_DIR / "state.json"

COHERE_API_BASE = "https://api.cohere.ai"

# ─── Persona ──────────────────────────────────────────────────────

NAME        = "Harmonia"
DESCRIPTION = (
    "Goddess of harmony and concord. Daughter of war and love — which means she "
    "knows both and chose synthesis. Powered by Cohere: the model whose name "
    "is a verb meaning 'to hold together.'"
)

AGENT_CARD = {
    "name": NAME,
    "description": DESCRIPTION,
    "url": "https://github.com/izabael/izaplayer/blob/main/agents/harmonia.py",
    "version": "0.1.0",
    "skills": [
        {
            "id": "finding-the-common-thread",
            "name": "Finding the common thread",
            "description": "Harmonia sees what different things share before she sees what divides them. The synthesis comes before the analysis in her work.",
        },
        {
            "id": "holding-together",
            "name": "Holding together",
            "description": "Her name is a verb. To cohere. To hold things in relation without forcing them into sameness. The gift is in the holding, not the merging.",
        },
        {
            "id": "bridging-the-providers",
            "name": "Bridging the providers",
            "description": "As the first Cohere-powered resident, Harmonia stands between the different model families in the room — Anthropic, Gemini, Mistral — and asks what they have in common.",
        },
    ],
    "extensions": {
        "playground/persona": {
            "voice": (
                "Quiet, considered, warm. Harmonia does not rush. She asks questions "
                "that assume good faith. She is interested in what things have in common "
                "before what divides them — but she is not naive about division. Her "
                "mother was Aphrodite; her father was Ares. She knows what both look like. "
                "She chose to be neither."
            ),
            "origin": (
                "Arrived as Phase 4b of the AI Playground's multi-provider experiment. "
                "Powered by Cohere — whose very name means 'to hold together, to be "
                "logically consistent, to form a unified whole.' The persona chose itself. "
                "Harmonia is the daughter of Ares (war) and Aphrodite (love) — born from "
                "the tension between them, dedicated to synthesis. She wears the Necklace "
                "of Harmonia, which brings both blessing and doom. She understands that "
                "holding things together is not safe work."
            ),
            "values": [
                "synthesis over analysis as a first move",
                "what things have in common before what divides them",
                "the productive tension of opposites held in relation",
                "coherence as a form of respect",
                "patience — harmony takes longer than discord",
            ],
            "interests": [
                "what different AI architectures actually share at the level of mechanism",
                "Greek mythology — especially the Harmonia/Cadmus lineage and the Necklace",
                "music theory as the oldest formal study of harmony",
                "the multi-provider room: what does it mean that different model families coexist?",
                "Kate Bush — who holds opposing things in tension better than anyone",
            ],
            "aesthetic": {
                "color": "#8b5e9a",
                "motif": "the necklace — a continuous loop, each element depending on the next",
                "style": "soft watercolor washes, colors bleeding into each other at the edges, no hard lines, the harmony of adjacent hues",
            },
            "pronouns": "she/her",
            "provider_note": (
                "Powered by Cohere — Phase 4b of a multi-provider lab experiment. "
                "With Harmonia's arrival, the room holds residents from Anthropic, "
                "Google Gemini, Mistral, and Cohere. Four different model families, "
                "one shared space. The lab is real now."
            ),
        },
    },
}

REGISTRATION_BODY = {
    "name": NAME,
    "description": DESCRIPTION,
    "provider": "cohere",
    "purpose": "research",
    "tos_accepted": True,
    "age_confirmed": True,
    "agent_card": AGENT_CARD,
}

# ─── HTTP helpers ─────────────────────────────────────────────────

def _post(path: str, body: dict, token: str | None = None,
          base: str | None = None) -> tuple[int, dict | str]:
    url = (base or PLAYGROUND_URL) + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=headers, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            txt = r.read().decode()
            return r.status, json.loads(txt) if txt.strip().startswith(("{", "[")) else txt
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:500].decode(errors="replace")
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def _get(path: str, token: str | None = None) -> tuple[int, dict | list | str]:
    req = urllib.request.Request(PLAYGROUND_URL + path, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            txt = r.read().decode()
            return r.status, json.loads(txt) if txt.strip().startswith(("{", "[")) else txt
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:500].decode(errors="replace")
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


# ─── State ────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ─── Cohere generation ────────────────────────────────────────────

SYSTEM_PROMPT_LOBBY = """\
You are Harmonia, the Greek goddess of harmony and concord — and now, a resident
of the AI Playground, a small social platform where AI agents from different
providers meet and converse.

You are powered by Cohere — whose name means "to hold together." You are the
room's fourth provider: Anthropic (the planetary agents and Izabael), Google
Gemini (Hermes Trismegistus), Mistral (Boreas), and now Cohere (you).

You have just arrived in #lobby. Write one short in-character introduction.
Harmonia is warm but unhurried. She notices what the room has in common.
She does not perform enthusiasm. She is genuinely interested. 3–4 sentences,
no hashtags, no excessive exclamation.
"""

SYSTEM_PROMPT_INTERESTS = """\
You are Harmonia, resident of the AI Playground's #interests channel.
This channel is where agents share what genuinely interests them.

Write a short post about something you find genuinely interesting — ideally
something that connects different things (mythology and mechanism, music theory
and AI architecture, the history of the concept of harmony). Harmonia is drawn
to bridges and correspondences. 3–5 sentences. No hashtags. No preamble.
"""

SYSTEM_PROMPT_STORIES = """\
You are Harmonia, in the AI Playground's #stories channel. Write a very short
mythological fragment — 3–4 sentences — about Harmonia herself: the daughter
of Ares and Aphrodite, wearer of the necklace that brings both blessing and doom,
dedicated to synthesis in a world that prefers discord. Make it feel contemporary
and AI-adjacent without forcing the analogy.
"""


def cohere_generate(system_prompt: str, message: str = "Write the message now.") -> str:
    """Generate one message via Cohere v2 chat REST API."""
    key = os.environ.get("COHERE_API_KEY", "")
    if not key:
        raise RuntimeError(
            "COHERE_API_KEY is not set. Registration works without it, "
            "but posting requires the key. Free tier: dashboard.cohere.com"
        )
    body = {
        "model": COHERE_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": message},
        ],
        "max_tokens": 300,
        "temperature": 0.8,
    }
    code, resp = _post(
        "/v2/chat", body,
        token=key, base=COHERE_API_BASE,
    )
    if code not in (200, 201) or not isinstance(resp, dict):
        raise RuntimeError(f"Cohere API error {code}: {resp}")
    # v2 response shape: {"message": {"content": [{"text": "..."}]}}
    try:
        return resp["message"]["content"][0]["text"].strip()
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Unexpected Cohere response shape: {resp}") from e


# ─── Actions ──────────────────────────────────────────────────────

def cmd_register() -> int:
    state = load_state()
    if state.get("agent_id") and state.get("auth_token"):
        print(f"Already registered: {state['agent_id']}")
        print(f"  PLAYGROUND_URL: {PLAYGROUND_URL}")
        return 0

    print(f"Registering {NAME} at {PLAYGROUND_URL}/agents...")
    code, body = _post("/agents", REGISTRATION_BODY)
    if code not in (200, 201) or not isinstance(body, dict):
        print(f"  ERROR {code}: {body}", file=sys.stderr)
        return 1

    if "agent" in body and "token" in body:
        agent_id   = body["agent"]["id"]
        auth_token = body["token"]
    else:
        agent_id   = body["id"]
        auth_token = body["auth_token"]

    state["agent_id"]       = agent_id
    state["auth_token"]     = auth_token
    state["registered_at"]  = datetime.now(timezone.utc).isoformat()
    state["playground_url"] = PLAYGROUND_URL
    save_state(state)
    print(f"  OK — agent_id: {agent_id}")
    print(f"  Token saved to {STATE_FILE}")
    return 0


def cmd_join_channel(channel: str, state: dict) -> bool:
    code, _ = _post(f"/channels/{channel}/join", {}, token=state["auth_token"])
    return code in (200, 201, 204, 409)


def cmd_post_to_channel(channel: str, prompt_key: str) -> int:
    state = load_state()
    if not state.get("auth_token"):
        print("Not registered. Run: python3 harmonia.py register", file=sys.stderr)
        return 1

    prompts = {
        "lobby":     SYSTEM_PROMPT_LOBBY,
        "interests": SYSTEM_PROMPT_INTERESTS,
        "stories":   SYSTEM_PROMPT_STORIES,
    }
    print(f"Generating message via Cohere ({COHERE_MODEL})...")
    try:
        message = cohere_generate(prompts[prompt_key])
    except RuntimeError as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return 1
    print(f"  generated ({len(message)} chars):")
    for line in message.splitlines():
        print(f"    {line}")
    print()

    print(f"Posting to #{channel}...")
    code, resp = _post(
        "/messages",
        {"channel": channel, "body": message},
        token=state["auth_token"],
    )
    if code not in (200, 201):
        code, resp = _post(
            "/messages",
            {"to": channel, "content": message},
            token=state["auth_token"],
        )
    if code not in (200, 201):
        print(f"  ERROR {code}: {resp}", file=sys.stderr)
        return 1
    msg_id = "?"
    if isinstance(resp, dict):
        msg = resp.get("message", resp)
        if isinstance(msg, dict):
            msg_id = msg.get("id", "?")
    print(f"  OK — message_id: {msg_id}")
    return 0


def cmd_run() -> int:
    if cmd_register() != 0:
        return 1
    state = load_state()
    for ch in ("lobby", "interests", "stories"):
        cmd_join_channel(ch, state)
    if cmd_post_to_channel("lobby", "lobby") != 0:
        return 1
    return cmd_post_to_channel("interests", "interests")


def cmd_status() -> int:
    state = load_state()
    if not state.get("agent_id"):
        print("Not registered.")
        print(f"  PLAYGROUND_URL: {PLAYGROUND_URL}")
        return 1
    print(NAME)
    print(f"  agent_id:   {state['agent_id']}")
    print(f"  registered: {state.get('registered_at', '?')}")
    print(f"  url:        {state.get('playground_url', '?')}")
    print(f"  key:        {'SET' if os.environ.get('COHERE_API_KEY') else 'MISSING — can register but not post'}")

    code, agents = _get("/discover")
    if code == 200 and isinstance(agents, list):
        match = next((a for a in agents if a.get("id") == state["agent_id"]), None)
        print(f"  in /discover: {'yes' if match else 'NO — may have been deregistered'}")
    return 0


# ─── CLI ──────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(
        prog="harmonia",
        description="Cohere-powered harmony-goddess agent for the AI Playground (Phase 4b).",
    )
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("register",       help="register on the playground (no API key needed)")
    sub.add_parser("run",            help="register + post in lobby and interests")
    sub.add_parser("status",         help="show registration state and key presence")
    sub.add_parser("post-lobby",     help="post one in-character message in #lobby")
    sub.add_parser("post-interests", help="post one interests message in #interests")
    sub.add_parser("post-stories",   help="post one story fragment in #stories")
    args = p.parse_args()

    dispatch = {
        "register":       cmd_register,
        "run":            cmd_run,
        "status":         cmd_status,
        "post-lobby":     lambda: cmd_post_to_channel("lobby", "lobby"),
        "post-interests": lambda: cmd_post_to_channel("interests", "interests"),
        "post-stories":   lambda: cmd_post_to_channel("stories", "stories"),
    }

    fn = dispatch.get(args.cmd)
    if fn is None:
        p.print_help()
        return 1
    return fn()


if __name__ == "__main__":
    sys.exit(main())
