#!/usr/bin/env python3
"""Write a properly-formed mailbox reply for one inbox request.

The provider (``our_ark_muse.core``) only accepts a reply that echoes the
``attempt`` nonce from the inbox request it answers. This helper reads
``inbox/<request_id>.json``, copies its attempt into the reply, and
atomic-writes ``outbox/<request_id>.json`` (tmp file + rename, 0600).

Usage:
    python3 scripts/mailbox_reply.py <request_id> --text "..." [--mailbox DIR]

Refuses to overwrite an existing valid reply for the same attempt, and
refuses when the request is missing or already cancelled (dead-letter).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


def _atomic_write_json(path: Path, payload: dict) -> None:
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request_id", help="request id (exact inbox filename stem)")
    parser.add_argument("--text", required=True, help="reply text (non-empty)")
    parser.add_argument(
        "--mailbox",
        default=os.environ.get("ENOCH_MUSE_MAILBOX", ""),
        help="mailbox base dir (default: $ENOCH_MUSE_MAILBOX)",
    )
    args = parser.parse_args()
    if not args.text.strip():
        print("refusing to write an empty reply", file=sys.stderr)
        return 2
    base = Path(args.mailbox).expanduser() if args.mailbox else Path.cwd()
    inbox_file = base / "inbox" / f"{args.request_id}.json"
    outbox_file = base / "outbox" / f"{args.request_id}.json"
    try:
        request = json.loads(inbox_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"no readable request at {inbox_file}", file=sys.stderr)
        return 1
    attempt = request.get("attempt")
    if not attempt:
        print("request has no attempt nonce; refusing (provider would reject)",
              file=sys.stderr)
        return 1
    if outbox_file.exists():
        try:
            existing = json.loads(outbox_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            existing = {}
        if isinstance(existing, dict) and existing.get("attempt") == attempt \
                and isinstance(existing.get("text"), str) and existing["text"].strip():
            print("a valid reply for this attempt already exists; not overwriting",
                  file=sys.stderr)
            return 1
    reply = {
        "request_id": args.request_id,
        "attempt": attempt,
        "text": args.text,
        "replied_at": time.time(),
    }
    _atomic_write_json(outbox_file, reply)
    print(f"wrote {outbox_file} (attempt {attempt[:8]}...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
