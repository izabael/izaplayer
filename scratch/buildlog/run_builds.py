#!/usr/bin/env python3
"""run_builds — dispatch the brief to Gemini and DeepSeek, save outputs.

Reads scratch/buildlog/briefs/<slug>.md, sends it verbatim to each provider
as a one-shot build request, saves the raw response to
scratch/buildlog/<provider>_<slug>.py. No merging, no cleanup —
whatever the model returned, that's what gets saved. Human review
happens after.

Usage:
    python3 run_builds.py buffering
    python3 run_builds.py buffering --only gemini
    python3 run_builds.py buffering --only deepseek

Keys: GEMINI_API_KEY, DEEPSEEK_API_KEY from env.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

HERE = Path(__file__).parent
BRIEFS = HERE / "briefs"

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


def strip_fence(text: str) -> str:
    """Some models ignore 'no fence' and wrap the file in ```python ... ```.
    Tolerate it: if the output begins with a fence, strip the fence."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        # drop first line (```python or ```)
        lines = lines[1:]
        # drop trailing fence
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines)
    return t.strip() + "\n"


def call_gemini(prompt: str) -> tuple[str, dict]:
    if not GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    model = "gemini-2.0-flash"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={GEMINI_KEY}"
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 8192},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read().decode("utf-8"))
    dt = time.time() - t0
    text = resp["candidates"][0]["content"]["parts"][0]["text"]
    meta = {
        "provider": "gemini",
        "model": model,
        "seconds": round(dt, 2),
        "usage": resp.get("usageMetadata", {}),
    }
    return strip_fence(text), meta


def call_deepseek(prompt: str) -> tuple[str, dict]:
    if not DEEPSEEK_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    model = "deepseek-chat"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 8192,
    }
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
        },
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.loads(r.read().decode("utf-8"))
    dt = time.time() - t0
    text = resp["choices"][0]["message"]["content"]
    meta = {
        "provider": "deepseek",
        "model": model,
        "seconds": round(dt, 2),
        "usage": resp.get("usage", {}),
    }
    return strip_fence(text), meta


PROVIDERS = {"gemini": call_gemini, "deepseek": call_deepseek}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("slug", help="short name for the build, e.g. 'buffering'")
    p.add_argument("--only", choices=list(PROVIDERS), help="run just one provider")
    args = p.parse_args()

    brief_path = BRIEFS / f"{args.slug}.md"
    if not brief_path.exists():
        print(f"no brief at {brief_path}", file=sys.stderr)
        return 2
    prompt = brief_path.read_text()

    providers = [args.only] if args.only else list(PROVIDERS)
    all_meta = {}
    for name in providers:
        print(f"\n─── {name} ─────────────────────────")
        try:
            code, meta = PROVIDERS[name](prompt)
        except Exception as exc:
            print(f"  !! {name} failed: {exc}")
            continue
        out = HERE / f"{name}_{args.slug}.py"
        out.write_text(code)
        all_meta[name] = meta
        print(f"  wrote {out}")
        print(f"  model: {meta['model']}  ·  {meta['seconds']}s")
        print(f"  usage: {meta.get('usage')}")
        print(f"  lines: {len(code.splitlines())}")

    meta_path = HERE / f"{args.slug}_meta.json"
    meta_path.write_text(json.dumps(all_meta, indent=2) + "\n")
    print(f"\nmeta saved to {meta_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
