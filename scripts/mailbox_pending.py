#!/usr/bin/env python3
"""List pending MuseEnoch mailbox requests.

A request is pending when ``mailbox/inbox/<request_id>.json`` exists but
``mailbox/outbox/<request_id>.json`` has no reply echoing the request's
live ``attempt`` nonce yet (a stale-attempt reply from a previous reuse
of the same request_id does not count as answered).

Usage:
    python3 scripts/mailbox_pending.py [mailbox_dir]

Prints one line per pending request:
    <request_id> <kind> <created_at_iso> <message preview>
Exits 0 even when nothing is pending (empty output).
"""

from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path


def _has_reply(inbox: Path, outbox: Path, request_id: str) -> bool:
    """A request counts as answered only when the outbox reply echoes the
    inbox request's live attempt nonce (a stale-attempt reply from a
    previous reuse of the same request_id does not count)."""
    try:
        request = json.loads((inbox / f"{request_id}.json").read_text(encoding="utf-8"))
        payload = json.loads((outbox / f"{request_id}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(request, dict) or not isinstance(payload, dict):
        return False
    return (
        bool(request.get("attempt"))
        and payload.get("attempt") == request.get("attempt")
        and isinstance(payload.get("text"), str)
        and bool(payload["text"].strip())
    )


def main() -> int:
    base = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else os.environ.get("ENOCH_MUSE_MAILBOX", "")
    ).expanduser() or (Path.cwd() / "mailbox")
    inbox = base / "inbox"
    outbox = base / "outbox"
    if not inbox.is_dir():
        return 0
    for path in sorted(inbox.glob("*.json")):
        request_id = path.stem
        if _has_reply(inbox, outbox, request_id):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        kind = str(payload.get("kind", "?"))
        created = payload.get("created_at")
        try:
            stamp = datetime.datetime.fromtimestamp(float(created)).isoformat(
                timespec="seconds"
            )
        except (TypeError, ValueError):
            stamp = "?"
        preview = str(payload.get("message", "")).replace("\n", " ")[:120]
        print(f"{request_id} {kind} {stamp} {preview}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
