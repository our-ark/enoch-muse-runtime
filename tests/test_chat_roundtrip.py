#!/usr/bin/env python3
"""Round-trip tests for the muse mailbox chat provider.

Stdlib ``unittest`` only (no pytest dependency). Run from the repo root:

    python3 tests/test_chat_roundtrip.py

Covers:
  (a) drop_chat_message -> receive() returns a ChatEvent with the right
      text, cursor, and conversation id;
  (b) cursor filtering: receive(cursor) only returns newer messages;
  (c) send_message writes chat_outbox and returns a message id;
  (d) empty text is rejected on the inbound path.
"""

from __future__ import annotations

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
from our_ark_muse.chat import MuseChatError  # noqa: E402
from our_ark_provider_kit.contracts import ChatProvider  # noqa: E402


class ChatRoundtripTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["ENOCH_MUSE_MAILBOX"] = self.tmp.name
        # Fresh client per test; mailbox dirs are created on demand.
        self.client = create_chat_provider()

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("ENOCH_MUSE_MAILBOX", None)

    def test_satisfies_chat_provider_contract(self) -> None:
        self.assertIsInstance(self.client, ChatProvider)
        self.assertEqual(self.client.provider_kind, "chat")
        self.assertEqual(self.client.name, "muse")

    def test_inbound_roundtrip(self) -> None:
        seq = drop_chat_message("@enoch hello there")
        events = self.client.receive()
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.cursor, seq)
        self.assertEqual(event.conversation_id, CONVERSATION_ID)
        self.assertEqual(event.text, "@enoch hello there")
        self.assertTrue(event.message_id)

    def test_cursor_filters_older_messages(self) -> None:
        first = drop_chat_message("first")
        second = drop_chat_message("second")
        events = self.client.receive(cursor=first)
        self.assertEqual([e.cursor for e in events], [second])
        self.assertEqual(events[0].text, "second")
        self.assertEqual(self.client.receive(cursor=second), [])

    def test_send_message_roundtrip(self) -> None:
        message_id = self.client.send_message(CONVERSATION_ID, "Enoch replies here.")
        self.assertTrue(message_id)
        outbox = Path(self.tmp.name) / "chat_outbox"
        files = list(outbox.glob("*.json"))
        self.assertEqual(len(files), 1)
        import json

        payload = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(payload["text"], "Enoch replies here.")
        self.assertEqual(payload["message_id"], message_id)

    def test_empty_inbound_rejected(self) -> None:
        with self.assertRaises(MuseChatError):
            drop_chat_message("   ")


if __name__ == "__main__":
    unittest.main(verbosity=2)
