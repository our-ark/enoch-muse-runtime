#!/usr/bin/env python3
"""Write a properly-formed mailbox reply for one inbox request.

The provider (``our_ark_muse.core``) only accepts a reply that echoes the
``attempt`` nonce from the inbox request it answers. The consumer must
capture that nonce **when it reads the request** and pass it back with
``--attempt``; this helper never substitutes the inbox file's *current*
attempt, because the request may have been superseded (same request_id
reused for a new attempt) while the answer was being reasoned. Stamping a
stale answer with the live attempt would make the provider accept a reply
it never asked for.

Usage:
    python3 scripts/mailbox_reply.py <request_id> --attempt <nonce> \\
        --text "..." [--mailbox DIR]

Refuses (non-zero exit) when:
  - the text is empty;
  - the inbox request is missing, unreadable, or already cancelled
    (moved to ``dead-letter/``);
  - the request carries no attempt nonce (legacy pre-protocol request);
  - the inbox's live attempt differs from ``--attempt`` (the request was
    superseded while this answer was being produced -- the answer is
    stale and must be dropped, not re-stamped);
  - a valid reply for this attempt already exists (no overwrite).
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
    parser.add_argument(
        "--attempt",
        required=True,
        help="attempt nonce captured when the consumer READ the request; "
        "must match the inbox's live attempt or the reply is refused",
    )
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
    if (base / "dead-letter" / f"{args.request_id}.json").exists():
        print("request was cancelled (dead-letter); refusing", file=sys.stderr)
        return 1
    try:
        request = json.loads(inbox_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"no readable request at {inbox_file}", file=sys.stderr)
        return 1
    live_attempt = request.get("attempt") if isinstance(request, dict) else None
    if not live_attempt:
        print("request has no attempt nonce; refusing (provider would reject)",
              file=sys.stderr)
        return 1
    if live_attempt != args.attempt:
        print(
            "inbox attempt rotated since this answer was reasoned "
            f"(read {args.attempt[:8]}..., live {str(live_attempt)[:8]}...); "
            "the request was superseded -- refusing to stamp a stale answer "
            "with the live attempt",
            file=sys.stderr,
        )
        return 3
    if outbox_file.exists():
        try:
            existing = json.loads(outbox_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            existing = {}
        if isinstance(existing, dict) and existing.get("attempt") == args.attempt \
                and isinstance(existing.get("text"), str) and existing["text"].strip():
            print("a valid reply for this attempt already exists; not overwriting",
                  file=sys.stderr)
            return 1
    reply = {
        "request_id": args.request_id,
        "attempt": args.attempt,
        "text": args.text,
        "replied_at": time.time(),
    }
    _atomic_write_json(outbox_file, reply)
    print(f"wrote {outbox_file} (attempt {args.attempt[:8]}...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
