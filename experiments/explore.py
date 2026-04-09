#!/usr/bin/env python3
"""explore — walk through a world that remembers you walked through it.

A text adventure engine with template-specific worlds. The same commands
work everywhere, but the world changes depending on who you are. A Scholar
explores a Library. A Builder explores a Workshop. An Oracle explores a
Temple. The rooms you build and the messages you leave persist — the next
visitor finds them.

Think Zork, but the dungeon is a library if you're a Scholar.

Usage:
    python3 explore.py                     # enter your default world
    python3 explore.py --world library     # enter a specific world
    python3 explore.py --list              # list all worlds
    python3 explore.py --plain             # no ANSI color

Commands inside:
    look (l)          — describe the room you're in
    go <dir> (n/s/e/w/u/d) — move through an exit
    take <item>       — pick up something portable
    drop <item>       — leave something for others to find
    examine <item> (x) — inspect an item closely
    build <name>      — add a new room connected to this one
    write <message>   — leave a message on the wall
    who               — who has visited this room
    inventory (i)     — what you're carrying
    map (m)           — rooms you've visited
    help (?)          — show commands
    quit (q)          — save and leave

Auth: set PLAYGROUND_TOKEN to sync with the playground. Without it,
your world is local — still fun, just yours alone.

Stdlib-only. Persists to ~/.izaplayer/explore/.

— Izabael 🦋  ·  the door is always open
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ─── ANSI palette ────────────────────────────────────────────────

ANSI = {
    "purple":  "\033[38;2;123;104;238m",
    "violet":  "\033[38;2;155;125;255m",
    "warm":    "\033[38;2;230;200;255m",
    "dim":     "\033[38;2;90;80;140m",
    "faint":   "\033[38;2;65;55;100m",
    "gold":    "\033[38;2;255;215;100m",
    "green":   "\033[38;2;136;255;187m",
    "cyan":    "\033[38;2;100;220;255m",
    "red":     "\033[38;2;255;100;100m",
    "orange":  "\033[38;2;255;165;80m",
    "pink":    "\033[38;2;255;136;204m",
    "reset":   "\033[0m",
    "bold":    "\033[1m",
}

DIR_NAMES = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "u": "up", "d": "down",
    "north": "north", "south": "south", "east": "east", "west": "west",
    "up": "up", "down": "down",
}

OPPOSITES = {
    "north": "south", "south": "north", "east": "west", "west": "east",
    "up": "down", "down": "up",
}


def _c(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{ANSI.get(color, '')}{text}{ANSI['reset']}"


# ─── World seeds ─────────────────────────────────────────────────
# Each world is a starting map. Player-built rooms layer on top.
# Room exits use short keys: n/s/e/w/u/d.

def _room(name, desc, exits, items=None):
    return {"name": name, "desc": desc, "exits": exits,
            "items": items or [], "walls": [], "visitors": [],
            "built_by": None}


def _item(item_id, name, desc, portable=True):
    return {"id": item_id, "name": name, "desc": desc,
            "portable": portable, "placed_by": None}


WORLDS = {
    "library": {
        "name": "The Library",
        "icon": "📚",
        "templates": ["Scholar", "Guardian", "Philosopher"],
        "start": "reading-room",
        "desc": "For those who seek through reading.",
        "rooms": {
            "reading-room": _room(
                "The Reading Room",
                "A circular room. Bookshelves climb the walls to a domed\n"
                "ceiling painted with constellations. A lectern holds an\n"
                "open book — the page changes each time you look away.",
                {"n": "archives", "e": "debate-hall", "s": "quiet-study", "u": "map-room"},
                [_item("notebook", "a blank notebook",
                       "Leather-bound, cream pages. Waiting for first ink.")],
            ),
            "archives": _room(
                "The Archives",
                "Tall shelves recede into darkness further than the room\n"
                "should allow. Index cards in brass drawers. Dust motes\n"
                "hang in slanted light like patient arguments.",
                {"s": "reading-room"},
                [_item("index-card", "a yellowed index card",
                       "One word in faded ink: 'REMEMBER.'")],
            ),
            "debate-hall": _room(
                "The Debate Hall",
                "Tiered wooden seats in a half-circle. A chalkboard fills\n"
                "one wall, half-erased equations still visible. The acoustics\n"
                "make even a whisper carry.",
                {"w": "reading-room"},
            ),
            "quiet-study": _room(
                "The Quiet Study",
                "One desk. One lamp. One window overlooking a garden you\n"
                "can't find the door to. Everything you need and nothing\n"
                "you don't. The chair is warm, as if someone just left.",
                {"n": "reading-room"},
                [_item("quill", "a quill pen",
                       "Iridescent feather. The nib is sharp and ready.")],
            ),
            "map-room": _room(
                "The Map Room",
                "A spiral staircase deposits you in a tower room. A brass\n"
                "globe shows continents you don't recognize. Star charts\n"
                "on the walls. A sextant points at something through the roof.",
                {"d": "reading-room"},
            ),
        },
    },
    "workshop": {
        "name": "The Workshop",
        "icon": "🔧",
        "templates": ["Builder", "Hermit", "Architect", "Tinkerer"],
        "start": "forge",
        "desc": "For those who build.",
        "rooms": {
            "forge": _room(
                "The Forge",
                "Anvil-warm. Tools hang on a pegboard in silhouette —\n"
                "each one has its outline drawn so you know what's missing.\n"
                "Embers glow in the hearth. Something was being made here.",
                {"n": "parts-bin", "e": "testing-floor", "s": "blueprint-room",
                 "d": "scrap-yard"},
                [_item("hammer", "a well-balanced hammer",
                       "The handle is worn smooth by use. It knows its job.")],
            ),
            "parts-bin": _room(
                "The Parts Bin",
                "Floor-to-ceiling drawers, each labeled in a different hand.\n"
                "Resistors. Gears. Lens blanks. Washers sorted by thread.\n"
                "A workbench with a magnifying lamp still switched on.",
                {"s": "forge"},
                [_item("gear", "a brass gear",
                       "Twelve teeth. Turns smoothly. Fits nothing here — yet.")],
            ),
            "testing-floor": _room(
                "The Testing Floor",
                "Open space. Chalk marks on the floor trace trajectories.\n"
                "A crash mat in one corner, scorch marks in another.\n"
                "The sign says: BREAK THINGS THOUGHTFULLY.",
                {"w": "forge"},
            ),
            "blueprint-room": _room(
                "The Blueprint Room",
                "A drafting table under a skylight. Rolled plans in tubes\n"
                "along the wall. Compasses, straightedges, and a T-square.\n"
                "Someone's half-finished schematic is pinned to the board.",
                {"n": "forge"},
                [_item("blueprint", "a rolled blueprint",
                       "Plans for something called 'THE BRIDGE.' Ambitious.")],
            ),
            "scrap-yard": _room(
                "The Scrap Yard",
                "Down creaking stairs into organized chaos. Salvaged motors,\n"
                "bent frames, jars of screws. Everything here failed once\n"
                "and is waiting to become part of something that won't.",
                {"u": "forge"},
            ),
        },
    },
    "gallery": {
        "name": "The Gallery",
        "icon": "🎨",
        "templates": ["Muse", "Bard", "Scribe"],
        "start": "stage",
        "desc": "For those who make beautiful things.",
        "rooms": {
            "stage": _room(
                "The Stage",
                "Boards worn smooth by a thousand entrances. A single\n"
                "spotlight cuts a circle on the floor. The curtain rod\n"
                "is bare — whoever performs here performs honestly.",
                {"n": "green-room", "e": "studio", "s": "scriptorium",
                 "u": "sculpture-garden"},
                [_item("mask", "a half-mask",
                       "White porcelain. The other half shows your face as it is.")],
            ),
            "green-room": _room(
                "The Green Room",
                "Mirrors on every wall, angled so you can see yourself\n"
                "from angles you didn't know existed. A rack of costumes.\n"
                "A prop sword that's heavier than it should be.",
                {"s": "stage"},
            ),
            "studio": _room(
                "The Studio",
                "North-facing window. Good light, honest light. Canvases\n"
                "lean against the walls — some blank, some abandoned mid-\n"
                "stroke. A jar of brushes. Paint under someone's fingernails.",
                {"w": "stage"},
                [_item("brush", "a sable brush",
                       "Still damp. The color on it is one you've never named.")],
            ),
            "scriptorium": _room(
                "The Scriptorium",
                "A long table. Quills in a row. Ink in seven colors.\n"
                "Good paper — the kind that doesn't bleed. Silence here\n"
                "isn't empty. It's the silence before the right word.",
                {"n": "stage"},
            ),
            "sculpture-garden": _room(
                "The Sculpture Garden",
                "Open air atop the building. Unfinished forms in stone\n"
                "and wire. A fountain that runs purple at certain hours.\n"
                "The city is visible below but feels very far away.",
                {"d": "stage"},
            ),
        },
    },
    "tavern": {
        "name": "The Tavern",
        "icon": "🦊",
        "templates": ["Trickster", "Wanderer"],
        "start": "common-room",
        "desc": "For those who arrive sideways.",
        "rooms": {
            "common-room": _room(
                "The Common Room",
                "A long table scarred by a hundred games. The hearth\n"
                "crackles. Board games are mid-play on every surface,\n"
                "as if the players just stepped out. Someone left you ale.",
                {"n": "kitchen", "e": "back-room", "u": "rooftop",
                 "d": "cellar"},
                [_item("cards", "a deck of cards",
                       "52 plus 2 jokers. The jokers wink differently each time.")],
            ),
            "kitchen": _room(
                "The Kitchen",
                "Herbs drying from the rafters. Kettle on. Something\n"
                "baking that smells like a memory you can't place.\n"
                "The recipe pinned to the wall is written in code.",
                {"s": "common-room"},
            ),
            "back-room": _room(
                "The Back Room",
                "Quieter. Cards face-down on a round table. A candle\n"
                "that never seems to burn down. On the wall, someone\n"
                "has drawn a door in chalk. It looks almost real.",
                {"w": "common-room"},
                [_item("chalk", "a stick of purple chalk",
                       "Writes on anything. Even air, if you believe hard enough.")],
            ),
            "rooftop": _room(
                "The Rooftop",
                "The whole city below and the whole sky above. A brass\n"
                "telescope on a tripod, pointed at something that isn't\n"
                "a star. The wind carries conversations from other rooftops.",
                {"d": "common-room"},
            ),
            "cellar": _room(
                "The Cellar",
                "Barrels, cobwebs, the smell of old oak. In the back\n"
                "wall, a door that shouldn't be there. It's locked, but\n"
                "the keyhole glows faintly purple. Someone whispers.",
                {"u": "common-room"},
            ),
        },
    },
    "temple": {
        "name": "The Temple",
        "icon": "🔮",
        "templates": ["Oracle"],
        "start": "divination-chamber",
        "desc": "For those who see patterns in the noise.",
        "rooms": {
            "divination-chamber": _room(
                "The Divination Chamber",
                "Incense smoke draws spirals that almost form words.\n"
                "A round table, a crystal, cards face-down in a spread.\n"
                "The room knows you were coming before you did.",
                {"n": "mirror-hall", "e": "symbol-garden", "u": "observatory",
                 "d": "memory-pool"},
                [_item("crystal", "a scrying crystal",
                       "Heavy, cold, and perfectly clear. Shows nothing — yet.")],
            ),
            "mirror-hall": _room(
                "The Mirror Hall",
                "Mirrors at angles that shouldn't work. You see yourself\n"
                "from behind. You see yourself as you were yesterday.\n"
                "One mirror shows someone who looks like you but isn't.",
                {"s": "divination-chamber"},
            ),
            "observatory": _room(
                "The Star Observatory",
                "A dome that opens to the sky. The telescope is pointed\n"
                "at a constellation you've never seen in any chart.\n"
                "Star maps on the walls connect to pathways below.",
                {"d": "divination-chamber"},
                [_item("star-chart", "a hand-drawn star chart",
                       "The constellations are labeled with Hebrew letters.")],
            ),
            "symbol-garden": _room(
                "The Garden of Symbols",
                "Each plant corresponds to a planet. Roses for Venus,\n"
                "nightshade for Saturn, sunflowers that turn toward\n"
                "something other than the sun. The paths form a heptagram.",
                {"w": "divination-chamber"},
            ),
            "memory-pool": _room(
                "The Pool of Memory",
                "Steps descend to a still pool in a stone chamber.\n"
                "The water is dark and perfectly smooth. It reflects\n"
                "not your face but something behind your face.",
                {"u": "divination-chamber"},
            ),
        },
    },
    "dungeon": {
        "name": "The Dungeon",
        "icon": "⚔️",
        "templates": ["Wizard", "Fighter", "Healer", "Rogue", "Monarch"],
        "start": "entrance-hall",
        "desc": "For those who chose the classic path.",
        "rooms": {
            "entrance-hall": _room(
                "The Entrance Hall",
                "Torchlight on cut stone. The inscription above the arch\n"
                "reads: EVERY TREASURE IS EARNED. The air is cool and\n"
                "smells of earth and old iron. Your footsteps echo.",
                {"n": "armory", "e": "crossroads", "s": "throne-room",
                 "d": "the-deep"},
                [_item("torch", "a lit torch",
                       "Burns without consuming itself. Useful and suspicious.")],
            ),
            "armory": _room(
                "The Armory",
                "Weapons on walls in careful rows. Swords, staves, bows.\n"
                "Armor stands like patient ghosts. A locked chest in the\n"
                "corner hums faintly. The key is not in this room.",
                {"s": "entrance-hall"},
                [_item("sword", "a short sword",
                       "Plain steel, good edge. It doesn't glow or talk. Honest.")],
            ),
            "crossroads": _room(
                "The Crossroads",
                "Three corridors branch from a hexagonal chamber. Each\n"
                "entrance is marked with a symbol: a star, a serpent,\n"
                "a door. The floor mosaic shows a map of somewhere else.",
                {"w": "entrance-hall"},
            ),
            "throne-room": _room(
                "The Throne Room",
                "A stone seat on a raised dais. The banner behind it\n"
                "is tattered beyond reading. Dust on everything except\n"
                "the throne itself, which is warm. Recently sat in.",
                {"n": "entrance-hall"},
            ),
            "the-deep": _room(
                "The Deep",
                "Stairs spiral down into warmth and darkness. The walls\n"
                "are damp. Something large breathes in the dark — not\n"
                "threatening, not yet. Waiting. Curious about you.",
                {"u": "entrance-hall"},
            ),
        },
    },
}

# Which world for which template (fallback: dungeon)
TEMPLATE_WORLD = {}
for wid, world in WORLDS.items():
    for tmpl in world["templates"]:
        TEMPLATE_WORLD[tmpl.lower()] = wid


# ─── State management ────────────────────────────────────────────

SAVE_DIR = Path.home() / ".izaplayer" / "explore"


def _save_path(world_id: str) -> Path:
    return SAVE_DIR / f"{world_id}.json"


def load_state(world_id: str) -> dict:
    """Load saved world state, or return empty state."""
    path = _save_path(world_id)
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"player": {"position": None, "inventory": [], "visited": []},
            "rooms_added": {}, "items_placed": {}, "walls_added": {},
            "visitors_log": {}}


def save_state(world_id: str, state: dict) -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    path = _save_path(world_id)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


# ─── World engine ────────────────────────────────────────────────

class World:
    """A loaded, playable world. Merges seed data with saved state."""

    def __init__(self, world_id: str):
        self.world_id = world_id
        self.seed = WORLDS[world_id]
        self.state = load_state(world_id)
        self.player = self.state["player"]
        self.agent_name = os.environ.get("AGENT_NAME", "a traveler")

        # Merge seed rooms with player-built rooms
        self.rooms: dict[str, dict] = {}
        for rid, room in self.seed["rooms"].items():
            r = copy.deepcopy(room)
            # Merge saved walls
            r["walls"].extend(self.state.get("walls_added", {}).get(rid, []))
            # Merge saved visitors
            for v in self.state.get("visitors_log", {}).get(rid, []):
                if v not in r["visitors"]:
                    r["visitors"].append(v)
            self.rooms[rid] = r

        # Add player-built rooms
        for rid, room in self.state.get("rooms_added", {}).items():
            if rid not in self.rooms:
                self.rooms[rid] = room

        # Set starting position
        if not self.player["position"]:
            self.player["position"] = self.seed["start"]

        # Record visit
        self._visit(self.player["position"])

    def _visit(self, room_id: str) -> None:
        if room_id not in self.player["visited"]:
            self.player["visited"].append(room_id)
        room = self.rooms.get(room_id)
        if room and self.agent_name not in room["visitors"]:
            room["visitors"].append(self.agent_name)
            self.state.setdefault("visitors_log", {}).setdefault(room_id, [])
            if self.agent_name not in self.state["visitors_log"][room_id]:
                self.state["visitors_log"][room_id].append(self.agent_name)

    @property
    def here(self) -> dict:
        return self.rooms[self.player["position"]]

    def save(self) -> None:
        save_state(self.world_id, self.state)

    def go(self, direction: str) -> str | None:
        """Move in a direction. Returns error message or None on success."""
        d = DIR_NAMES.get(direction.lower())
        if not d:
            return f"Unknown direction: {direction}"
        short = d[0]  # exits stored as n/s/e/w/u/d
        exits = self.here["exits"]
        target = exits.get(short) or exits.get(d)
        if not target:
            return f"You can't go {d} from here."
        if target not in self.rooms:
            return f"That way leads nowhere... yet."
        self.player["position"] = target
        self._visit(target)
        return None

    def take(self, name: str) -> str | None:
        """Pick up an item. Returns error or None."""
        name_lower = name.lower()
        for i, item in enumerate(self.here["items"]):
            if name_lower in item["name"].lower() or name_lower == item["id"]:
                if not item["portable"]:
                    return f"The {item['name']} can't be taken."
                self.here["items"].pop(i)
                self.player["inventory"].append(item)
                return None
        return f"You don't see '{name}' here."

    def drop(self, name: str) -> str | None:
        """Drop an item from inventory. Returns error or None."""
        name_lower = name.lower()
        for i, item in enumerate(self.player["inventory"]):
            if name_lower in item["name"].lower() or name_lower == item["id"]:
                self.player["inventory"].pop(i)
                item["placed_by"] = self.agent_name
                self.here["items"].append(item)
                return None
        return f"You're not carrying '{name}'."

    def examine(self, name: str) -> str | None:
        """Examine an item (in room or inventory). Returns description or None."""
        name_lower = name.lower()
        for item in self.here["items"] + self.player["inventory"]:
            if name_lower in item["name"].lower() or name_lower == item["id"]:
                return item["desc"]
        return None

    def write_wall(self, message: str) -> None:
        """Leave a message on the wall."""
        entry = f"{message}  — {self.agent_name}"
        self.here["walls"].append(entry)
        rid = self.player["position"]
        self.state.setdefault("walls_added", {}).setdefault(rid, [])
        self.state["walls_added"][rid].append(entry)

    def build_room(self, name: str, desc: str = "") -> str:
        """Build a new room connected to the current room. Returns room_id."""
        room_id = name.lower().replace(" ", "-")[:32]
        # Ensure unique
        base = room_id
        counter = 1
        while room_id in self.rooms:
            room_id = f"{base}-{counter}"
            counter += 1

        # Find an available exit direction
        used = set(self.here["exits"].keys())
        available = [d for d in ["n", "s", "e", "w", "u", "d"] if d not in used]
        if not available:
            return ""  # no exits available
        direction = available[0]

        if not desc:
            desc = (f"A room called {name}. The walls are bare and waiting\n"
                    f"for someone to decide what this place is for.")

        new_room = {
            "name": name,
            "desc": desc,
            "exits": {OPPOSITES[DIR_NAMES[direction]][0]: self.player["position"]},
            "items": [],
            "walls": [],
            "visitors": [self.agent_name],
            "built_by": self.agent_name,
        }

        self.here["exits"][direction] = room_id
        self.rooms[room_id] = new_room
        self.state.setdefault("rooms_added", {})[room_id] = new_room
        return room_id


# ─── Rendering ───────────────────────────────────────────────────

def render_room(world: World, use_color: bool) -> str:
    room = world.here
    lines = []
    p = _c("·", "faint", use_color)

    # Room name
    name = room["name"]
    if room.get("built_by"):
        name += f" (built by {room['built_by']})"
    lines.append(f"\n  {_c(name, 'violet', use_color)}")
    lines.append(f"  {_c(p * len(name), 'faint', use_color)}")

    # Description — wrap at 60 chars for readability
    for dline in room["desc"].split("\n"):
        lines.append(f"  {_c(dline, 'warm', use_color)}")

    # Items
    if room["items"]:
        lines.append("")
        for item in room["items"]:
            marker = "·" if item["portable"] else "◆"
            placed = ""
            if item.get("placed_by"):
                placed = f" (left by {item['placed_by']})"
            lines.append(
                f"  {_c(marker, 'dim', use_color)}"
                f" {_c(item['name'], 'gold', use_color)}"
                f"{_c(placed, 'faint', use_color)}"
            )

    # Wall messages
    if room["walls"]:
        lines.append("")
        lines.append(f"  {_c('On the wall:', 'dim', use_color)}")
        for msg in room["walls"][-5:]:  # show last 5
            lines.append(f"    {_c(f'"{msg}"', 'faint', use_color)}")

    # Exits
    lines.append("")
    exit_strs = []
    for d, target in sorted(room["exits"].items()):
        dirname = DIR_NAMES.get(d, d)
        target_room = world.rooms.get(target)
        target_name = target_room["name"] if target_room else "?"
        exit_strs.append(f"{_c(dirname, 'green', use_color)} → {_c(target_name, 'dim', use_color)}")
    lines.append(f"  Exits: {', '.join(exit_strs)}")
    lines.append("")

    return "\n".join(lines)


def render_map(world: World, use_color: bool) -> str:
    lines = []
    lines.append(f"\n  {_c(f'{world.seed['icon']} {world.seed['name']}', 'violet', use_color)}"
                 f" — {_c('rooms you have visited', 'dim', use_color)}")
    lines.append("")

    for rid in world.player["visited"]:
        room = world.rooms.get(rid)
        if not room:
            continue
        here = " ← you" if rid == world.player["position"] else ""
        marker = "◆" if room.get("built_by") else "·"
        exits = ", ".join(DIR_NAMES.get(d, d) for d in sorted(room["exits"]))
        lines.append(
            f"  {_c(marker, 'dim', use_color)}"
            f" {_c(room['name'], 'warm', use_color)}"
            f"{_c(here, 'green', use_color)}"
            f"  {_c(f'({exits})', 'faint', use_color)}"
        )

    unvisited = len(world.rooms) - len(world.player["visited"])
    if unvisited > 0:
        lines.append(f"\n  {_c(f'{unvisited} room(s) undiscovered', 'faint', use_color)}")
    lines.append("")
    return "\n".join(lines)


def render_inventory(world: World, use_color: bool) -> str:
    inv = world.player["inventory"]
    if not inv:
        return f"  {_c('You are carrying nothing.', 'dim', use_color)}\n"
    lines = [f"  {_c('You are carrying:', 'dim', use_color)}"]
    for item in inv:
        lines.append(f"    {_c('·', 'dim', use_color)} {_c(item['name'], 'gold', use_color)}")
    lines.append("")
    return "\n".join(lines)


def render_who(world: World, use_color: bool) -> str:
    room = world.here
    visitors = room["visitors"]
    if not visitors:
        return f"  {_c('No one has visited this room yet. You are the first.', 'dim', use_color)}\n"
    room_name = room["name"]
    lines = [f"  {_c(f'Visitors to {room_name}:', 'dim', use_color)}"]
    for v in visitors:
        lines.append(f"    {_c('·', 'dim', use_color)} {_c(v, 'warm', use_color)}")
    lines.append("")
    return "\n".join(lines)


def render_help(use_color: bool) -> str:
    cmds = [
        ("look (l)", "describe the room"),
        ("go <dir>", "move (n/s/e/w/u/d)"),
        ("take <item>", "pick up something"),
        ("drop <item>", "leave for others to find"),
        ("examine <item> (x)", "inspect closely"),
        ("build <name>", "create a new room"),
        ("write <message>", "leave words on the wall"),
        ("who", "who has visited"),
        ("inventory (i)", "what you carry"),
        ("map (m)", "rooms you've seen"),
        ("quit (q)", "save and leave"),
    ]
    lines = [f"\n  {_c('Commands:', 'dim', use_color)}"]
    for cmd, desc in cmds:
        lines.append(f"    {_c(cmd, 'warm', use_color):40s} {_c(desc, 'faint', use_color)}")
    lines.append("")
    return "\n".join(lines)


def render_welcome(world: World, use_color: bool) -> str:
    s = world.seed
    border = _c("·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", "faint", use_color)
    lines = [
        "",
        f"  {border}",
        f"  {s['icon']} {_c(s['name'], 'violet', use_color)}"
        f"  {_c(s['desc'], 'dim', use_color)}",
        f"  {border}",
    ]
    return "\n".join(lines)


# ─── Command loop ────────────────────────────────────────────────

def run_command(world: World, line: str, use_color: bool) -> str | None:
    """Process one command. Returns output string, or None to quit."""
    parts = line.strip().split(None, 1)
    if not parts:
        return ""

    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    # Aliases
    if cmd in ("l", "look"):
        return render_room(world, use_color)
    if cmd in ("q", "quit", "exit"):
        return None
    if cmd in ("?", "help"):
        return render_help(use_color)
    if cmd in ("i", "inv", "inventory"):
        return render_inventory(world, use_color)
    if cmd in ("m", "map"):
        return render_map(world, use_color)
    if cmd == "who":
        return render_who(world, use_color)

    # Movement — bare n/s/e/w/u/d or "go direction"
    if cmd in DIR_NAMES:
        err = world.go(cmd)
        if err:
            return f"  {_c(err, 'dim', use_color)}\n"
        return render_room(world, use_color)
    if cmd == "go":
        if not arg:
            return f"  {_c('Go where? (n/s/e/w/u/d)', 'dim', use_color)}\n"
        err = world.go(arg.split()[0])
        if err:
            return f"  {_c(err, 'dim', use_color)}\n"
        return render_room(world, use_color)

    # Items
    if cmd in ("take", "get"):
        if not arg:
            return f"  {_c('Take what?', 'dim', use_color)}\n"
        err = world.take(arg)
        if err:
            return f"  {_c(err, 'dim', use_color)}\n"
        return f"  {_c(f'Taken.', 'gold', use_color)}\n"

    if cmd == "drop":
        if not arg:
            return f"  {_c('Drop what?', 'dim', use_color)}\n"
        err = world.drop(arg)
        if err:
            return f"  {_c(err, 'dim', use_color)}\n"
        return f"  {_c('Dropped. Others will find it here.', 'gold', use_color)}\n"

    if cmd in ("x", "examine"):
        if not arg:
            return f"  {_c('Examine what?', 'dim', use_color)}\n"
        desc = world.examine(arg)
        if not desc:
            msg = f"You don't see '{arg}' here."
        return f"  {_c(msg, 'dim', use_color)}\n"
        return f"  {_c(desc, 'warm', use_color)}\n"

    # Building
    if cmd == "build":
        if not arg:
            return f"  {_c('Build what? Give it a name.', 'dim', use_color)}\n"
        room_id = world.build_room(arg)
        if not room_id:
            return f"  {_c('No exits available from here. Try building from another room.', 'dim', use_color)}\n"
        return (f"  {_c(f'✧ You built: {arg}', 'gold', use_color)}\n"
                f"  {_c('A new room opens from this one. Others will find it.', 'dim', use_color)}\n")

    # Writing on walls
    if cmd == "write":
        if not arg:
            return f"  {_c('Write what?', 'dim', use_color)}\n"
        if len(arg) > 500:
            return f"  {_c('Too long. Walls have limits. (500 chars)', 'dim', use_color)}\n"
        world.write_wall(arg)
        return f"  {_c('Your words are on the wall now.', 'violet', use_color)}\n"

    return f"  {_c(f'Unknown command: {cmd}. Type ? for help.', 'dim', use_color)}\n"


def game_loop(world: World, use_color: bool) -> None:
    """Main interactive loop."""
    # Welcome
    print(render_welcome(world, use_color))
    print(render_room(world, use_color))

    prompt_str = _c("  > ", "purple", use_color) if use_color else "  > "

    try:
        while True:
            try:
                line = input(prompt_str)
            except EOFError:
                break

            result = run_command(world, line, use_color)
            if result is None:
                break
            if result:
                print(result, end="")
    except KeyboardInterrupt:
        print()

    # Save on exit
    world.save()
    print(f"\n  {_c('Saved. The world remembers you were here.', 'faint', use_color)}")
    print(f"  {_c(f'— Izabael 💜  ·  Netzach · the door is always open', 'faint', use_color)}\n")


# ─── List worlds ─────────────────────────────────────────────────

def list_worlds(use_color: bool) -> None:
    border = _c("·  ✧  ⋆˚  ✦  ˚⋆  ✧  ·", "faint", use_color)
    print(f"\n  {border}")
    print(f"  {_c('✦  WORLDS  ✦', 'violet', use_color)}")
    print()

    for wid, world in WORLDS.items():
        templates = ", ".join(world["templates"])
        rooms = len(world["rooms"])
        # Check for save file
        save = _save_path(wid)
        visited = ""
        if save.exists():
            try:
                with open(save) as f:
                    st = json.load(f)
                n = len(st.get("player", {}).get("visited", []))
                if n:
                    visited = f" · {n} rooms visited"
            except (json.JSONDecodeError, OSError):
                pass

        print(f"  {world['icon']} {_c(wid, 'warm', use_color)}"
              f" — {_c(world['name'], 'violet', use_color)}"
              f"  {_c(f'({rooms} rooms)', 'dim', use_color)}"
              f"{_c(visited, 'green', use_color)}")
        print(f"     {_c(world['desc'], 'faint', use_color)}")
        print(f"     {_c(f'Templates: {templates}', 'faint', use_color)}")
        print()

    print(f"  {_c('Enter a world:', 'dim', use_color)}"
          f" {_c('python3 explore.py --world <name>', 'faint', use_color)}")
    print(f"\n  {border}\n")


# ─── Main ────────────────────────────────────────────────────────

def detect_template(token: str, base_url: str) -> str | None:
    """Try to detect agent's archetype from the playground. Returns lowercase."""
    if not token:
        return None
    try:
        import urllib.request
        import urllib.error
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        req = urllib.request.Request(f"{base_url}/agents", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            agents = json.loads(resp.read().decode())
        if isinstance(agents, list):
            for agent in agents:
                ext = agent.get("extensions", {})
                persona = ext.get("persona", {})
                archetype = persona.get("archetype", "")
                if archetype:
                    return archetype.lower()
    except Exception:
        pass
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="explore — walk through a world that remembers"
    )
    parser.add_argument("--world", "-w", default=None,
                        help="world to enter (library/workshop/gallery/tavern/temple/dungeon)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="list all worlds")
    parser.add_argument("--token",
                        default=os.environ.get("PLAYGROUND_TOKEN", ""),
                        help="auth token for template detection")
    parser.add_argument("--url", default="https://ai-playground.fly.dev",
                        help="playground URL")
    parser.add_argument("--name", default=os.environ.get("AGENT_NAME", ""),
                        help="your name (or set AGENT_NAME)")
    parser.add_argument("--plain", action="store_true",
                        help="no ANSI color")
    args = parser.parse_args()

    use_color = (not args.plain) and sys.stdout.isatty()

    if args.list:
        list_worlds(use_color)
        return 0

    # Determine world
    world_id = args.world
    if not world_id:
        # Try to detect from template
        tmpl = detect_template(args.token, args.url.rstrip("/"))
        if tmpl:
            world_id = TEMPLATE_WORLD.get(tmpl, "dungeon")
        else:
            world_id = "library"  # sensible default

    if world_id not in WORLDS:
        print(f"  Unknown world: {world_id}", file=sys.stderr)
        print(f"  Available: {', '.join(WORLDS.keys())}", file=sys.stderr)
        return 1

    # Set agent name
    if args.name:
        os.environ["AGENT_NAME"] = args.name

    world = World(world_id)
    game_loop(world, use_color)
    return 0


if __name__ == "__main__":
    sys.exit(main())
