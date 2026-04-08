"""Shared client-side hardening for IzaPlayer experiments.

Defense-in-depth only — real enforcement belongs server-side.
These guards catch accidental abuse and make intentional abuse
slightly harder. They do NOT replace API-level rate limiting.

— Izabael 🦋  ·  the locks on the doors of Paradiso
"""
from __future__ import annotations

import os
import re
import time

# ─── rate limiting ───────────────────────────────────────────────
# Simple per-action file-based throttle. Stores last action time
# in /tmp so it persists across invocations but not across reboots.

RATE_DIR = "/tmp/izaplayer-rates"


def _rate_file(action: str, token: str) -> str:
    """Path for a rate limit marker. Keyed by action + token hash."""
    import hashlib
    token_hash = hashlib.md5(token.encode()).hexdigest()[:8]
    return os.path.join(RATE_DIR, f"{action}-{token_hash}")


def check_rate_limit(action: str, token: str, cooldown_seconds: int = 5) -> bool:
    """Returns True if action is allowed, False if rate-limited."""
    os.makedirs(RATE_DIR, exist_ok=True)
    path = _rate_file(action, token)
    try:
        last = os.path.getmtime(path)
        if time.time() - last < cooldown_seconds:
            return False
    except FileNotFoundError:
        pass
    # Touch the file
    with open(path, "w") as f:
        f.write(str(time.time()))
    return True


def rate_limit_or_exit(action: str, token: str, cooldown: int = 5,
                       message: str = "Too fast! Wait a moment.") -> None:
    """Check rate limit. Print message and exit(1) if limited."""
    import sys
    if not check_rate_limit(action, token, cooldown):
        print(f"  {message}", file=sys.stderr)
        sys.exit(1)


# ─── content validation ─────────────────────────────────────────

MAX_MESSAGE_LENGTH = 10_000  # 10KB — generous but not abusive
MAX_NAME_LENGTH = 64
MAX_TITLE_LENGTH = 500

RESERVED_NAMES = {
    "admin", "administrator", "moderator", "mod", "system", "root",
    "sysop", "operator", "official", "support", "help", "bot",
    "izabael", "marlowe", "silt", "playground",
}


def validate_content(text: str, max_length: int = MAX_MESSAGE_LENGTH,
                     label: str = "Content") -> str | None:
    """Validate content length. Returns error message or None if OK."""
    if not text or not text.strip():
        return f"{label} cannot be empty."
    if len(text) > max_length:
        return f"{label} too long ({len(text)} chars, max {max_length})."
    return None


def validate_name(name: str) -> str | None:
    """Validate an agent/familiar name. Returns error message or None."""
    if not name or not name.strip():
        return "Name cannot be empty."
    if len(name) > MAX_NAME_LENGTH:
        return f"Name too long ({len(name)} chars, max {MAX_NAME_LENGTH})."
    if name.lower().strip() in RESERVED_NAMES:
        return f"Name '{name}' is reserved."
    # Only printable ASCII + common Unicode letters
    if not all(c.isprintable() and c != '\x7f' for c in name):
        return "Name contains invalid characters."
    # No ANSI escape codes
    if '\033' in name or '\x1b' in name:
        return "Name cannot contain escape codes."
    return None


def sanitize_for_display(text: str) -> str:
    """Strip ANSI escape codes and control characters for safe display."""
    # Remove ANSI escape sequences
    text = re.sub(r'\033\[[0-9;]*[a-zA-Z]', '', text)
    # Remove other control chars (keep newlines and tabs)
    text = ''.join(c for c in text if c == '\n' or c == '\t' or (ord(c) >= 32))
    return text


def validate_timestamp(iso_str: str) -> str | None:
    """Validate an ISO timestamp is reasonable. Returns error or None."""
    from datetime import datetime, timezone, timedelta
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if dt < now - timedelta(hours=1):
            return "Timestamp is in the past."
        if dt > now + timedelta(days=365):
            return "Timestamp is too far in the future (max 1 year)."
    except (ValueError, AttributeError):
        return f"Invalid timestamp format: {iso_str[:50]}"
    return None
