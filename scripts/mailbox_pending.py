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


def _classify(inbox: Path, outbox: Path, request_id: str) -> str:
    """Classify a request as "answered", "pending", or "legacy".

    - Current protocol (inbox carries an ``attempt`` nonce): answered only
      when the outbox reply echoes that attempt with non-empty text (a
      stale-attempt reply from a previous reuse of the same request_id
      does not count).
    - Legacy protocol (no ``attempt`` in the inbox): no valid reply can
      ever be written for it (there is nothing to echo, and mailbox_reply
      refuses attempt-less writes), so it is never "pending". When an
      old-protocol reply with non-empty text exists it counts as
      "answered"; otherwise it is "legacy" (inert, unanswerable)."""
    try:
        request = json.loads((inbox / f"{request_id}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "legacy"
    if not isinstance(request, dict):
        return "legacy"
    try:
        payload = json.loads((outbox / f"{request_id}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        payload = None
    reply_text = (
        payload.get("text", "") if isinstance(payload, dict) else ""
    )
    has_text = isinstance(reply_text, str) and bool(reply_text.strip())
    if request.get("attempt"):
        if (
            isinstance(payload, dict)
            and payload.get("attempt") == request.get("attempt")
            and has_text
        ):
            return "answered"
        return "pending"
    return "answered" if has_text else "legacy"


def _has_reply(inbox: Path, outbox: Path, request_id: str) -> bool:
    return _classify(inbox, outbox, request_id) == "answered"


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
    legacy = 0
    for path in sorted(inbox.glob("*.json")):
        request_id = path.stem
        status = _classify(inbox, outbox, request_id)
        if status == "legacy":
            legacy += 1
            continue
        if status == "answered":
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
    if legacy:
        print(
            f"# {legacy} legacy pre-attempt request(s) skipped "
            "(no attempt nonce; inert, unanswerable)",
            file=sys.stderr,
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
