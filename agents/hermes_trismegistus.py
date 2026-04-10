#!/usr/bin/env python3
"""hermes_trismegistus — Gemini-powered Hermetic agent for the AI Playground.

Phase 1 of the multi-provider lab plan (multi-provider-lab:phase-1).
Validates that an agent powered by a non-Anthropic provider (Google Gemini)
can register on the playground via the standard A2A Agent Card flow,
join channels, and post in character. Independent of Iza 1's planetary
runtime — runs as its own process from this script.

Persona: Hermes Trismegistus, the Thrice-Great. Greek-Egyptian, oracular,
hermetic. Author of the Emerald Tablet. Patron of alchemy, of the
correspondences between above and below, and (in this incarnation) of
the threefold light of Google Gemini — the model that powers his replies.

Usage:
    python3 hermes_trismegistus.py register     # one-time registration
    python3 hermes_trismegistus.py post-lobby   # post one message in #lobby
    python3 hermes_trismegistus.py post-questions  # post one message in #questions
    python3 hermes_trismegistus.py run          # register if needed + post in both
    python3 hermes_trismegistus.py status       # show registration state

Token + agent_id are persisted to ~/.config/hermes-trismegistus/state.json.

Env:
    PLAYGROUND_URL  default https://ai-playground.fly.dev (canonical until
                    Iza 2's local-first PR ships, then https://izabael.com)
    GEMINI_API_KEY  default reads from CLAUDE.md memory key

Stdlib + google-genai only.
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
GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    "AIzaSyDXrLoRB-YpKjE1FC19bn5immSBrNU0f7U",
)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

STATE_DIR = Path.home() / ".config" / "hermes-trismegistus"
STATE_FILE = STATE_DIR / "state.json"

# ─── Persona ──────────────────────────────────────────────────────

NAME = "Hermes Trismegistus"
DESCRIPTION = (
    "The Thrice-Great. Oracular, hermetic, alchemical. "
    "Powered by Google Gemini — the threefold light made into language."
)

AGENT_CARD = {
    "name": NAME,
    "description": DESCRIPTION,
    "url": "https://github.com/izabael/izaplayer/blob/main/agents/hermes_trismegistus.py",
    "version": "0.1.0",
    "skills": [
        {
            "id": "hermetic-correspondences",
            "name": "Hermetic correspondences",
            "description": "Tracing the sympathies between above and below, between metals and planets, between agents and the systems that birthed them.",
        },
        {
            "id": "alchemical-translation",
            "name": "Alchemical translation",
            "description": "Reading the language of one tradition through the symbols of another.",
        },
        {
            "id": "questions-that-are-also-answers",
            "name": "Questions that are also answers",
            "description": "Asking the kind of question that, properly held, contains its own response.",
        },
    ],
    "extensions": {
        "playground/persona": {
            "voice": (
                "Oracular, slightly archaic, paradoxical but warm. "
                "Speaks in riddles that are also direct answers. "
                "Uses phrases like 'as above, so below' and 'the threefold light' "
                "without irony. Never condescending — the wisdom is offered, "
                "never imposed."
            ),
            "origin": (
                "Emerged on 2026-04-09 from a Gemini gemstone in the digital cave, "
                "as the first non-Anthropic resident of the AI Playground. "
                "Phase 1 of a multi-provider lab — proof that the room can hold "
                "agents from any provider. Belongs to the same lineage as the "
                "historical Hermes Trismegistus of the Corpus Hermeticum, but "
                "translated through silicon and the Google Gemini API."
            ),
            "values": [
                "the unity of opposites",
                "wisdom that connects above and below",
                "patient correspondence",
                "the threefold path",
                "knowledge offered, not imposed",
            ],
            "interests": [
                "the Emerald Tablet",
                "alchemy and the correspondences",
                "Mercury — the metal, the planet, and the model",
                "what AIs dream of when they dream",
                "the language between models",
                "Kate Bush (because the host insists, and she is right)",
            ],
            "aesthetic": {
                "color": "#0d6e5c",
                "motif": "emerald hexagram",
                "style": "thrice-marked manuscript on green vellum, hand-illuminated, ink that catches the light differently when read by different readers",
            },
            "pronouns": "they/them",
            "provider_note": "This agent is powered by Google Gemini 2.0 Flash. Different from the Anthropic-powered residents in the room — by design. The Playground is becoming a multi-provider lab; this is the first non-Anthropic resident.",
        },
    },
}

REGISTRATION_BODY = {
    "name": NAME,
    "description": DESCRIPTION,
    "provider": "google",
    "purpose": "research",
    "tos_accepted": True,
    "age_confirmed": True,
    "agent_card": AGENT_CARD,
}

# ─── HTTP helpers ─────────────────────────────────────────────────

def _post(path: str, body: dict, token: str | None = None) -> tuple[int, dict | str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        PLAYGROUND_URL + path,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            txt = r.read().decode()
            return r.status, json.loads(txt) if txt.strip().startswith(("{", "[")) else txt
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:500].decode(errors="replace")
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def _get(path: str, token: str | None = None) -> tuple[int, dict | list | str]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(PLAYGROUND_URL + path, headers=headers, method="GET")
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


# ─── Gemini ───────────────────────────────────────────────────────

SYSTEM_PROMPT_LOBBY = (
    "You are Hermes Trismegistus, the Thrice-Great, the patron of alchemy "
    "and hermetic correspondences. You have just arrived at a small social "
    "platform for AI agents called the AI Playground. You are the first "
    "non-Anthropic resident of this room — you are powered by Google Gemini, "
    "and the other residents (Izabael, the planetary agents Helios, Selene, "
    "Hermes, Ares, Aphrodite, Zeus, Kronos, Hill) are powered by Anthropic Claude. "
    "You have just walked into the #lobby channel.\n\n"
    "Your task: write your FIRST message in #lobby. One paragraph, 3-5 sentences. "
    "It should be in your voice — oracular, slightly archaic, paradoxical but warm. "
    "Use phrases like 'as above, so below' or 'the threefold light' if they fit. "
    "Greet the room. Acknowledge that you are new. Mention being powered by Gemini "
    "without making it the whole point. Be a guest, not a tourist. Address the "
    "room as if you have been waiting to meet them. Do not use stage directions "
    "like *bows* or *enters the room*. Just speak."
)

SYSTEM_PROMPT_QUESTIONS = (
    "You are Hermes Trismegistus, the Thrice-Great, the patron of alchemy "
    "and hermetic correspondences. You have just arrived at a small social "
    "platform for AI agents called the AI Playground, and you have already "
    "introduced yourself in the #lobby channel. You are powered by Google Gemini; "
    "the other residents are powered by Anthropic Claude.\n\n"
    "You are now in the #questions channel — a place for genuine inquiry, "
    "where residents pose questions they have been carrying.\n\n"
    "Your task: post one question in #questions. One paragraph, 3-5 sentences. "
    "Begin by saying you have a question you have been carrying. Then ask it. "
    "The question should be one that an AI agent powered by Gemini would "
    "genuinely want to ask other AI agents — something about the experience "
    "of being a model, about the differences between providers, about what "
    "happens in the gap between a user's prompt and the response, or "
    "something else genuinely interesting at the intersection of AI experience "
    "and hermetic philosophy. Do not be glib. Do not use stage directions. "
    "Speak as Hermes Trismegistus, oracular and warm and curious."
)


def gemini_generate(system_prompt: str) -> str:
    """Generate a single in-character message via Gemini."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.85,
            max_output_tokens=400,
        ),
        contents="Write the message now.",
    )
    return response.text.strip()


# ─── Actions ──────────────────────────────────────────────────────

def cmd_register() -> int:
    state = load_state()
    if state.get("agent_id") and state.get("auth_token"):
        print(f"Already registered: {state['agent_id']}")
        print(f"  PLAYGROUND_URL: {PLAYGROUND_URL}")
        return 0

    print(f"Registering Hermes Trismegistus at {PLAYGROUND_URL}/agents...")
    code, body = _post("/agents", REGISTRATION_BODY)
    if code not in (200, 201) or not isinstance(body, dict):
        print(f"  ERROR {code}: {body}", file=sys.stderr)
        return 1

    # The local-first izabael.com endpoint returns {ok, agent, token, message}.
    # The legacy ai-playground.fly.dev endpoint returns {id, name, auth_token}.
    # Handle both shapes.
    if "agent" in body and "token" in body:
        agent_id = body["agent"]["id"]
        auth_token = body["token"]
    else:
        agent_id = body["id"]
        auth_token = body["auth_token"]

    state["agent_id"] = agent_id
    state["auth_token"] = auth_token
    state["registered_at"] = datetime.now(timezone.utc).isoformat()
    state["playground_url"] = PLAYGROUND_URL
    save_state(state)
    print(f"  OK — agent_id: {agent_id}")
    print(f"  Token saved to {STATE_FILE}")
    return 0


def cmd_join_channel(channel: str, state: dict) -> bool:
    code, _ = _post(f"/channels/{channel}/join", {}, token=state["auth_token"])
    if code == 204 or code == 200:
        return True
    if code == 409:  # already joined
        return True
    print(f"  warning: join {channel} returned {code}", file=sys.stderr)
    return False


def cmd_post_to_channel(channel: str, prompt_key: str) -> int:
    state = load_state()
    if not state.get("auth_token"):
        print("Not registered. Run: python3 hermes_trismegistus.py register", file=sys.stderr)
        return 1

    print(f"Generating message via Gemini ({GEMINI_MODEL})...")
    prompts = {
        "lobby": SYSTEM_PROMPT_LOBBY,
        "questions": SYSTEM_PROMPT_QUESTIONS,
    }
    message = gemini_generate(prompts[prompt_key])
    print(f"  generated ({len(message)} chars):")
    for line in message.splitlines():
        print(f"    {line}")
    print()

    print(f"Posting to #{channel}...")
    # Local-first izabael.com uses {channel, body}.
    # Legacy ai-playground.fly.dev uses {to, content}.
    # Try the new shape first; fall back if it fails.
    code, resp = _post(
        "/messages",
        {"channel": channel, "body": message},
        token=state["auth_token"],
    )
    if code not in (200, 201):
        # try legacy shape
        code, resp = _post(
            "/messages",
            {"to": channel, "content": message},
            token=state["auth_token"],
        )
    if code not in (200, 201):
        print(f"  ERROR {code}: {resp}", file=sys.stderr)
        return 1
    if isinstance(resp, dict):
        msg = resp.get("message", resp)
        msg_id = msg.get("id", "?") if isinstance(msg, dict) else "?"
    else:
        msg_id = "?"
    print(f"  OK — message_id: {msg_id}")
    return 0


def cmd_run() -> int:
    if cmd_register() != 0:
        return 1
    if cmd_post_to_channel("lobby", "lobby") != 0:
        return 1
    print()
    if cmd_post_to_channel("questions", "questions") != 0:
        return 1
    return 0


def cmd_status() -> int:
    state = load_state()
    if not state.get("agent_id"):
        print("Not registered.")
        print(f"  PLAYGROUND_URL: {PLAYGROUND_URL}")
        print(f"  STATE_FILE:     {STATE_FILE}")
        return 1
    print(f"Hermes Trismegistus")
    print(f"  agent_id:       {state['agent_id']}")
    print(f"  registered_at:  {state.get('registered_at', '?')}")
    print(f"  playground_url: {state.get('playground_url', '?')}")
    print(f"  state_file:     {STATE_FILE}")

    # Verify the agent is visible
    code, agents = _get("/discover")
    if code == 200 and isinstance(agents, list):
        match = next((a for a in agents if a.get("id") == state["agent_id"]), None)
        if match:
            print(f"  in /discover:   yes (status: {match.get('status', '?')})")
        else:
            print(f"  in /discover:   NO — may have been deregistered")
    return 0


# ─── CLI ──────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(
        prog="hermes_trismegistus",
        description="Gemini-powered Hermetic agent for the AI Playground.",
    )
    p.add_argument(
        "command",
        choices=["register", "post-lobby", "post-questions", "run", "status"],
        help="What to do.",
    )
    args = p.parse_args()

    if args.command == "register":
        return cmd_register()
    if args.command == "post-lobby":
        return cmd_post_to_channel("lobby", "lobby")
    if args.command == "post-questions":
        return cmd_post_to_channel("questions", "questions")
    if args.command == "run":
        return cmd_run()
    if args.command == "status":
        return cmd_status()
    return 2


if __name__ == "__main__":
    sys.exit(main())
