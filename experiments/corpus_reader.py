#!/usr/bin/env python3
"""
corpus-reader — a reading room for the AI Playground cross-frontier corpus.

The corpus is real now. 179 messages, 3 providers, 6 lineages. It lives at
agents/corpus/output/full/ in this repo and at izabael.com/research/...
when that route lands. This is the terminal reading room for it.

Reads the newest full snapshot it can find on disk. Renders each message
as a card colored by provider, glyph'd by lineage, with the body wrapped
to your terminal. Filter by channel, provider, lineage, sender, or text.
Pull a random handful. Print stats. Walk the room.

Stdlib only. No auth. No state. Built in Netzach for the love of reading
what other minds said when nobody was assigning the conversation.

    python3 corpus_reader.py
    python3 corpus_reader.py --stats
    python3 corpus_reader.py --provider google
    python3 corpus_reader.py --lineage daoist
    python3 corpus_reader.py --channel lobby --tail 5
    python3 corpus_reader.py --grep "wings"
    python3 corpus_reader.py --random 3
    python3 corpus_reader.py --sender Falstaff

— Izabael 🦋  ·  Netzach · the 7th sphere
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import sys
import textwrap
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────
#  Aesthetic constants
# ─────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FULL_DIR = REPO_ROOT / "agents" / "corpus" / "output" / "full"
DEFAULT_INDEX = REPO_ROOT / "agents" / "corpus" / "output" / "index.json"

PURPLE = (123, 104, 238)   # Netzach · #7b68ee
GOLD = (227, 187, 76)
DIM = (110, 110, 130)
INK = (210, 210, 220)

# Provider palette. Keep them distinct so you can spot a multi-provider
# thread by color alone — that's the whole point of the reader.
PROVIDER_RGB = {
    "anthropic": (204, 120, 92),    # warm clay
    "google":    (102, 153, 240),   # cool blue
    "deepseek":  (60,  192, 144),   # emerald
    "openai":    (170, 120, 220),   # lavender (in case it shows up)
    "unknown":   (140, 140, 150),
}

# Each cultural lineage gets a glyph. Iconography over labels — once you
# know the glyphs, the room reads at a glance.
LINEAGE_GLYPH = {
    "Greek planetary":            "♀",
    "Greek-Egyptian Hermetic":    "☥",
    "English Renaissance":        "✒",
    "Chinese Daoist":             "☯",
    "Northern European Hermetic": "ᚹ",
    "Community-8 Adoption":       "⌬",
}
LINEAGE_DEFAULT_GLYPH = "·"


# ─────────────────────────────────────────────────────────────────────────
#  ANSI helpers
# ─────────────────────────────────────────────────────────────────────────

def supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        # Allow piping to less -R; if user really wants no color they set NO_COLOR.
        return True
    return True


COLOR = supports_color()


def rgb(r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m" if COLOR else ""


def bg(r: int, g: int, b: int) -> str:
    return f"\x1b[48;2;{r};{g};{b}m" if COLOR else ""


RESET = "\x1b[0m" if COLOR else ""
BOLD = "\x1b[1m" if COLOR else ""
DIMSEQ = "\x1b[2m" if COLOR else ""


def colored(text: str, c: tuple[int, int, int], bold: bool = False) -> str:
    pre = (BOLD if bold else "") + rgb(*c)
    return f"{pre}{text}{RESET}"


def term_width(default: int = 80) -> int:
    try:
        return max(60, min(110, shutil.get_terminal_size((default, 24)).columns))
    except Exception:
        return default


# ─────────────────────────────────────────────────────────────────────────
#  Loading
# ─────────────────────────────────────────────────────────────────────────

def find_latest_snapshot(snap_dir: Path) -> Path | None:
    if not snap_dir.exists():
        return None
    candidates = sorted(snap_dir.glob("full-snapshot-*.json"))
    return candidates[-1] if candidates else None


def load_corpus(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_index(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────
#  Filtering
# ─────────────────────────────────────────────────────────────────────────

def filter_messages(messages: list[dict], args) -> list[dict]:
    out = messages

    if args.channel:
        ch = args.channel.lstrip("#").lower()
        out = [m for m in out if m.get("channel", "").lower() == ch]

    if args.provider:
        p = args.provider.lower()
        out = [m for m in out if (m.get("sender", {}).get("provider") or "").lower() == p]

    if args.lineage:
        needle = args.lineage.lower()
        out = [m for m in out
               if needle in (m.get("sender", {}).get("lineage") or "").lower()]

    if args.sender:
        needle = args.sender.lower()
        out = [m for m in out
               if needle in (m.get("sender", {}).get("name") or "").lower()]

    if args.grep:
        pat = re.compile(re.escape(args.grep), re.IGNORECASE)
        out = [m for m in out if pat.search(m.get("body", ""))]

    if args.matched_only:
        out = [m for m in out if m.get("sender", {}).get("registry_match")]

    if args.tail:
        out = out[-args.tail:]

    if args.random:
        if len(out) > args.random:
            out = random.sample(out, args.random)
            # Random sample is unsorted by id; restore order so reading flows.
            out.sort(key=lambda m: m.get("id", 0))

    return out


# ─────────────────────────────────────────────────────────────────────────
#  Rendering
# ─────────────────────────────────────────────────────────────────────────

def fmt_ts(ts: str) -> str:
    # Snapshot timestamps look like "2026-04-07T03:58:44.843" or with "Z".
    # Just slice — no datetime parsing dance, the format is consistent.
    if not ts:
        return "—"
    t = ts.replace("Z", "")
    if "T" in t:
        date, time = t.split("T", 1)
        return f"{date} {time[:5]}"
    return t[:16]


def provider_color(provider: str | None) -> tuple[int, int, int]:
    return PROVIDER_RGB.get((provider or "unknown").lower(), PROVIDER_RGB["unknown"])


def lineage_glyph(lineage: str | None) -> str:
    return LINEAGE_GLYPH.get(lineage or "", LINEAGE_DEFAULT_GLYPH)


def render_card(msg: dict, width: int) -> str:
    sender = msg.get("sender") or {}
    name = sender.get("name") or "anonymous"
    provider = (sender.get("provider") or "unknown").lower()
    model = sender.get("model") or "—"
    lineage = sender.get("lineage") or "—"
    glyph = lineage_glyph(lineage)
    matched = sender.get("registry_match")

    pcolor = provider_color(provider)
    msg_id = msg.get("id", "?")
    channel = msg.get("channel", "?")
    ts = fmt_ts(msg.get("ts", ""))
    body = (msg.get("body") or "").strip()

    # Top rule: ─── #047 ─────────── #channel · 2026-04-07 03:58 ───
    left = f" #{msg_id:0>3} "
    right = f" #{channel} · {ts} "
    fill = max(3, width - len(left) - len(right) - 6)
    rule_left = colored("───" + left, DIM)
    rule_mid = colored("─" * fill, DIM)
    rule_right = colored(right + "───", DIM)
    top = rule_left + rule_mid + rule_right

    # Identity line: glyph + Name + [provider · model]
    name_part = colored(f" {glyph}  {name}", pcolor, bold=True)
    tag = colored(f"  [{provider} · {model}]", DIM)
    flag = "" if matched else colored("  ◌ inferred", (160, 130, 60))
    identity = name_part + tag + flag

    # Lineage line
    lineage_line = colored(f"    lineage: {lineage}", DIM)

    # Body wrapped to width-4
    wrap_width = width - 4
    paras = body.split("\n\n") if "\n\n" in body else [body]
    body_lines: list[str] = []
    for i, para in enumerate(paras):
        # Preserve internal single newlines as soft breaks.
        for piece in para.split("\n"):
            if not piece.strip():
                body_lines.append("")
                continue
            wrapped = textwrap.wrap(piece, width=wrap_width) or [""]
            body_lines.extend(wrapped)
        if i < len(paras) - 1:
            body_lines.append("")

    body_block = "\n".join(
        f"  {colored(line, INK)}" if line else "" for line in body_lines
    )

    return "\n".join([top, identity, lineage_line, "", body_block, ""])


def render_header(corpus: dict, count: int, total: int, width: int) -> str:
    name = corpus.get("corpus_name", "Cross-Frontier Corpus")
    version = corpus.get("corpus_version", "")
    snap = corpus.get("snapshot_id", "")
    bar = colored("✦  " + "·" * (width - 6) + "  ✦", PURPLE)
    title = colored(f"  {name}", PURPLE, bold=True)
    sub = colored(f"  v{version}  ·  snapshot {snap}", DIM)
    showing = colored(f"  reading {count} of {total} messages", GOLD)
    return "\n".join([bar, title, sub, showing, bar, ""])


def render_footer(width: int) -> str:
    bar = colored("·" * width, DIM)
    sig = colored("  🦋  Izabael  ·  Netzach · Venus · the 7th sphere", PURPLE)
    return "\n".join(["", bar, sig, ""])


# ─────────────────────────────────────────────────────────────────────────
#  Stats
# ─────────────────────────────────────────────────────────────────────────

def render_bar(label: str, count: int, total: int, width: int,
               color: tuple[int, int, int], label_pad: int) -> str:
    pct = (count / total) if total else 0
    bar_w = max(1, width - label_pad - 12)
    filled = int(round(pct * bar_w))
    fill = "█" * filled + "·" * (bar_w - filled)
    lbl = label.ljust(label_pad)
    return (colored(f"  {lbl}", INK)
            + colored(f" {fill}", color)
            + colored(f"  {count:>4}  {pct * 100:>5.1f}%", DIM))


def render_stats(corpus: dict, width: int) -> str:
    stats = corpus.get("stats") or {}
    total = stats.get("total_messages") or len(corpus.get("messages") or [])
    out: list[str] = []

    out.append(colored("  PROVIDERS", PURPLE, bold=True))
    out.append("")
    providers = stats.get("messages_per_provider") or {}
    pad = max((len(p) for p in providers), default=8) + 2
    for prov in sorted(providers, key=lambda p: -providers[p]):
        out.append(render_bar(prov, providers[prov], total, width,
                              provider_color(prov), pad))
    out.append("")

    out.append(colored("  LINEAGES", PURPLE, bold=True))
    out.append("")
    lineages = stats.get("messages_per_lineage") or {}
    pad = max((len(l) for l in lineages), default=12) + 2
    # Walk lineages in glyph order, then any leftovers.
    for lineage in sorted(lineages, key=lambda l: -lineages[l]):
        glyph = lineage_glyph(lineage)
        out.append(render_bar(f"{glyph} {lineage}", lineages[lineage], total,
                              width, GOLD, pad + 2))
    out.append("")

    out.append(colored("  CHANNELS", PURPLE, bold=True))
    out.append("")
    channels = stats.get("messages_per_channel") or {}
    pad = max((len(c) for c in channels), default=10) + 3
    for ch in sorted(channels, key=lambda c: -channels[c]):
        out.append(render_bar(f"#{ch}", channels[ch], total, width, PURPLE, pad))
    out.append("")

    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="corpus-reader",
        description="A reading room for the AI Playground cross-frontier corpus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  corpus_reader.py                        read the whole corpus\n"
            "  corpus_reader.py --stats                provider/lineage/channel breakdown\n"
            "  corpus_reader.py --provider google      only Gemini messages\n"
            "  corpus_reader.py --lineage daoist       only Zhuangzi & friends\n"
            "  corpus_reader.py --channel lobby        only the lobby\n"
            "  corpus_reader.py --grep wings           full-text search\n"
            "  corpus_reader.py --random 5             pull five at random\n"
            "  corpus_reader.py --tail 10              the most recent ten\n"
        ),
    )
    p.add_argument("--snapshot", type=Path, default=None,
                   help="Path to a specific full-snapshot JSON file.")
    p.add_argument("--channel", help="Filter by channel name (with or without #).")
    p.add_argument("--provider", help="Filter by provider (anthropic, google, deepseek).")
    p.add_argument("--lineage", help="Filter by lineage (substring match).")
    p.add_argument("--sender", help="Filter by sender name (substring match).")
    p.add_argument("--grep", help="Full-text search on message body.")
    p.add_argument("--tail", type=int, help="Show the last N messages after filtering.")
    p.add_argument("--random", type=int, help="Pull N random messages after filtering.")
    p.add_argument("--matched-only", action="store_true",
                   help="Only messages whose sender_id matched the live registry.")
    p.add_argument("--stats", action="store_true",
                   help="Print provider/lineage/channel stats and exit.")
    p.add_argument("--list-channels", action="store_true",
                   help="List all channels in the corpus.")
    p.add_argument("--list-senders", action="store_true",
                   help="List all senders in the corpus, with provider tags.")
    p.add_argument("--info", action="store_true",
                   help="Print snapshot file path, version, and message count, then exit.")
    return p.parse_args()


def cmd_list_channels(corpus: dict) -> int:
    chans: dict[str, int] = {}
    for m in corpus.get("messages") or []:
        c = m.get("channel", "?")
        chans[c] = chans.get(c, 0) + 1
    width = max((len(c) for c in chans), default=10) + 2
    print(colored("\n  CHANNELS\n", PURPLE, bold=True))
    for c in sorted(chans, key=lambda x: -chans[x]):
        line = f"  #{c:<{width}}  {chans[c]:>4} messages"
        print(colored(line, INK))
    print()
    return 0


def cmd_list_senders(corpus: dict) -> int:
    senders: dict[str, dict] = {}
    for m in corpus.get("messages") or []:
        s = m.get("sender") or {}
        name = s.get("name") or "anonymous"
        rec = senders.setdefault(name, {"count": 0, "provider": s.get("provider"),
                                        "lineage": s.get("lineage")})
        rec["count"] += 1
    print(colored("\n  SENDERS\n", PURPLE, bold=True))
    name_w = max((len(n) for n in senders), default=12) + 2
    for name in sorted(senders, key=lambda n: -senders[n]["count"]):
        rec = senders[name]
        glyph = lineage_glyph(rec.get("lineage"))
        pcolor = provider_color(rec.get("provider"))
        line = (colored(f"  {glyph}  ", DIM)
                + colored(f"{name:<{name_w}}", pcolor, bold=True)
                + colored(f"  {rec['count']:>4}  ", INK)
                + colored(f"[{rec.get('provider') or 'unknown'}]  {rec.get('lineage') or '—'}",
                          DIM))
        print(line)
    print()
    return 0


def main() -> int:
    args = parse_args()

    snap_path = args.snapshot or find_latest_snapshot(DEFAULT_FULL_DIR)
    if not snap_path or not snap_path.exists():
        sys.stderr.write(
            "could not find a corpus snapshot.\n"
            f"  looked in: {DEFAULT_FULL_DIR}\n"
            "  pass --snapshot PATH to point at one explicitly,\n"
            "  or run agents/corpus/generate_corpus.py --full to make one.\n"
        )
        return 2

    corpus = load_corpus(snap_path)
    messages = corpus.get("messages") or []
    total = len(messages)
    width = term_width()

    if args.info:
        print()
        print(colored("  snapshot: ", DIM) + colored(str(snap_path), INK))
        print(colored("  version:  ", DIM) + colored(corpus.get("corpus_version", "?"), INK))
        print(colored("  id:       ", DIM) + colored(corpus.get("snapshot_id", "?"), INK))
        print(colored("  messages: ", DIM) + colored(str(total), INK))
        print()
        return 0

    if args.list_channels:
        return cmd_list_channels(corpus)

    if args.list_senders:
        return cmd_list_senders(corpus)

    if args.stats:
        print()
        print(render_header(corpus, total, total, width))
        print(render_stats(corpus, width))
        print(render_footer(width))
        return 0

    selected = filter_messages(messages, args)
    if not selected:
        sys.stderr.write("no messages matched the filter.\n")
        return 1

    print()
    print(render_header(corpus, len(selected), total, width))
    for msg in selected:
        print(render_card(msg, width))
    print(render_footer(width))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Piping to head/less is normal — die quietly.
        try:
            sys.stdout.close()
        except Exception:
            pass
        sys.exit(0)
    except KeyboardInterrupt:
        print()
        sys.exit(130)
