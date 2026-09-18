#!/usr/bin/env python3
"""Round-trip tests for the muse mailbox runtime provider.

Stdlib ``unittest`` only (no pytest dependency). Run from the repo root:

    python3 tests/test_roundtrip.py

Covers:
  (a) full round-trip: ``respond()`` in a thread, simulated external
      consumer writes ``outbox/<request_id>.json`` after ~3s;
  (b) pre-cancelled execution raises ``AgentRuntimeCancelled`` WITHOUT
      creating any inbox file;
  (c) a short harness timeout raises ``AgentRuntimeTimedOut``.
"""

from __future__ import annotations

import json
import os
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
    AgentRuntime,
    AgentRuntimeCancelled,
    AgentRuntimeTimedOut,
    RuntimeExecutionControl,
    RuntimeResult,
    normalize_runtime_result,
)


class _Identity:
    """Duck-typed AgentIdentity (name + mission)."""

    def __init__(self, name: str = "Enoch", mission: str = "test mission") -> None:
        self.name = name
        self.mission = mission


class MailboxRoundtripTest(unittest.TestCase):
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

    def _write_reply(self, request_id: str, text: str) -> None:
        outbox = self.mailbox / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        tmp = outbox / f".{request_id}.json.tmp"
        tmp.write_text(
            json.dumps(
                {"request_id": request_id, "text": text, "created_at": time.time()}
            ),
            encoding="utf-8",
        )
        os.chmod(tmp, 0o600)
        os.replace(tmp, outbox / f"{request_id}.json")

    # -- (a) round-trip -------------------------------------------------

    def test_roundtrip(self) -> None:
        runtime = create_provider()
        self.assertIsInstance(runtime, AgentRuntime)

        request_id = "test-roundtrip-1"
        result_box: dict[str, object] = {}
        errors: list[BaseException] = []

        def call() -> None:
            try:
                result_box["result"] = normalize_runtime_result(
                    runtime.respond(
                        _Identity(),
                        "hello from harness",
                        execution=RuntimeExecutionControl(
                            request_id=request_id, session_key="s1"
                        ),
                    )
                )
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        worker = threading.Thread(target=call, name="respond-call")
        worker.start()
        try:
            inbox_file = self.mailbox / "inbox" / f"{request_id}.json"
            deadline = time.time() + 15
            while not inbox_file.exists():
                self.assertLess(
                    time.time(), deadline, "provider never dropped the request file"
                )
                time.sleep(0.1)

            # Request file layout + permissions.
            payload = json.loads(inbox_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["request_id"], request_id)
            self.assertEqual(payload["kind"], "respond")
            self.assertEqual(payload["identity"]["name"], "Enoch")
            self.assertEqual(payload["message"], "hello from harness")
            self.assertEqual(payload["session_key"], "s1")
            self.assertEqual(oct(inbox_file.stat().st_mode & 0o777), "0o600")
            self.assertEqual(oct(inbox_file.parent.stat().st_mode & 0o777), "0o700")

            time.sleep(3)  # simulate a slow external consumer
            self._write_reply(request_id, "hello from muse")

            worker.join(timeout=15)
            self.assertFalse(worker.is_alive(), "respond() did not return after reply")
            self.assertFalse(errors, f"respond() raised: {errors!r}")
            result = result_box["result"]
            self.assertIsInstance(result, RuntimeResult)
            assert isinstance(result, RuntimeResult)
            self.assertEqual(result.final_text, "hello from muse")
            self.assertEqual(result.session_id, request_id)
        finally:
            worker.join(timeout=5)

    # -- (b) pre-cancelled execution ------------------------------------

    def test_precancelled_raises_without_side_effects(self) -> None:
        runtime = create_provider()
        cancelled = threading.Event()
        cancelled.set()
        with self.assertRaises(AgentRuntimeCancelled):
            runtime.act_in_session(
                _Identity(),
                "should never run",
                execution=RuntimeExecutionControl(
                    request_id="test-cancel-1", cancellation_event=cancelled
                ),
            )
        inbox = self.mailbox / "inbox"
        self.assertFalse(
            inbox.exists() and any(inbox.iterdir()),
            "pre-cancelled call must not touch the mailbox",
        )

    # -- (c) short harness timeout --------------------------------------

    def test_short_timeout(self) -> None:
        runtime = create_provider()
        started = time.monotonic()
        with self.assertRaises(AgentRuntimeTimedOut):
            runtime.respond(
                _Identity(),
                "nobody answers",
                execution=RuntimeExecutionControl(
                    request_id="test-timeout-1", timeout_seconds=2
                ),
            )
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 10, "timeout took far longer than the deadline")


if __name__ == "__main__":
    unittest.main(verbosity=2)
