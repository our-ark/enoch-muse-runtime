#!/usr/bin/env python3
"""Mailbox consumer STUB for the MuseEnoch PoC.

This file documents the external-side protocol only. It is NOT wired to
anything live: there is intentionally no loop here that would summon a
Muse turn on its own. In the real deployment, a scheduled job (cron)
runs the equivalent of ``main()`` below on a timer: scan the inbox, hand
each prompt to the Muse operator, and write the reply file the provider
is polling for.

Mailbox protocol (see ``our_ark_muse.core`` for the provider side):

    <mailbox>/inbox/<request_id>.json
        {
          "request_id": "...",            # from the harness, or uuid4 hex
          "kind": "respond" | "act_in_session",
          "identity": {"name": ..., "mission": ...},
          "message": "...",               # the full prompt for this turn
          "session_key": "...",           # thread key; keep one Muse-side
                                          # thread per session_key for continuity
          "sandbox": "read-only" | "workspace-write" | ...,
          "cwd": "...", "state_root": "...",
          "image_paths": [...],           # host-local paths, if any
          "created_at": 1234567890.0
        }

    <mailbox>/outbox/<request_id>.json   (written by the consumer)
        {
          "request_id": "...",
          "text": "...",                  # PLAIN TEXT reply; the harness
                                          # parses [ENOCH_ACTION] blocks itself
          "created_at": 1234567890.0
        }

Consumer rules:

1. Write the reply file ATOMICALLY: write to a temp file in the same
   directory, chmod 0600, then ``os.replace()`` into place. The provider
   tolerates transient partial reads, but atomic rename is the contract.
2. Reply with plain text. To make Enoch act (run a command, queue work),
   emit ``[ENOCH_ACTION]{"command": ..., "argument": ...}[/ENOCH_ACTION]``
   blocks verbatim in the text -- the harness parses them; anything else
   is treated as the final answer for the turn.
3. One provider call == one reply. There is no harness-managed session
   resume (unlike codex ``--resume``): keep per-``session_key`` threads on
   the Muse side if multi-turn continuity matters.
4. Expire stale inbox entries (e.g. older than 2h with no reply) so a
   crashed daemon cannot leave orphan requests that a later reply would
   confuse. Request ids are unique per attempt.
5. Mailbox dirs are 0700, files 0600: prompts carry private agent state
   (identity, memory). Treat the mailbox like the migration bundle.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def mailbox_base() -> Path:
    raw = os.environ.get("ENOCH_MUSE_MAILBOX", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.cwd() / ".enoch" / "muse_mailbox"


def pending_requests(base: Path) -> list[Path]:
    inbox = base / "inbox"
    if not inbox.is_dir():
        return []
    return sorted(inbox.glob("*.json"))


def main() -> int:
    base = mailbox_base()
    pending = pending_requests(base)
    if not pending:
        print(f"no pending requests in {base / 'inbox'}")
        return 0
    for request_file in pending:
        try:
            payload = json.loads(request_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"SKIP unreadable {request_file.name}: {exc}")
            continue
        age = time.time() - float(payload.get("created_at", 0) or 0)
        print(f"PENDING {request_file.name} kind={payload.get('kind')} age={age:.0f}s")
        print("  identity:", payload.get("identity"))
        print("  session_key:", payload.get("session_key"))
        # --- the live consumer would, for each request: ---
        # 1. hand payload["message"] (+ identity/sandbox context) to the
        #    Muse operator on a per-session_key thread;
        # 2. collect the plain-text reply (with [ENOCH_ACTION] blocks as needed);
        # 3. atomic-write {"request_id","text","created_at"} to
        #    outbox/<request_id>.json (0600, os.replace);
        # 4. optionally archive/remove the inbox file afterwards.
        print("  -> stub: not wired to a live Muse operator; no reply written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
