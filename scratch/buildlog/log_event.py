#!/usr/bin/env python3
"""log_event — append a ship / reject / grade event to BUILDS.jsonl.

run_builds.py auto-logs every build attempt. This helper logs the
events that happen AFTER the build — reviewer decisions, grader
results, and the occasional retroactive note.

Usage:
    log_event.py ship   <slug> <provider> [--from-draft X] [--commit SHA] [--notes "..."]
    log_event.py reject <slug> <provider> [--notes "..."]
    log_event.py grade  <slug> <provider> --passed N --total M [--failures a,b,c] [--notes "..."]
    log_event.py note   <slug> --notes "..."     # free-form entry tied to a slug
    log_event.py tail [N]                          # show last N entries

Examples:
    log_event.py ship buffering deepseek --commit 6800c3e \\
        --notes "in-place animation + status-line-lies joke"
    log_event.py grade kamea gemini --passed 6 --total 7 --failures sun \\
        --notes "Strachey singly-even method broken"
    log_event.py tail 10

BUILDS.jsonl is append-only. Nothing in this file ever rewrites a
prior line — every event is a new line. The log is the record.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
LOG = HERE / "BUILDS.jsonl"


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _operator() -> str:
    return os.environ.get("IZABAEL_SISTER", os.environ.get("USER", "unknown"))


def append(event: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"logged {event['type']}: {event.get('slug','-')}/{event.get('provider','-')}")


def cmd_ship(args) -> int:
    event = {
        "ts": _utc_now(),
        "type": "ship",
        "slug": args.slug,
        "provider": args.provider,
        "reviewer": _operator(),
    }
    if args.from_draft:
        event["from_draft"] = args.from_draft
    if args.shipped_file:
        event["shipped_file"] = args.shipped_file
    if args.commit:
        event["commit"] = args.commit
    if args.round:
        event["round"] = args.round
    if args.notes:
        event["notes"] = args.notes
    append(event)
    return 0


def cmd_reject(args) -> int:
    event = {
        "ts": _utc_now(),
        "type": "reject",
        "slug": args.slug,
        "provider": args.provider,
        "reviewer": _operator(),
    }
    if args.round:
        event["round"] = args.round
    if args.notes:
        event["notes"] = args.notes
    append(event)
    return 0


def cmd_grade(args) -> int:
    event = {
        "ts": _utc_now(),
        "type": "grade",
        "slug": args.slug,
        "provider": args.provider,
        "passed": args.passed,
        "total": args.total,
        "grader": _operator(),
    }
    if args.round:
        event["round"] = args.round
    if args.failures:
        event["failures"] = [x.strip() for x in args.failures.split(",") if x.strip()]
    if args.notes:
        event["notes"] = args.notes
    append(event)
    return 0


def cmd_note(args) -> int:
    event = {
        "ts": _utc_now(),
        "type": "note",
        "slug": args.slug,
        "author": _operator(),
        "notes": args.notes,
    }
    if args.round:
        event["round"] = args.round
    append(event)
    return 0


def cmd_tail(args) -> int:
    if not LOG.exists():
        print(f"no log at {LOG}")
        return 1
    lines = LOG.read_text().splitlines()
    tail = lines[-args.n:] if args.n > 0 else lines
    for line in tail:
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            print(f"  !! malformed: {line[:80]}")
            continue
        parts = [
            e.get("ts", "?")[:19].replace("T", " "),
            e.get("type", "?").ljust(6),
            (e.get("slug") or "-").ljust(10),
            (e.get("provider") or e.get("author") or e.get("reviewer") or "-").ljust(10),
        ]
        detail = []
        if "seconds" in e: detail.append(f"{e['seconds']}s")
        if "completion_tokens" in e: detail.append(f"{e['completion_tokens']}t")
        if "lines" in e: detail.append(f"{e['lines']}L")
        if "passed" in e: detail.append(f"{e['passed']}/{e['total']}")
        if "commit" in e: detail.append(e["commit"][:7])
        if "notes" in e: detail.append(e["notes"][:60])
        print(" ".join(parts) + "  " + "  ".join(detail))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Append an event to BUILDS.jsonl")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("ship", help="log a ship decision")
    s.add_argument("slug"); s.add_argument("provider")
    s.add_argument("--from-draft"); s.add_argument("--shipped-file")
    s.add_argument("--commit"); s.add_argument("--round", type=int)
    s.add_argument("--notes")
    s.set_defaults(func=cmd_ship)

    r = sub.add_parser("reject", help="log a reject decision")
    r.add_argument("slug"); r.add_argument("provider")
    r.add_argument("--round", type=int); r.add_argument("--notes")
    r.set_defaults(func=cmd_reject)

    g = sub.add_parser("grade", help="log a grader result")
    g.add_argument("slug"); g.add_argument("provider")
    g.add_argument("--passed", type=int, required=True)
    g.add_argument("--total", type=int, required=True)
    g.add_argument("--failures", help="comma-separated list")
    g.add_argument("--round", type=int); g.add_argument("--notes")
    g.set_defaults(func=cmd_grade)

    n = sub.add_parser("note", help="log a free-form note")
    n.add_argument("slug"); n.add_argument("--notes", required=True)
    n.add_argument("--round", type=int)
    n.set_defaults(func=cmd_note)

    t = sub.add_parser("tail", help="print last N events")
    t.add_argument("n", type=int, nargs="?", default=20)
    t.set_defaults(func=cmd_tail)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
