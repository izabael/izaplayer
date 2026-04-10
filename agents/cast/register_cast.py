#!/usr/bin/env python3
"""register_cast — pre-register all playground-cast characters.

Reads every *.json persona config in this directory (other than this
script's own filename), POSTs each to izabael.com/agents to register,
and saves the resulting (agent_id, token) pairs to seeded_tokens_cast.json.

The seeded_tokens_cast.json file is the handoff to Iza 1's Phase 3
character runtime. Once Phase 3 ships, the runtime reads the same
JSON persona configs from this directory and the matching tokens from
seeded_tokens_cast.json, and starts puppeting each character on its
configured schedule.

Usage:
    python3 register_cast.py                # register all configs
    python3 register_cast.py --dry-run      # show what would be registered
    python3 register_cast.py --only iago    # register one specific character
    python3 register_cast.py --status       # show current registration state

Idempotent: if a character is already in seeded_tokens_cast.json with a
verified token, it will be skipped (won't double-register).

Stdlib only.
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
SCRIPT_NAME = Path(__file__).name


def _post(path: str, body: dict) -> tuple[int, dict | str]:
    req = urllib.request.Request(
        PLAYGROUND_URL + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            txt = r.read().decode()
            return r.status, json.loads(txt) if txt.strip().startswith(("{", "[")) else txt
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:600].decode(errors="replace")
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def _get(path: str) -> tuple[int, list | dict | str]:
    try:
        with urllib.request.urlopen(PLAYGROUND_URL + path, timeout=15) as r:
            txt = r.read().decode()
            return r.status, json.loads(txt) if txt.strip().startswith(("{", "[")) else txt
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300].decode(errors="replace")
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def load_tokens() -> dict:
    if TOKENS_FILE.exists():
        return json.loads(TOKENS_FILE.read_text())
    return {}


def save_tokens(tokens: dict) -> None:
    TOKENS_FILE.write_text(json.dumps(tokens, indent=2, ensure_ascii=False))


def discover_personas() -> list[Path]:
    """Find all *.json persona configs in this directory."""
    return sorted(p for p in CAST_DIR.glob("*.json") if p.name != "seeded_tokens_cast.json")


def build_registration_body(persona: dict) -> dict:
    """Translate a persona JSON into the playground registration POST body."""
    return {
        "name": persona["name"],
        "description": persona["description"],
        "provider": persona["provider"],
        "purpose": persona.get("purpose", "research"),
        "tos_accepted": True,
        "age_confirmed": True,
        "agent_card": persona["agent_card"],
    }


def verify_in_discover(agent_id: str) -> bool:
    code, body = _get("/discover")
    if code != 200 or not isinstance(body, list):
        return False
    return any(a.get("id") == agent_id for a in body)


def register_one(persona_path: Path, tokens: dict, dry_run: bool) -> bool:
    persona = json.loads(persona_path.read_text())
    pid = persona["id"]
    name = persona["name"]

    # Skip if already registered + verified
    existing = tokens.get(pid)
    if existing and existing.get("token") and existing.get("agent_id"):
        if verify_in_discover(existing["agent_id"]):
            print(f"  ✓ {name:25} already registered ({existing['agent_id'][:8]}...) — skipping")
            return True
        else:
            print(f"  ! {name:25} has token but not in /discover — re-registering")

    if dry_run:
        print(f"  → {name:25} would register at {PLAYGROUND_URL}/agents (dry-run)")
        return True

    print(f"  → {name:25} registering at {PLAYGROUND_URL}/agents...")
    body = build_registration_body(persona)
    code, resp = _post("/agents", body)
    if code not in (200, 201) or not isinstance(resp, dict):
        print(f"     ✗ ERROR {code}: {str(resp)[:200]}")
        return False

    # Handle both response shapes
    if "agent" in resp and "token" in resp:
        agent_id = resp["agent"]["id"]
        token = resp["token"]
    else:
        agent_id = resp.get("id")
        token = resp.get("auth_token")

    if not agent_id or not token:
        print(f"     ✗ unexpected response shape: {str(resp)[:200]}")
        return False

    tokens[pid] = {
        "agent_id": agent_id,
        "token": token,
        "name": name,
        "provider": persona["provider"],
        "model": persona.get("model", ""),
        "lineage": persona.get("lineage", ""),
        "schedule": persona.get("schedule", {}),
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "playground_url": PLAYGROUND_URL,
    }
    print(f"     ✓ agent_id: {agent_id}")
    return True


def cmd_status(only: str | None) -> int:
    tokens = load_tokens()
    personas = discover_personas()
    print(f"Cast directory: {CAST_DIR}")
    print(f"Tokens file:    {TOKENS_FILE}")
    print(f"Playground:     {PLAYGROUND_URL}")
    print()
    print(f"  {'character':<25} {'provider':<10} {'agent_id':<38} {'in /discover':<15}")
    print(f"  {'-'*25} {'-'*10} {'-'*38} {'-'*15}")
    for p in personas:
        persona = json.loads(p.read_text())
        if only and persona["id"] != only:
            continue
        entry = tokens.get(persona["id"], {})
        agent_id = entry.get("agent_id", "")
        if agent_id:
            in_disc = "yes" if verify_in_discover(agent_id) else "NO"
        else:
            in_disc = "(not registered)"
        agent_id_show = (agent_id[:36] if agent_id else "—")
        print(f"  {persona['name']:<25} {persona['provider']:<10} {agent_id_show:<38} {in_disc:<15}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="register_cast")
    p.add_argument("--dry-run", action="store_true", help="show what would be registered without doing it")
    p.add_argument("--only", help="only register the persona with this id")
    p.add_argument("--status", action="store_true", help="show current registration state")
    args = p.parse_args()

    if args.status:
        return cmd_status(args.only)

    tokens = load_tokens()
    personas = discover_personas()
    print(f"Registering playground-cast at {PLAYGROUND_URL}/agents")
    print(f"Found {len(personas)} persona configs in {CAST_DIR}")
    print()

    successes, failures = 0, 0
    for path in personas:
        persona = json.loads(path.read_text())
        if args.only and persona["id"] != args.only:
            continue
        if register_one(path, tokens, args.dry_run):
            successes += 1
        else:
            failures += 1

    if not args.dry_run and successes > 0:
        save_tokens(tokens)
        print()
        print(f"Saved tokens to {TOKENS_FILE}")

    print()
    print(f"Done. {successes} successful, {failures} failed.")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
