#!/usr/bin/env python3
"""Tests for in_reply_to threading on the muse mailbox chat provider.

Stdlib ``unittest`` only (no pytest dependency). Run from the repo root:

    python3 tests/test_in_reply_to.py

Covers:
  (a) a reply sent after ``send_read_ack`` carries ``in_reply_to`` pointing
      at the acked inbound message id;
  (b) a proactive send with no prior ack carries no ``in_reply_to``;
  (c) the pending ack persists until the *next* ack (progress updates stay
      threaded under the same inbound event);
  (d) acking a new message re-threads subsequent replies to it.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
# Enoch's provider-kit is a local source tree, not an installed package.
# Resolved portably: ENOCH_SRC env, then ~/enoch-body, then the legacy path.
def _provider_kit_src() -> str:
    candidates = []
    env_src = os.environ.get("ENOCH_SRC")
    if env_src:
        candidates.append(Path(env_src) / "libraries" / "provider-kit" / "src")
    candidates.append(Path.home() / "enoch-body" / "libraries" / "provider-kit" / "src")
    candidates.append(
        Path("/home/hatch/workspace/enoch-experiment/libraries/provider-kit/src")
    )
    for candidate in candidates:
        if (candidate / "our_ark_provider_kit").is_dir():
            return str(candidate)
    raise RuntimeError("provider-kit src not found; set ENOCH_SRC")


sys.path.insert(0, _provider_kit_src())

from our_ark_muse import (  # noqa: E402
    CONVERSATION_ID,
    create_chat_provider,
    drop_chat_message,
)
from our_ark_muse.chat import _PENDING_IN_REPLY_TO  # noqa: E402


class InReplyToTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["ENOCH_MUSE_MAILBOX"] = self.tmp.name
        # The pending-ack tracker is module-global: reset between tests.
        _PENDING_IN_REPLY_TO.set(None)
        self.client = create_chat_provider()

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("ENOCH_MUSE_MAILBOX", None)
        _PENDING_IN_REPLY_TO.set(None)

    def _outbox_payloads(self) -> list[dict]:
        outbox = Path(self.tmp.name) / "chat_outbox"
        payloads = []
        for child in sorted(outbox.glob("*.json")):
            payloads.append(json.loads(child.read_text(encoding="utf-8")))
        return payloads

    def test_reply_threads_to_acked_message(self) -> None:
        drop_chat_message("@enoch hello there")
        events = self.client.receive()
        self.assertEqual(len(events), 1)
        event = events[0]
        self.client.send_read_ack(event.conversation_id, event.message_id)
        self.client.send_message(event.conversation_id, "Enoch replies here.")
        payloads = self._outbox_payloads()
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["in_reply_to"], event.message_id)

    def test_proactive_send_has_no_in_reply_to(self) -> None:
        self.client.send_message(CONVERSATION_ID, "proactive notification")
        payloads = self._outbox_payloads()
        self.assertEqual(len(payloads), 1)
        self.assertNotIn("in_reply_to", payloads[0])

    def test_ack_persists_until_next_ack(self) -> None:
        drop_chat_message("@enoch first")
        (event,) = self.client.receive()
        self.client.send_read_ack(event.conversation_id, event.message_id)
        self.client.send_message(event.conversation_id, "reply one")
        self.client.send_message(event.conversation_id, "still working…")
        payloads = self._outbox_payloads()
        self.assertEqual(len(payloads), 2)
        for payload in payloads:
            self.assertEqual(payload["in_reply_to"], event.message_id)

    def test_new_ack_rethreads(self) -> None:
        drop_chat_message("@enoch first")
        (first,) = self.client.receive(cursor=0)
        drop_chat_message("@enoch second")
        (second,) = self.client.receive(cursor=first.cursor)
        self.client.send_read_ack(first.conversation_id, first.message_id)
        self.client.send_message(first.conversation_id, "reply to first")
        self.client.send_read_ack(second.conversation_id, second.message_id)
        self.client.send_message(second.conversation_id, "reply to second")
        by_text = {p["text"]: p for p in self._outbox_payloads()}
        self.assertEqual(by_text["reply to first"]["in_reply_to"], first.message_id)
        self.assertEqual(by_text["reply to second"]["in_reply_to"], second.message_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
