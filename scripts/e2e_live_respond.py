#!/usr/bin/env python3
"""Live end-to-end test: load MuseRuntime through Enoch's real provider
registry, then run one blocking respond() turn through the file mailbox.

The consumer side (this repo's cron job, or a human acting as Muse) must
write ``mailbox/outbox/<request_id>.json`` while this script waits.

Usage:
    ENOCH_MUSE_MAILBOX=~/workspace/muse-enoch/mailbox \\
    ENOCH_MUSE_POLL_SECONDS=2 ENOCH_MUSE_TIMEOUT=300 \\
    PYTHONPATH=<enoch>/src:<enoch>/libraries/provider-kit/src \\
    python3 scripts/e2e_live_respond.py "prompt text"
"""

from __future__ import annotations

import sys
import types

from enoch.providers.registry import available_providers, load_provider


def main() -> int:
    print("available runtime providers:", available_providers("runtime"), flush=True)
    provider = load_provider("runtime", name="muse")
    print(
        "loaded:",
        type(provider).__module__ + "." + type(provider).__name__,
        flush=True,
    )
    print("health:", provider.health(), flush=True)

    identity = types.SimpleNamespace(
        name="Enoch",
        mission="End-to-end test of the MuseEnoch mailbox bridge.",
    )
    message = sys.argv[1] if len(sys.argv) > 1 else (
        "Live end-to-end test of the MuseEnoch mailbox bridge. "
        "Reply with one short acknowledgement line that includes the request id."
    )
    result = provider.respond(identity, message, session_key="e2e-live-1")
    print("respond() returned.", flush=True)
    print("session_id:", result.session_id, flush=True)
    print("final_text:", result.final_text, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
