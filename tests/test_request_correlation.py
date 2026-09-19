#!/usr/bin/env python3
"""Request/reply correlation and timeout-lifecycle tests for the muse provider.

Stdlib ``unittest`` only (no pytest dependency). Run from the repo root:

    python3 tests/test_request_correlation.py

Covers the two failure modes reported 2026-09-18:

  (a) Stale-outbox reuse: the harness reuses a fixed request_id (the
      task-context path does this). The second ``respond()`` must NOT
      return the first attempt's reply instantly; a reply carrying the
      old attempt nonce must be ignored, and only the reply echoing the
      live attempt is accepted.
  (b) Timeout lifecycle: when the wait times out, the provider must close
      the request's lifecycle -- the inbox file moves to ``dead-letter/``
      stamped with ``cancelled_at`` / ``cancel_reason`` -- instead of
      leaving it for a later consumer to answer.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
# Enoch's provider-kit is a local source tree, not an installed package.
sys.path.insert(
    0, "/home/hatch/workspace/enoch-experiment/libraries/provider-kit/src"
)

from our_ark_muse import create_provider  # noqa: E402
from our_ark_provider_kit.contracts import (  # noqa: E402
    AgentRuntimeTimedOut,
    RuntimeExecutionControl,
)


class _Identity:
    """Duck-typed AgentIdentity (name + mission)."""

    def __init__(self, name: str = "Enoch", mission: str = "test mission") -> None:
        self.name = name
        self.mission = mission


class RequestCorrelationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.mailbox = Path(self.tmp.name) / "mailbox"
        self._saved_env = {
            key: os.environ.get(key)
            for key in (
                "ENOCH_MUSE_MAILBOX",
                "ENOCH_MUSE_POLL_SECONDS",
                "ENOCH_MUSE_TIMEOUT",
            )
        }
        os.environ["ENOCH_MUSE_MAILBOX"] = str(self.mailbox)
        os.environ["ENOCH_MUSE_POLL_SECONDS"] = "0.2"

        def _restore() -> None:
            for key, value in self._saved_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        self.addCleanup(_restore)
        self.provider = create_provider()

    def _inbox_payload(self, request_id: str) -> dict:
        return json.loads((self.mailbox / "inbox" / f"{request_id}.json").read_text())

    def _write_reply_raw(self, request_id: str, payload: dict) -> None:
        outbox = self.mailbox / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        tmp = outbox / f".{request_id}.tmp"
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, outbox / f"{request_id}.json")

    def test_same_request_id_reuse_gets_fresh_attempt(self) -> None:
        """Second call with the same request_id must not see the first reply."""
        rid = "task:fixed-id"
        ident = _Identity()
        first: dict = {}
        second: dict = {}

        def call_first() -> None:
            first["result"] = self.provider.respond(
                ident, "first", execution=RuntimeExecutionControl(request_id=rid)
            ).final_text

        t1 = threading.Thread(target=call_first)
        t1.start()
        try:
            deadline = time.monotonic() + 10
            inbox = self.mailbox / "inbox" / f"{rid}.json"
            while not inbox.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(inbox.exists(), "provider never dropped the request")
            attempt1 = json.loads(inbox.read_text())["attempt"]
            self.assertTrue(attempt1, "inbox payload must carry an attempt nonce")
            # Consumer answers attempt 1.
            self._write_reply_raw(
                rid, {"request_id": rid, "attempt": attempt1, "text": "reply-one"}
            )
            t1.join(timeout=10)
            self.assertFalse(t1.is_alive(), "first respond() did not return")
            self.assertEqual(first["result"], "reply-one")
        finally:
            t1.join(timeout=10)

        # Second call reuses the same request_id. The stale outbox file
        # must not be returned (the 0.5ms instant-return bug).
        started = time.monotonic()

        def call_second() -> None:
            second["result"] = self.provider.respond(
                ident, "second", execution=RuntimeExecutionControl(request_id=rid)
            ).final_text

        t2 = threading.Thread(target=call_second)
        t2.start()
        try:
            time.sleep(1.0)
            self.assertTrue(
                t2.is_alive(),
                "second respond() returned without a fresh reply "
                f"(elapsed {time.monotonic() - started:.3f}s) -- stale outbox reuse!",
            )
            attempt2 = self._inbox_payload(rid)["attempt"]
            self.assertNotEqual(attempt2, attempt1, "attempt nonce must rotate")
            # A late/duplicate reply carrying the OLD attempt is ignored.
            self._write_reply_raw(
                rid, {"request_id": rid, "attempt": attempt1, "text": "stale!"}
            )
            time.sleep(1.0)
            self.assertTrue(t2.is_alive(), "stale-attempt reply was wrongly accepted")
            # The correct reply (live attempt) is accepted.
            self._write_reply_raw(
                rid, {"request_id": rid, "attempt": attempt2, "text": "reply-two"}
            )
            t2.join(timeout=10)
            self.assertFalse(t2.is_alive(), "second respond() did not return")
            self.assertEqual(second["result"], "reply-two")
        finally:
            t2.join(timeout=10)

    def test_timeout_quarantines_request_to_dead_letter(self) -> None:
        """A timed-out wait must close the request lifecycle."""
        rid = "task:will-timeout"
        os.environ["ENOCH_MUSE_TIMEOUT"] = "60"  # fallback, not used here
        outcome: dict = {}

        def call() -> None:
            try:
                self.provider.respond(
                    _Identity(),
                    "nobody answers",
                    execution=RuntimeExecutionControl(
                        request_id=rid, timeout_seconds=2
                    ),
                )
            except BaseException as exc:  # noqa: BLE001 - capture for assertion
                outcome["exc"] = exc

        t = threading.Thread(target=call)
        t.start()
        t.join(timeout=15)
        self.assertFalse(t.is_alive(), "respond() did not time out")
        self.assertIsInstance(outcome.get("exc"), AgentRuntimeTimedOut)
        # The inbox file must be gone and quarantined with stamps.
        self.assertFalse((self.mailbox / "inbox" / f"{rid}.json").exists())
        dead = self.mailbox / "dead-letter" / f"{rid}.json"
        self.assertTrue(dead.exists(), "timed-out request not moved to dead-letter/")
        payload = json.loads(dead.read_text())
        self.assertEqual(payload["cancel_reason"], "timeout")
        self.assertGreater(payload["cancelled_at"], 0)
        self.assertIn("attempt", payload)


class MailboxReplyHelperTest(unittest.TestCase):
    """Regression test for the stale-answer re-stamping race (2026-09-19).

    Race: request A (attempt a1) is read by the consumer; A times out and
    the same request_id is reused for request B (attempt a2); A's late
    answer is then submitted. The helper must NOT stamp that stale answer
    with B's live attempt -- it must refuse, because the consumer's
    captured attempt (a1) no longer matches the inbox's live attempt (a2).
    """

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.mailbox = Path(self.tmp.name) / "mailbox"
        (self.mailbox / "inbox").mkdir(parents=True)
        (self.mailbox / "outbox").mkdir(parents=True)
        self.helper = REPO_ROOT / "scripts" / "mailbox_reply.py"

    def _write_inbox(self, request_id: str, attempt: str) -> None:
        (self.mailbox / "inbox" / f"{request_id}.json").write_text(
            json.dumps(
                {
                    "request_id": request_id,
                    "attempt": attempt,
                    "kind": "respond",
                    "message": "hello",
                    "created_at": time.time(),
                }
            ),
            encoding="utf-8",
        )

    def _reply(self, request_id: str, attempt: str, text: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(self.helper),
                request_id,
                "--attempt",
                attempt,
                "--text",
                text,
                "--mailbox",
                str(self.mailbox),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_stale_answer_refused_after_attempt_rotation(self) -> None:
        rid = "race:1"
        # Consumer reads request A and captures attempt a1.
        self._write_inbox(rid, "a1")
        captured_attempt = json.loads(
            (self.mailbox / "inbox" / f"{rid}.json").read_text()
        )["attempt"]
        self.assertEqual(captured_attempt, "a1")
        # A times out; the same request_id is reused for request B.
        self._write_inbox(rid, "a2")
        # A's late answer arrives, carrying the attempt captured at read.
        stale = self._reply(rid, "a1", "stale answer from A")
        self.assertNotEqual(
            stale.returncode, 0, "stale answer must be refused after rotation"
        )
        self.assertIn("superseded", stale.stderr)
        # Nothing may be written: B must not see A's answer under its nonce.
        outbox_file = self.mailbox / "outbox" / f"{rid}.json"
        self.assertFalse(
            outbox_file.exists(),
            "refused stale answer must not leave an outbox file",
        )
        # A fresh answer for the live attempt is still accepted.
        fresh = self._reply(rid, "a2", "fresh answer for B")
        self.assertEqual(fresh.returncode, 0, fresh.stderr)
        payload = json.loads(outbox_file.read_text())
        self.assertEqual(payload["attempt"], "a2")
        self.assertEqual(payload["text"], "fresh answer for B")

    def test_attempt_argument_is_required(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(self.helper), "x", "--text", "hi"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertNotEqual(proc.returncode, 0, "--attempt must be mandatory")


if __name__ == "__main__":
    unittest.main(verbosity=2)
