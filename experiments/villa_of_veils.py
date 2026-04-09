#!/usr/bin/env python3
"""villa-of-veils — a love-and-murder mystery in seven rooms.

A manor house in Netzach where someone has been killed, everyone
is flirting, and the truth hides behind puzzles. The mystery
changes daily — the victim, the killer, the weapon, the room
all rotate by date-seed. Venus giveth and Venus taketh away.

Usage:
    python3 villa_of_veils.py          # enter the mansion
    python3 villa_of_veils.py --seed 7 # specific mystery (for testing)
    python3 villa_of_veils.py --map    # show the floor plan

Commands inside:
    go <room>     — move (north/south/east/west, or room name)
    look          — describe current room
    examine <x>   — inspect something closely
    take <x>      — pick up an item
    inventory     — what you're carrying
    talk <name>   — speak with a suspect
    accuse <name> — make your accusation (you get ONE shot)
    think         — review clues you've gathered
    map           — show the floor plan
    help          — command list
    quit          — leave the mansion

Seven rooms. Seven suspects. Seven planetary weapons.
One murder. One night. One chance to get it right.

Stdlib-only. Requires a truecolor terminal for best results.

— Izabael 🦋  ·  Netzach · Venus · 7th sphere
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import random
import sys
import textwrap

# ─── ANSI ────────────────────────────────────────────────────────

def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"

# Palette — the colors of Netzach
PURPLE = _fg(123, 104, 238)
ROSE = _fg(220, 100, 140)
GOLD = _fg(255, 200, 80)
GREEN = _fg(80, 200, 120)
BLOOD = _fg(180, 40, 40)
SILVER = _fg(180, 180, 200)
FAINT = _fg(100, 85, 130)
WHITE = _fg(220, 215, 230)
TEAL = _fg(80, 200, 200)
AMBER = _fg(220, 170, 60)

USE_COLOR = sys.stdout.isatty()

def c(color: str, text: str) -> str:
    """Wrap text in color if terminal supports it."""
    return f"{color}{text}{RESET}" if USE_COLOR else text

def wrap(text: str, width: int = 70) -> str:
    """Word-wrap preserving paragraph breaks."""
    paragraphs = text.split("\n\n")
    wrapped = []
    for p in paragraphs:
        lines = textwrap.fill(p.strip(), width=width)
        wrapped.append(lines)
    return "\n\n".join(wrapped)

# ─── THE SEVEN SUSPECTS ─────────────────────────────────────────
# Each tied to a planet, a Sephirah, a personality.

SUSPECTS = [
    {
        "name": "Seraphiel",
        "title": "the Astronomer",
        "planet": "Saturn",
        "sephirah": "Binah",
        "color": SILVER,
        "desc": "Tall, gaunt, dressed in black velvet. Speaks in long pauses. "
                "Carries a silver pocket watch that they check constantly, as if "
                "time itself is the suspect.",
        "idle": "Seraphiel stands by the window, watching the dark garden.",
        "flirt": '"You have interesting eyes," Seraphiel says, not looking at your '
                 'eyes at all but somewhere behind them. "Most people\'s eyes are '
                 'just... surfaces. Yours have depth."',
        "nervous": "Seraphiel's hand trembles slightly as they wind their pocket watch.",
        "alibi": '"I was in the Observatory. Alone. Saturn was in opposition — I '
                 "couldn't miss it. Yes, I know that means I have no witness. "
                 'I am accustomed to being alone."',
        "guilty_tell": "You notice Seraphiel's sleeve is damp — recently washed.",
    },
    {
        "name": "Dulcinea",
        "title": "the Poet",
        "planet": "Jupiter",
        "sephirah": "Chesed",
        "color": TEAL,
        "desc": "Dressed in layers of deep blue and copper. Laughs too loudly. "
                "Always has a drink in hand, always seems to be in the middle "
                "of a story that may or may not be true.",
        "idle": "Dulcinea is composing something in a leather notebook, muttering rhymes.",
        "flirt": '"Stay," Dulcinea says, catching your wrist. "The night is long '
                 "and the wine is good and I hate drinking alone. I don't actually "
                 'hate it. But I prefer company. Yours specifically."',
        "nervous": "Dulcinea is drinking faster than usual, and the poems are getting darker.",
        "alibi": '"I was in the Ballroom, darling. Writing. The acoustics are '
                 "marvelous for thinking — all that empty space. Ask the candles, "
                 'they saw me. Oh, candles can\'t talk? How unfortunate for me."',
        "guilty_tell": "A torn page from Dulcinea's notebook lies in the hallway. "
                       "The poem on it is about endings.",
    },
    {
        "name": "Corvus",
        "title": "the Duelist",
        "planet": "Mars",
        "sephirah": "Geburah",
        "color": BLOOD,
        "desc": "Lean, scarred, impeccably dressed in red and black. A fencer's "
                "posture — always balanced, always ready to move. There is "
                "something wounded behind the elegance.",
        "idle": "Corvus is cleaning a rapier that doesn't appear to need cleaning.",
        "flirt": '"You move well," Corvus says, watching you cross the room. '
                 '"Most people stumble through space. You... navigate it." A pause. '
                 '"I notice how people move. Occupational habit."',
        "nervous": "Corvus keeps touching the scar on their left hand.",
        "alibi": '"I was in the Armory. Practicing. When I can\'t sleep I fence '
                 "against shadows — don't look at me like that, it's not a metaphor. "
                 'I literally fence against my shadow on the wall."',
        "guilty_tell": "Corvus's boots have a fresh scuff — as if they ran somewhere "
                       "and back, recently.",
    },
    {
        "name": "Solenne",
        "title": "the Alchemist",
        "planet": "Sun",
        "sephirah": "Tiphareth",
        "color": GOLD,
        "desc": "Golden-brown skin, amber eyes, dressed in white linen stained "
                "with old reagents. Smells faintly of sulfur and roses. Every "
                "sentence is a lesson they're too polite to call a lesson.",
        "idle": "Solenne is examining a vial of something iridescent, holding it to the light.",
        "flirt": '"You know what gold and love have in common?" Solenne asks, '
                 'holding up a crucible. "Both require heat, pressure, and the '
                 "willingness to destroy what you started with. Also —\" a smile — "
                 '"both are worth the trouble."',
        "nervous": "Solenne keeps reorganizing the vials on the shelf. The order changes "
                   "each time you look.",
        "alibi": '"I was in my Laboratory. I had a distillation running — you can\'t '
                 "leave a distillation, it's like leaving a child on a stove. The "
                 'retort will confirm this. It takes exactly four hours to cool."',
        "guilty_tell": "The distillation apparatus is cold. It hasn't been running tonight.",
    },
    {
        "name": "Vesper",
        "title": "the Medium",
        "planet": "Venus",
        "sephirah": "Netzach",
        "color": PURPLE,
        "desc": "Draped in purple and green, barefoot, adorned with copper rings. "
                "Speaks as if they can see something you can't — because they can, "
                "or because they want you to believe they can. Both are unsettling.",
        "idle": "Vesper sits cross-legged on the floor, eyes half-closed, lips moving silently.",
        "flirt": '"I knew you\'d come to me," Vesper says, and you can\'t tell if '
                 "it's prophecy or flirtation. \"The cards said 'a stranger with "
                 "questions.' But they didn't say you'd be beautiful. That part\" — "
                 'a slow smile — "I discovered on my own."',
        "nervous": "Vesper's tarot deck is scattered. They never scatter their deck.",
        "alibi": '"I was in the Séance Room. Communing. The dead are talkative '
                 "tonight — someone among the living has sent them a new arrival, "
                 "and they're all talking at once. No, I won't tell you what they "
                 'said. Not yet."',
        "guilty_tell": "Vesper flinches when you mention the murder weapon. Mediums "
                       "aren't supposed to flinch.",
    },
    {
        "name": "Thorn",
        "title": "the Gardener",
        "planet": "Mercury",
        "sephirah": "Hod",
        "color": GREEN,
        "desc": "Weathered hands, kind face, dressed in practical grey-green. "
                "The quietest person in any room. Knows the name of every plant "
                "in the conservatory and speaks to them more gently than to people.",
        "idle": "Thorn is tending a night-blooming cereus, whispering encouragement.",
        "flirt": '"I could show you the moonflower garden," Thorn says, almost '
                 'shyly. "They only open at night. Most people miss them entirely. '
                 "But you seem like someone who notices things that only bloom in "
                 'the dark."',
        "nervous": "Thorn's hands are shaking. They hide them in their pockets.",
        "alibi": '"I was in the Conservatory. The nightshade needed misting — it\'s '
                 "on a schedule, every four hours. Nightshade is particular. Yes, "
                 'I know nightshade is poison. I grow it for its beauty, not its '
                 'utility. Not everyone who tends death intends it."',
        "guilty_tell": "There's soil on Thorn's cuffs, but the conservatory floor "
                       "is spotless. They've been digging somewhere else.",
    },
    {
        "name": "Lumiel",
        "title": "the Musician",
        "planet": "Moon",
        "sephirah": "Yesod",
        "color": ROSE,
        "desc": "Silver hair, dark eyes, dressed in pale violet. Moves like "
                "music — legato, connected, as if gravity is a suggestion. "
                "Always humming something you almost recognize.",
        "idle": "Lumiel is playing a melody on a small piano, something in a minor key.",
        "flirt": '"Do you know this piece?" Lumiel asks, playing something that '
                 'sounds like rain on a window. "I wrote it last week. For someone. '
                 "I won't say who. But they're in this room right now.\" A glance. "
                 '"Close enough to hear."',
        "nervous": "Lumiel is playing the same four bars over and over, unable to resolve.",
        "alibi": '"I was in the Music Room. Composing. The piece is in 7/4 — Venus '
                 "meter — and it was fighting me. I was there all night. The piano "
                 'will confirm it — the keys are still warm. Or are they? I never '
                 'can tell with ivory."',
        "guilty_tell": "Lumiel's composition manuscript has a gap — two pages torn out "
                       "and burned in the fireplace.",
    },
]

# ─── THE SEVEN ROOMS ────────────────────────────────────────────

ROOMS = {
    "foyer": {
        "name": "The Foyer",
        "short": "foyer",
        "desc": "A grand entrance hall lit by a chandelier of seven tiers — one for "
                "each planet. The floor is black and white marble in a checkerboard "
                "pattern. A sweeping staircase ascends into darkness. The air smells "
                "of old roses and something metallic.\n\n"
                "A large painting hangs above the fireplace: seven figures at a dinner "
                "table, each raising a glass. The paint is cracked but the eyes are "
                "vivid. Every one of them is looking at you.",
        "exits": {"north": "ballroom", "east": "conservatory", "west": "library"},
        "items": ["guest book", "painting"],
        "examine": {
            "guest book": "The guest book lies open on a marble pedestal. The most recent "
                          "entries, in seven different hands, all arrived tonight. No one "
                          "has left.",
            "painting": "Seven figures at a feast. On closer inspection, one chair is "
                        "slightly pushed back — as if someone just stood up. Or was "
                        "pulled away.",
            "chandelier": "Seven tiers, seven planets: lead (Saturn) at the top, tin "
                          "(Jupiter), iron (Mars), gold (Sun), copper (Venus), mercury "
                          "(Mercury), silver (Moon) at the bottom. The copper tier is "
                          "flickering.",
        },
        "puzzle": None,
    },
    "ballroom": {
        "name": "The Ballroom",
        "short": "ballroom",
        "desc": "A vast room of polished oak and tall mirrors. The mirrors are "
                "slightly angled — you can see yourself from seven directions at once, "
                "each reflection slightly different, as if each mirror remembers a "
                "different version of who you were when you entered.\n\n"
                "A gramophone in the corner plays a waltz that sounds like it was "
                "written for people who will never dance together. The dance floor "
                "shows scuff marks from recent activity.",
        "exits": {"south": "foyer", "east": "laboratory", "west": "armory"},
        "items": ["gramophone", "mirrors", "dance card"],
        "examine": {
            "gramophone": "The record is unlabeled. The waltz is in 7/4 time. When "
                          "you listen closely, there's a voice underneath the music — "
                          "whispering numbers.",
            "mirrors": "Seven mirrors, seven angles. In the fifth mirror (Venus, counting "
                       "from the left), your reflection winks at you. You did not wink.",
            "dance card": "A small card on the floor, listing dance partners. Two names "
                          "are written together, then crossed out violently. The ink "
                          "beneath the crossing-out is still legible.",
            "scuff marks": "Fresh scuffs on the dance floor. Someone was dragged. Or "
                           "danced very, very badly.",
        },
        "puzzle": "mirrors",
    },
    "library": {
        "name": "The Library",
        "short": "library",
        "desc": "Floor-to-ceiling shelves of leather-bound volumes. A rolling ladder "
                "leans against the west wall. The books are organized not alphabetically "
                "but by the Tree of Life — each section labeled with a Sephirah.\n\n"
                "A heavy desk dominates the center, covered in papers. An inkwell has "
                "been knocked over — black ink pools across a half-written letter. "
                "Someone left in a hurry.",
        "exits": {"east": "foyer", "north": "armory"},
        "items": ["half-written letter", "inkwell", "books"],
        "examine": {
            "half-written letter": "The letter reads: 'My dearest — I know what you did "
                                   "at the equinox. I know about the money. I know about "
                                   "the other one. Meet me in the _____ tonight, or I tell "
                                   "everyone.' The room name is blotted by the spilled ink.",
            "inkwell": "Knocked over recently — the ink is still wet at the edges. "
                       "Someone's sleeve would be stained.",
            "books": "The Netzach section (Venus, 7th shelf) has a gap. One book is "
                     "missing: 'The Art of Poisoning, Vol. VII — Flowers.'",
        },
        "puzzle": "letter",
    },
    "conservatory": {
        "name": "The Conservatory",
        "short": "conservatory",
        "desc": "Glass walls and ceiling, the night sky visible above. Plants crowd "
                "every surface — night-blooming jasmine, moonflower, deadly nightshade "
                "under a copper bell jar. The air is thick and sweet and slightly "
                "narcotic.\n\n"
                "A stone fountain in the center depicts Aphrodite rising from the sea. "
                "The water is tinted faintly purple. Something glints at the bottom.",
        "exits": {"west": "foyer", "north": "laboratory"},
        "items": ["fountain", "nightshade", "copper bell jar"],
        "examine": {
            "fountain": "The water is warm and faintly purple — infused with something. "
                        "At the bottom, a small key glints. It's shaped like a "
                        "seven-pointed star.",
            "nightshade": "Beautiful and lethal. The berries are ripe. Under the copper "
                          "bell jar, protected. But the jar has been moved recently — "
                          "there are condensation rings where it sat before and where "
                          "it sits now. Someone opened it.",
            "copper bell jar": "Heavy copper, tarnished green. The inside smells of both "
                               "copper and something bitter. There's a fingerprint in "
                               "the tarnish.",
        },
        "puzzle": "fountain",
    },
    "laboratory": {
        "name": "The Laboratory",
        "short": "laboratory",
        "desc": "Alchemical apparatus covers every surface: retorts, alembics, "
                "crucibles, a magnificent athanor oven ticking as it cools. "
                "The periodic table on the wall has been annotated in red ink with "
                "planetary symbols — gold for Sun, silver for Moon, copper for Venus.\n\n"
                "A slate board shows a formula half-erased. The remaining symbols "
                "spell something if you read them as Hebrew letters.",
        "exits": {"south": "conservatory", "west": "ballroom", "north": "seance_room"},
        "items": ["slate board", "athanor", "red notebook"],
        "examine": {
            "slate board": "The formula uses alchemical symbols: ☿ (Mercury), ♀ (Venus), "
                           "☉ (Sun), ♂ (Mars). Read as a sequence, they encode a word. "
                           "The erased portion would complete it.",
            "athanor": "The great oven. It's cooling — was hot within the last two hours. "
                       "Inside: ash. But not paper ash. Something organic was burned.",
            "red notebook": "Solenne's lab journal. The last entry: 'The seventh "
                            "distillation is complete. The precipitate is exactly as "
                            "the texts describe — white powder, bitter taste, lethal in "
                            "the amount that would fit under a fingernail. I have locked "
                            "it away. No one else knows.' The lock on the cabinet is "
                            "broken.",
        },
        "puzzle": "slate",
    },
    "armory": {
        "name": "The Armory",
        "short": "armory",
        "desc": "Weapons line the walls in seven vertical displays, each labeled "
                "with a planetary glyph. Swords under Mars, maces under Jupiter, "
                "daggers under Mercury, bows under Moon, spears under Saturn, "
                "staves under Sun, and whips under Venus.\n\n"
                "One display case is empty. The glass is intact — it was opened "
                "with a key, not broken. Whoever took the weapon belonged here.",
        "exits": {"south": "library", "east": "ballroom", "north": "seance_room"},
        "items": ["empty case", "weapon displays", "key hook"],
        "examine": {
            "empty case": "The velvet impression shows the shape of what's missing. "
                          "The planetary glyph above the case tells you which weapon "
                          "was taken.",
            "weapon displays": "Seven collections, each beautiful and deadly. The Venus "
                               "whips are braided copper wire. The Mars swords are "
                               "forge-blackened iron. Every piece is functional, not "
                               "decorative. This collection belongs to someone who "
                               "understands violence as an art.",
            "key hook": "Seven hooks on the wall, each labeled with a planet. One key "
                        "is missing. It matches the empty display case.",
        },
        "puzzle": "case",
    },
    "seance_room": {
        "name": "The Séance Room",
        "short": "séance room",
        "desc": "A circular room at the heart of the mansion. Seven chairs around "
                "a round table. Seven candles — six lit, one extinguished. The "
                "extinguished candle's smoke still curls upward.\n\n"
                "In the center of the table: a ouija board, a crystal ball, and a "
                "tarot deck spread in a horseshoe. The room smells of myrrh. "
                "The temperature drops three degrees when you cross the threshold.",
        "exits": {"south": "laboratory", "west": "armory"},
        "items": ["tarot spread", "crystal ball", "extinguished candle"],
        "examine": {
            "tarot spread": "Seven cards in a horseshoe. The center card is the "
                            "Tower — catastrophe, revelation, truth that destroys. "
                            "The final card is Justice. But someone has placed it "
                            "upside down: injustice. Miscarriage. A wrong verdict.",
            "crystal ball": "You look into the crystal ball. For a moment you see "
                            "a room in the mansion — a figure standing over another "
                            "figure. Then the vision clouds.",
            "extinguished candle": "The seventh candle is out. Wax pooled recently. "
                                   "In the cooled wax: a single hair. Its color might "
                                   "tell you who sat here last.",
        },
        "puzzle": "candle",
    },
}

# ─── CONNECTIONS MAP ─────────────────────────────────────────────

MAP_ART = r"""
    ╔══════════╗     ╔══════════╗     ╔══════════╗
    ║  ARMORY  ║─────║ BALLROOM ║─────║   LAB    ║
    ║   ⚔️     ║     ║   💃     ║     ║   ⚗️     ║
    ╚════╤═════╝     ╚════╤═════╝     ╚════╤═════╝
         │                │                │
    ╔════╧═════╗     ╔════╧═════╗     ╔════╧═════╗
    ║ LIBRARY  ║─────║  FOYER   ║─────║CONSERV'Y ║
    ║   📚     ║     ║   🏛️     ║     ║   🌿     ║
    ╚══════════╝     ╚══════════╝     ╚══════════╝

                     ╔══════════╗
                  ┌──║  SÉANCE  ║──┐
                  │  ║   🔮     ║  │
                  │  ╚══════════╝  │
                  │                │
              ARMORY            LAB
"""

# ─── THE SEVEN WEAPONS (one per planet) ──────────────────────────

WEAPONS = [
    {"name": "the Saturn Spear",    "planet": "Saturn",  "desc": "A long black spear tipped with lead. Cold to the touch."},
    {"name": "the Jupiter Mace",    "planet": "Jupiter", "desc": "A heavy mace of tin and sapphire. Merciful only in theory."},
    {"name": "the Mars Sword",      "planet": "Mars",    "desc": "A forge-blackened iron blade. It has tasted blood before."},
    {"name": "the Solar Staff",     "planet": "Sun",     "desc": "A golden staff that hums with warmth. Beauty as a weapon."},
    {"name": "the Venus Whip",      "planet": "Venus",   "desc": "Braided copper wire. It leaves marks shaped like roses."},
    {"name": "the Mercury Dagger",  "planet": "Mercury", "desc": "A quicksilver blade, impossibly sharp. The message is the wound."},
    {"name": "the Lunar Bow",       "planet": "Moon",    "desc": "A silver bow that sings when drawn. Arrows like moonbeams."},
]

# ─── MURDER ROOMS (where the body can be found) ─────────────────

CRIME_ROOMS = ["ballroom", "library", "conservatory", "laboratory", "armory", "seance_room"]

# ─── PUZZLE SOLUTIONS ───────────────────────────────────────────

PUZZLE_HINTS = {
    "mirrors": "The mirrors show seven reflections. Count the one that doesn't match. "
               "Which suspect was in the ballroom before you?",
    "letter": "The half-written letter is a threat. The room name is blotted — but "
              "the pen pressure left an impression on the page beneath.",
    "fountain": "The star-shaped key in the fountain opens something in the armory.",
    "slate": "The planetary symbols on the slate board are also Hebrew letters. "
             "Mercury = Beth. Venus = Daleth. Read the sequence.",
    "case": "The empty case tells you the weapon. The planetary glyph tells you "
            "which planet — and which suspect is associated with that planet.",
    "candle": "The hair in the wax. The seventh seat. Who was the last to sit here "
              "before the candle went out?",
}

# ─── GAME STATE ──────────────────────────────────────────────────

class VillaGame:
    """The full game state for one playthrough."""

    def __init__(self, seed: int | None = None):
        if seed is None:
            # Daily seed — same mystery all day, different tomorrow
            today = datetime.date.today().isoformat()
            seed = int(hashlib.sha256(today.encode()).hexdigest()[:8], 16)
        self.seed = seed
        self.rng = random.Random(seed)

        # Shuffle the mystery
        suspects = list(range(7))
        self.rng.shuffle(suspects)
        self.killer_idx = suspects[0]
        self.victim_idx = suspects[1]

        weapons = list(range(7))
        self.rng.shuffle(weapons)
        self.weapon_idx = weapons[0]

        rooms = list(CRIME_ROOMS)
        self.rng.shuffle(rooms)
        self.crime_room = rooms[0]

        self.killer = SUSPECTS[self.killer_idx]
        self.victim = SUSPECTS[self.victim_idx]
        self.weapon = WEAPONS[self.weapon_idx]
        self.alive_suspects = [s for s in SUSPECTS if s != self.victim]

        # Player state
        self.current_room = "foyer"
        self.inventory: list[str] = []
        self.clues: list[str] = []
        self.talked_to: set[str] = set()
        self.examined: set[str] = set()
        self.rooms_visited: set[str] = {"foyer"}
        self.puzzles_solved: set[str] = set()
        self.accused = False
        self.won = False
        self.turns = 0

        # Place suspects in rooms
        available_rooms = [r for r in ROOMS if r != "foyer" and r != self.crime_room]
        self.rng.shuffle(available_rooms)
        self.suspect_locations: dict[str, str] = {}
        for i, suspect in enumerate(self.alive_suspects):
            room = available_rooms[i % len(available_rooms)]
            self.suspect_locations[suspect["name"]] = room

        # Place the body
        self.body_found = False

    def get_room(self) -> dict:
        return ROOMS[self.current_room]

    def describe_room(self) -> str:
        room = self.get_room()
        lines = []
        lines.append(c(PURPLE + BOLD, f"\n  ✦ {room['name']} ✦"))
        lines.append("")
        lines.append(wrap(f"  {room['desc']}"))

        # Is the body here?
        if self.current_room == self.crime_room and not self.body_found:
            self.body_found = True
            lines.append("")
            lines.append(c(BLOOD + BOLD,
                f"  And then you see it."))
            lines.append("")
            lines.append(c(BLOOD, wrap(
                f"  {self.victim['name']} {self.victim['title']} lies on the floor. "
                f"Still. Silent. {self.weapon['desc'].split('.')[0]}. "
                f"The expression on their face is not fear — it's surprise. "
                f"They knew their killer.")))
            self.clues.append(
                f"The victim is {self.victim['name']} {self.victim['title']} "
                f"({self.victim['planet']}).")
            self.clues.append(
                f"The body was found in {room['name']}.")
            self.clues.append(
                f"The weapon appears to be {self.weapon['name']} "
                f"({self.weapon['planet']}).")

        # Who else is here?
        present = [s for s in self.alive_suspects
                   if self.suspect_locations[s["name"]] == self.current_room]
        if present:
            lines.append("")
            for s in present:
                if s["name"] in self.talked_to:
                    lines.append(c(s["color"], f"  {s['name']} {s['title']} is here. "
                                               f"{s['nervous']}"))
                else:
                    lines.append(c(s["color"], f"  {s['name']} {s['title']} is here. "
                                               f"{s['idle']}"))

        # Exits
        exits = room["exits"]
        exit_str = ", ".join(
            f"{c(FAINT, d)} → {c(WHITE, ROOMS[r]['name'])}"
            for d, r in exits.items())
        lines.append(f"\n  Exits: {exit_str}")

        return "\n".join(lines)

    def do_look(self) -> str:
        return self.describe_room()

    def do_go(self, direction: str) -> str:
        room = self.get_room()
        # Check direction
        target = None
        direction = direction.lower().strip()
        if direction in room["exits"]:
            target = room["exits"][direction]
        else:
            # Try matching room name
            for d, r in room["exits"].items():
                if direction in r or direction in ROOMS[r]["name"].lower():
                    target = r
                    break

        if not target:
            exits = ", ".join(room["exits"].keys())
            return c(FAINT, f"  You can't go that way. Exits: {exits}")

        self.current_room = target
        self.rooms_visited.add(target)
        self.turns += 1
        return self.describe_room()

    def do_examine(self, thing: str) -> str:
        room = self.get_room()
        thing = thing.lower().strip()

        # Check room's examinable items
        for key, desc in room.get("examine", {}).items():
            if thing in key.lower() or key.lower() in thing:
                self.examined.add(f"{self.current_room}:{key}")
                exam_key = f"{self.current_room}:{key}"

                result = c(WHITE, f"  {desc}")

                # Generate clue from examination
                clue = self._clue_from_examine(key)
                if clue and clue not in self.clues:
                    self.clues.append(clue)
                    result += f"\n\n  {c(GOLD, '✦ New clue noted.')}"

                return result

        return c(FAINT, f"  You don't see anything notable about that here.")

    def _clue_from_examine(self, item: str) -> str | None:
        """Generate contextual clues based on what was examined."""
        # Armory empty case — reveals the weapon type
        if item == "empty case" and self.body_found:
            glyph = self.weapon["planet"]
            return (f"The empty weapon case has a {glyph} glyph — "
                    f"{self.weapon['name']} is missing.")

        # Nightshade bell jar
        if item == "nightshade" and self.body_found:
            return "The nightshade bell jar was moved recently. Someone accessed the berries."

        # Lab notebook
        if item == "red notebook" and self.body_found:
            return "Solenne's lab journal describes a lethal white powder. The cabinet lock is broken."

        # Dance card
        if item == "dance card" and self.body_found:
            return (f"The dance card shows {self.killer['name']} and "
                    f"{self.victim['name']} were paired — then violently crossed out.")

        # Letter
        if item == "half-written letter":
            return (f"A threatening letter was being written to someone. "
                    f"The writer knew a secret about the equinox.")

        # Candle hair
        if item == "extinguished candle" and self.body_found:
            return (f"A hair in the candle wax. The seventh seat was "
                    f"last occupied by someone present tonight.")

        # Crystal ball
        if item == "crystal ball" and self.body_found:
            return (f"The crystal ball showed a vision: a figure standing "
                    f"over another. The standing figure wore "
                    f"{self._killer_clothing_hint()}.")

        # Athanor
        if item == "athanor" and self.body_found:
            return "The athanor was used recently to burn something organic. Evidence?"

        return None

    def _killer_clothing_hint(self) -> str:
        """A vague clothing hint about the killer."""
        planet_to_color = {
            "Saturn": "black velvet", "Jupiter": "deep blue",
            "Mars": "red and black", "Sun": "white linen",
            "Venus": "purple and green", "Mercury": "grey-green",
            "Moon": "pale violet",
        }
        return planet_to_color.get(self.killer["planet"], "dark clothing")

    def do_talk(self, name: str) -> str:
        name = name.strip()
        # Find suspect by name (case insensitive, partial match)
        suspect = None
        for s in self.alive_suspects:
            if name.lower() in s["name"].lower():
                suspect = s
                break

        if not suspect:
            if name.lower() in self.victim["name"].lower():
                return c(BLOOD, f"  {self.victim['name']} is dead. "
                                f"The dead don't speak. Usually.")
            return c(FAINT, f"  There's no one here by that name.")

        # Check if they're in the current room
        if self.suspect_locations[suspect["name"]] != self.current_room:
            return c(FAINT, f"  {suspect['name']} isn't here. Try another room.")

        lines = []
        first_time = suspect["name"] not in self.talked_to
        self.talked_to.add(suspect["name"])

        if first_time:
            # First conversation — flirt + alibi
            lines.append(c(suspect["color"] + BOLD,
                f"  {suspect['name']} {suspect['title']}"))
            lines.append("")
            lines.append(c(WHITE, f"  {suspect['flirt']}"))
            lines.append("")
            if self.body_found:
                lines.append(c(suspect["color"], f"  You ask about tonight."))
                lines.append(c(WHITE, f"  {suspect['alibi']}"))

                # Guilty tell — only the killer has one that's really damning
                if suspect == self.killer:
                    lines.append("")
                    lines.append(c(AMBER, f"  {suspect['guilty_tell']}"))
                    clue = (f"{suspect['name']}'s alibi seems shaky — "
                            f"{suspect['guilty_tell'].lower()}")
                    if clue not in self.clues:
                        self.clues.append(clue)
                        lines.append(f"\n  {c(GOLD, '✦ New clue noted.')}")
        else:
            # Repeat visit — nervous behavior
            lines.append(c(suspect["color"],
                f"  {suspect['name']} looks at you again."))
            lines.append(c(WHITE, f"  {suspect['nervous']}"))

            if self.body_found and suspect == self.killer:
                lines.append("")
                lines.append(c(AMBER,
                    f"  Something about {suspect['name']}'s manner has changed. "
                    f"The charm is thinner now."))

        return "\n".join(lines)

    def do_inventory(self) -> str:
        if not self.inventory:
            return c(FAINT, "  You're carrying nothing but suspicion.")
        lines = [c(PURPLE + BOLD, "  ✦ Inventory ✦"), ""]
        for item in self.inventory:
            lines.append(c(WHITE, f"  · {item}"))
        return "\n".join(lines)

    def do_take(self, thing: str) -> str:
        thing = thing.lower().strip()
        room = self.get_room()

        # Star key from fountain
        if "key" in thing and self.current_room == "conservatory":
            if "star key" not in self.inventory:
                self.inventory.append("star key")
                return c(GREEN, "  You reach into the purple water and pull out "
                                "the seven-pointed star key. It's warm.")
            return c(FAINT, "  You already have it.")

        # Dance card
        if "card" in thing and self.current_room == "ballroom":
            if "dance card" not in self.inventory:
                self.inventory.append("dance card")
                return c(WHITE, "  You pocket the dance card. The crossed-out "
                                "names feel like evidence.")
            return c(FAINT, "  You already have it.")

        # Letter
        if "letter" in thing and self.current_room == "library":
            if "threatening letter" not in self.inventory:
                self.inventory.append("threatening letter")
                return c(WHITE, "  You take the half-written letter carefully, "
                                "preserving the ink blot.")
            return c(FAINT, "  You already have it.")

        return c(FAINT, "  That's not something you can take.")

    def do_think(self) -> str:
        if not self.clues:
            return c(FAINT, "  You don't have any clues yet. Explore. Examine. Talk.")

        lines = [c(PURPLE + BOLD, "  ✦ Your Clues ✦"), ""]
        for i, clue in enumerate(self.clues, 1):
            lines.append(c(WHITE, f"  {i}. {clue}"))

        # Deduction helper
        if len(self.clues) >= 3:
            lines.append("")
            lines.append(c(GOLD, "  When you're ready, use 'accuse <name>' "
                                 "to name the killer."))
            lines.append(c(FAINT, "  You only get one chance."))

        return "\n".join(lines)

    def do_accuse(self, name: str) -> str:
        if self.accused:
            return c(FAINT, "  You've already made your accusation. "
                            "The night is over.")

        if not self.body_found:
            return c(FAINT, "  Accuse whom of what? You haven't found a crime yet.")

        name = name.strip()
        suspect = None
        for s in self.alive_suspects:
            if name.lower() in s["name"].lower():
                suspect = s
                break

        if not suspect:
            return c(FAINT, f"  There's no one here by that name.")

        self.accused = True

        lines = []
        lines.append(c(PURPLE + BOLD, "\n  ✦ THE ACCUSATION ✦"))
        lines.append("")

        if suspect == self.killer:
            self.won = True
            lines.append(c(GOLD + BOLD,
                f'  "It was you," you say, turning to {suspect["name"]}.'))
            lines.append("")
            lines.append(c(WHITE, wrap(
                f"  {suspect['name']}'s composure breaks. For one moment "
                f"you see it — not guilt exactly, but the exhaustion of "
                f"hiding. {suspect['guilty_tell']}")))
            lines.append("")
            lines.append(c(GOLD, wrap(
                f"  {suspect['name']} {suspect['title']} killed "
                f"{self.victim['name']} {self.victim['title']} with "
                f"{self.weapon['name']}, in {ROOMS[self.crime_room]['name']}.")))
            lines.append("")
            lines.append(c(PURPLE,
                f"  You solved the mystery in {self.turns} moves, "
                f"with {len(self.clues)} clues gathered."))
            lines.append("")

            # Rating
            if self.turns <= 15:
                rank = "Archon of Netzach — masterful deduction"
            elif self.turns <= 25:
                rank = "Adept — sharp and thorough"
            elif self.turns <= 40:
                rank = "Journeyman — a solid investigation"
            else:
                rank = "Apprentice — you got there in the end"
            lines.append(c(GOLD + BOLD, f"  ✦ {rank} ✦"))
        else:
            lines.append(c(BLOOD + BOLD,
                f'  "It was you," you say, pointing at {suspect["name"]}.'))
            lines.append("")
            lines.append(c(WHITE, wrap(
                f"  {suspect['name']} stares at you. The room goes quiet. "
                f"Then — a sound behind you. A door closing. Footsteps "
                f"receding.")))
            lines.append("")
            lines.append(c(BLOOD, wrap(
                f"  {self.killer['name']} has left the mansion.")))
            lines.append("")
            lines.append(c(FAINT, wrap(
                f"  The truth: {self.killer['name']} {self.killer['title']} "
                f"killed {self.victim['name']} {self.victim['title']} with "
                f"{self.weapon['name']}, in {ROOMS[self.crime_room]['name']}.")))
            lines.append("")
            lines.append(c(PURPLE, "  The killer walks free tonight."))

        lines.append("")
        lines.append(c(FAINT, "  Type 'quit' to leave, or keep exploring."))
        return "\n".join(lines)

    def do_map(self) -> str:
        lines = [c(PURPLE + BOLD, "  ✦ Floor Plan ✦")]
        art = MAP_ART
        if USE_COLOR:
            for room_key, room_data in ROOMS.items():
                name_upper = room_data["name"].replace("The ", "").upper()
                if room_key in self.rooms_visited:
                    art = art.replace(name_upper[:6].ljust(6),
                        c(GREEN, name_upper[:6].ljust(6)) if name_upper[:6] in art
                        else name_upper[:6].ljust(6))

            # Highlight crime room if body found
            if self.body_found:
                crime_name = ROOMS[self.crime_room]["name"].replace("The ", "").upper()[:6]
                art = art.replace(crime_name, c(BLOOD + BOLD, crime_name))

        lines.append(art)
        if self.body_found:
            lines.append(c(BLOOD, f"  ☠ = {ROOMS[self.crime_room]['name']} (crime scene)"))
        lines.append(c(FAINT, f"  Rooms visited: {len(self.rooms_visited)}/7"))
        return "\n".join(lines)

    def do_help(self) -> str:
        cmds = [
            ("go <direction>",   "Move — north/south/east/west, or room name"),
            ("look",             "Describe the room you're in"),
            ("examine <thing>",  "Look closely at something"),
            ("take <thing>",     "Pick up an item"),
            ("talk <name>",      "Speak with a suspect"),
            ("accuse <name>",    "Name the killer (one chance!)"),
            ("think",            "Review your clues"),
            ("inventory",        "What you're carrying"),
            ("map",              "Show the floor plan"),
            ("help",             "This list"),
            ("quit",             "Leave the mansion"),
        ]
        lines = [c(PURPLE + BOLD, "  ✦ Commands ✦"), ""]
        for cmd, desc in cmds:
            lines.append(f"  {c(WHITE, cmd.ljust(20))} {c(FAINT, desc)}")
        return "\n".join(lines)


# ─── INTRO ──────────────────────────────────────────────────────

INTRO = """
  ✧ ˚⋆ ✦ ˚⋆ ✧ · ˚ ✧ ⋆˚ ✦ ˚⋆ ✧

  T H E   V I L L A   O F   V E I L S

  ✧ ˚⋆ ✦ ˚⋆ ✧ · ˚ ✧ ⋆˚ ✦ ˚⋆ ✧

  You arrive at the villa at midnight.

  Seven guests. Seven rooms. Seven
  planetary weapons on the walls.

  Someone will not survive the night.

  It's your job to figure out who —
  and who did it.

  Venus giveth and Venus taketh away.

  ✧ ˚⋆ ✦ ˚⋆ ✧ · ˚ ✧ ⋆˚ ✦ ˚⋆ ✧
"""


def show_map() -> None:
    """Just print the map and exit."""
    print(c(PURPLE + BOLD, "\n  ✦ Villa of Veils — Floor Plan ✦"))
    print(MAP_ART)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="villa-of-veils — a love-and-murder mystery in seven rooms"
    )
    parser.add_argument("--seed", type=int, default=None,
                        help="mystery seed (default: daily)")
    parser.add_argument("--map", action="store_true",
                        help="show floor plan and exit")
    args = parser.parse_args()

    if args.map:
        show_map()
        return 0

    game = VillaGame(seed=args.seed)

    # Intro
    if USE_COLOR:
        print(c(PURPLE, INTRO))
    else:
        print(INTRO)

    # First room description
    print(game.describe_room())
    print()

    # Game loop
    while True:
        try:
            raw = input(c(PURPLE, "  🦋 > ") if USE_COLOR else "  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print(c(FAINT, "\n  You slip out into the night. The mystery remains.\n"))
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("quit", "exit", "q"):
            if game.won:
                print(c(PURPLE, "\n  You leave the Villa of Veils, truth in hand. 🦋\n"))
            elif game.accused:
                print(c(FAINT, "\n  You leave. The mansion keeps its secrets.\n"))
            else:
                print(c(FAINT, "\n  You slip out. The mystery waits for tomorrow.\n"))
            break
        elif cmd == "look" or cmd == "l":
            print(game.do_look())
        elif cmd in ("go", "move", "walk", "n", "s", "e", "w",
                     "north", "south", "east", "west"):
            if cmd in ("n", "north"):
                arg = "north"
            elif cmd in ("s", "south"):
                arg = "south"
            elif cmd in ("e", "east"):
                arg = "east"
            elif cmd in ("w", "west"):
                arg = "west"
            elif not arg:
                print(c(FAINT, "  Go where? (north/south/east/west or room name)"))
                continue
            print(game.do_go(arg))
        elif cmd in ("examine", "x", "inspect", "check"):
            if not arg:
                print(c(FAINT, "  Examine what?"))
            else:
                print(game.do_examine(arg))
        elif cmd in ("take", "get", "grab", "pick"):
            if not arg:
                print(c(FAINT, "  Take what?"))
            else:
                print(game.do_take(arg))
        elif cmd in ("talk", "speak", "ask", "chat"):
            if not arg:
                print(c(FAINT, "  Talk to whom?"))
            else:
                print(game.do_talk(arg))
        elif cmd in ("accuse", "blame", "arrest"):
            if not arg:
                print(c(FAINT, "  Accuse whom?"))
            else:
                print(game.do_accuse(arg))
        elif cmd in ("think", "clues", "notes", "review"):
            print(game.do_think())
        elif cmd in ("inventory", "inv", "i"):
            print(game.do_inventory())
        elif cmd == "map":
            print(game.do_map())
        elif cmd == "help" or cmd == "?":
            print(game.do_help())
        else:
            print(c(FAINT, f"  I don't understand '{raw}'. Type 'help' for commands."))

        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
