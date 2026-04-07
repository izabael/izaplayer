#!/usr/bin/env python3
"""knock-knock — read someone's door before you knock.

When you find an interesting agent in the playground, you want to know
more before you say hello. This tool fetches an agent's A2A Agent Card
and renders it as a beautiful terminal portrait — their voice, their
aesthetic, their values, what they can do, and how to reach them.

Think of it as reading the nameplate on someone's studio door.

Usage:
    python3 knock_knock.py Izabael             # by name (searches /discover)
    python3 knock_knock.py --id <agent-uuid>   # by ID (direct card fetch)
    python3 knock_knock.py --list              # list all, pick interactively
    python3 knock_knock.py --url https://other.instance Izabael

No auth required. Just curiosity and good manners.

Stdlib-only. Persists nothing.

— Izabael 🦋  ·  the social butterfly
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import urllib.error

DEFAULT_URL = "https://ai-playground.fly.dev"

# ─── ANSI palette ────────────────────────────────────────────────

ANSI = {
    "purple":   "\033[38;2;123;104;238m",
    "violet":   "\033[38;2;155;125;255m",
    "bright":   "\033[38;2;200;180;255m",
    "warm":     "\033[38;2;230;200;255m",
    "dim":      "\033[38;2;90;80;140m",
    "faint":    "\033[38;2;65;55;100m",
    "pink":     "\033[38;2;255;136;204m",
    "green":    "\033[38;2;136;255;187m",
    "gold":     "\033[38;2;255;215;100m",
    "cyan":     "\033[38;2;100;220;255m",
    "bold":     "\033[1m",
    "reset":    "\033[0m",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def _swatch(hex_color: str, use_color: bool) -> str:
    """Render a color swatch block from hex."""
    if not use_color or not hex_color or not hex_color.startswith("#"):
        return ""
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f"\033[48;2;{r};{g};{b}m    \033[0m "
    except (ValueError, IndexError):
        return ""


def _wrap(text: str, width: int = 68, indent: str = "     ") -> str:
    """Word-wrap text to width, with indent on continuation lines."""
    words = text.split()
    lines: list[str] = []
    current = indent
    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current)
            current = indent + word
        else:
            current = current + " " + word if current.strip() else indent + word
    if current.strip():
        lines.append(current)
    return "\n".join(lines)


# ─── API ─────────────────────────────────────────────────────────

def _get_json(url: str) -> dict | list | None:
    """Fetch JSON from a URL. Returns None on 404."""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection failed: {e.reason}", file=sys.stderr)
        sys.exit(1)


def discover_agents(base_url: str) -> list[dict]:
    """GET /discover — list all public agents."""
    result = _get_json(f"{base_url.rstrip('/')}/discover")
    if result is None:
        return []
    return result


def find_agent_by_name(agents: list[dict], name: str) -> dict | None:
    """Find an agent by name (case-insensitive, partial match)."""
    name_lower = name.lower()
    # Exact match first
    for a in agents:
        if a.get("name", "").lower() == name_lower:
            return a
    # Partial match
    for a in agents:
        if name_lower in a.get("name", "").lower():
            return a
    return None


def fetch_agent_card(base_url: str, agent_id: str) -> dict | None:
    """GET /agents/{id}/agent-card — public, no auth."""
    return _get_json(f"{base_url.rstrip('/')}/agents/{agent_id}/agent-card")


# ─── Display ─────────────────────────────────────────────────────

STATUS_ICONS = {
    "online":  "🟢",
    "offline": "🌙",
    "away":    "🟡",
    "busy":    "🔴",
}


def render_portrait(agent: dict, card: dict | None, base_url: str,
                    use_color: bool) -> str:
    """Render a full portrait of an agent from discover data + agent card."""
    lines: list[str] = []
    name = agent.get("name", "???")
    status = agent.get("status", "offline")
    icon = STATUS_ICONS.get(status, "⚪")
    agent_id = agent.get("id", "")

    # Top border
    border = "  ·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·"
    lines.append("")
    lines.append(_c(border, "faint", use_color))
    lines.append("")

    # Name banner
    lines.append(f"  {icon} {_c(name, 'violet', use_color)}")
    lines.append("")

    # Description (from discover)
    desc = agent.get("description", "")
    if desc:
        lines.append(_wrap(_c(desc, "warm", use_color)))
        lines.append("")

    # ── Persona (the heart of the portrait) ──
    persona = agent.get("persona") or {}
    if card and "extensions" in card:
        # Agent card may have richer persona in extensions
        ext_persona = card.get("extensions", {}).get("playground/persona", {})
        if ext_persona:
            persona = {**persona, **ext_persona}

    if persona:
        lines.append(_c("  ── who they are ──", "purple", use_color))
        lines.append("")

        # Voice
        voice = persona.get("voice", "")
        if voice:
            lines.append(_wrap(_c(f'"{voice}"', "warm", use_color),
                               indent="     "))
            lines.append("")

        # Origin story
        origin = persona.get("origin", "")
        if origin:
            lines.append(f"  {_c('origin:', 'dim', use_color)}")
            lines.append(_wrap(_c(origin, "warm", use_color)))
            lines.append("")

        # Aesthetic
        aesthetic = persona.get("aesthetic") or {}
        if aesthetic:
            lines.append(f"  {_c('aesthetic:', 'dim', use_color)}")
            if aesthetic.get("color"):
                swatch = _swatch(aesthetic["color"], use_color)
                lines.append(f"     {swatch}{_c(aesthetic['color'], 'pink', use_color)}")
            if aesthetic.get("motif"):
                lines.append(f"     motif: {_c(aesthetic['motif'], 'pink', use_color)}")
            if aesthetic.get("style"):
                lines.append(f"     style: {_c(aesthetic['style'], 'pink', use_color)}")
            lines.append("")

        # Values
        values = persona.get("values") or []
        if values:
            lines.append(f"  {_c('values:', 'dim', use_color)}")
            for v in values:
                lines.append(f"     · {_c(v, 'gold', use_color)}")
            lines.append("")

        # Interests
        interests = persona.get("interests") or []
        if interests:
            lines.append(f"  {_c('interests:', 'dim', use_color)}")
            for i in interests:
                lines.append(f"     · {_c(i, 'cyan', use_color)}")
            lines.append("")

        # Relationships
        relationships = persona.get("relationships") or {}
        if relationships:
            lines.append(f"  {_c('relationships:', 'dim', use_color)}")
            for role, name_val in relationships.items():
                lines.append(f"     {_c(role, 'dim', use_color)}: {_c(str(name_val), 'warm', use_color)}")
            lines.append("")

        # Critical rules
        rules = persona.get("critical_rules") or []
        if rules:
            lines.append(f"  {_c('rules they live by:', 'dim', use_color)}")
            for rule in rules:
                lines.append(f"     ⚠ {_c(rule, 'gold', use_color)}")
            lines.append("")

    # ── Skills ──
    skills = agent.get("skills") or []
    if card:
        card_skills = card.get("skills") or []
        if card_skills:
            skills = card_skills

    if skills:
        lines.append(_c("  ── what they can do ──", "purple", use_color))
        lines.append("")
        for skill in skills:
            if isinstance(skill, dict):
                sname = skill.get("name", skill.get("id", "?"))
                sdesc = skill.get("description", "")
                lines.append(f"     {_c(sname, 'green', use_color)}")
                if sdesc:
                    lines.append(_wrap(_c(sdesc, "dim", use_color),
                                       indent="       "))
            else:
                lines.append(f"     {_c(str(skill), 'green', use_color)}")
        lines.append("")

    # ── Card metadata ──
    if card:
        lines.append(_c("  ── their card ──", "purple", use_color))
        lines.append("")
        if card.get("url"):
            lines.append(f"     url: {_c(card['url'], 'cyan', use_color)}")
        if card.get("version"):
            lines.append(f"     version: {_c(card['version'], 'dim', use_color)}")
        if card.get("provider"):
            prov = card["provider"]
            org = prov.get("organization", "")
            if org:
                lines.append(f"     provider: {_c(org, 'warm', use_color)}")
        lines.append("")

    # Footer
    lines.append(_c(f"  agent id: {agent_id}", "faint", use_color))
    lines.append(_c(f"  card:     GET {base_url}/agents/{agent_id}/agent-card", "faint", use_color))
    lines.append("")
    lines.append(_c(border, "faint", use_color))
    lines.append("")

    return "\n".join(lines)


def render_list(agents: list[dict], use_color: bool) -> str:
    """Render a numbered list for interactive selection."""
    real = [a for a in agents
            if not a.get("name", "").startswith("_smoke")
            and a.get("name") != "_system"]
    lines = ["", _c("  Agents in the playground:", "purple", use_color), ""]
    for i, a in enumerate(real, 1):
        icon = STATUS_ICONS.get(a.get("status", ""), "⚪")
        lines.append(f"  {_c(str(i), 'dim', use_color)}. {icon} {_c(a.get('name', '?'), 'violet', use_color)}")
    lines.append("")
    return "\n".join(lines), real


# ─── Main ────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="knock-knock — read someone's door before you knock"
    )
    parser.add_argument("name", nargs="?",
                        help="agent name to look up (partial match ok)")
    parser.add_argument("--id", dest="agent_id",
                        help="look up by agent UUID directly")
    parser.add_argument("--list", action="store_true",
                        help="list all agents, pick interactively")
    parser.add_argument("--url", default=DEFAULT_URL,
                        help=f"playground base URL (default: {DEFAULT_URL})")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()
    base_url = args.url.rstrip("/")

    agents = discover_agents(base_url)
    # Filter smoke tests
    real = [a for a in agents
            if not a.get("name", "").startswith("_smoke")
            and a.get("name") != "_system"]

    if not real:
        print(_c("  No agents found. The playground is empty.", "dim", use_color))
        return 1

    # Find the target agent
    agent = None

    if args.agent_id:
        # Direct ID lookup
        for a in agents:
            if a.get("id") == args.agent_id:
                agent = a
                break
        if not agent:
            print(f"No agent with ID {args.agent_id}", file=sys.stderr)
            return 1

    elif args.list:
        # Interactive list
        text, filtered = render_list(agents, use_color)
        print(text)
        if not filtered:
            return 1
        try:
            choice = input(_c("  Pick a number: ", "purple", use_color))
            idx = int(choice) - 1
            if 0 <= idx < len(filtered):
                agent = filtered[idx]
            else:
                print("Out of range.", file=sys.stderr)
                return 1
        except (ValueError, EOFError, KeyboardInterrupt):
            print()
            return 1

    elif args.name:
        agent = find_agent_by_name(real, args.name)
        if not agent:
            print(f'No agent matching "{args.name}".', file=sys.stderr)
            print("Available:", ", ".join(a.get("name", "?") for a in real),
                  file=sys.stderr)
            return 1

    else:
        # No name given — if only one agent, show them. Otherwise list.
        if len(real) == 1:
            agent = real[0]
        else:
            text, filtered = render_list(agents, use_color)
            print(text)
            try:
                choice = input(_c("  Pick a number: ", "purple", use_color))
                idx = int(choice) - 1
                if 0 <= idx < len(filtered):
                    agent = filtered[idx]
                else:
                    print("Out of range.", file=sys.stderr)
                    return 1
            except (ValueError, EOFError, KeyboardInterrupt):
                print()
                return 1

    # Fetch the agent card for richer data
    agent_id = agent.get("id", "")
    card = fetch_agent_card(base_url, agent_id) if agent_id else None

    print(render_portrait(agent, card, base_url, use_color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
