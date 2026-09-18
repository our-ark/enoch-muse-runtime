"""Muse runtime provider for Enoch (MuseEnoch PoC).

Implements Enoch's ``AgentRuntime`` contract
(``our_ark_provider_kit.contracts``) using an async file mailbox as the
transport to the Muse operator::

    provider  ->  inbox/<request_id>.json    (prompt + context)
    consumer  ->  outbox/<request_id>.json    (reply text)

The provider drops a request file and blocks (polling) until the reply
appears, the execution is cancelled, or the deadline expires.

This is a reasoner-axis (R) substitution under RIPA: Enoch's daemon loop,
leases, audit artifacts, and ``[ENOCH_ACTION]`` text-protocol parsing all
run natively; only the model call itself is bridged. No function-calling
is expected of the provider -- the harness teaches agentic behavior
through the prompt and parses ``[ENOCH_ACTION]{...}[/ENOCH_ACTION]``
blocks out of the returned plain text.

Environment variables (all optional):

    ENOCH_MUSE_MAILBOX        mailbox base dir; default ``<cwd>/.enoch/muse_mailbox``
    ENOCH_MUSE_POLL_SECONDS   outbox poll interval; default ``10``
    ENOCH_MUSE_TIMEOUT        self-imposed deadline (seconds) when the
                              harness passes no ``timeout_seconds``
                              (conversation turns); default ``1800``
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from our_ark_provider_kit.contracts import (
    AgentIdentity,
    AgentRuntime,  # noqa: F401  (re-exported so callers can isinstance-check)
    AgentRuntimeError,
    AgentRuntimeTimedOut,
    ProviderCapabilities,
    ProviderHealth,
    RuntimeExecutionControl,
    RuntimeProgress,
    RuntimeResult,
    RuntimeResultLike,
)

__all__ = [
    "MuseRuntime",
    "MuseModelOption",
    "create_provider",
    "mailbox_configured",
    "mailbox_base",
]


# ---------------------------------------------------------------------------
# Mailbox layout
# ---------------------------------------------------------------------------


def mailbox_base() -> Path:
    """Resolve the mailbox base directory (not created as a side effect)."""
    raw = os.environ.get("ENOCH_MUSE_MAILBOX", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.cwd() / ".enoch" / "muse_mailbox"


def _ensure_private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass
    return path


def mailbox_configured() -> bool:
    """``supports`` gate for the ``OUR_ARK_PROVIDERS`` descriptor.

    Called with no arguments by Enoch's provider registry. Returns True
    when the mailbox directory can be created and written to.
    """
    try:
        base = _ensure_private_dir(mailbox_base())
        _ensure_private_dir(base / "inbox")
        _ensure_private_dir(base / "outbox")
        return os.access(base, os.W_OK)
    except OSError:
        return False


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON atomically (tmp file + rename) with 0600 permissions."""
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex[:8]}")
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


def _request_id(control: RuntimeExecutionControl) -> str:
    """Use the harness-supplied request id when present (idempotency)."""
    candidate = (control.request_id or "").strip()
    return candidate or uuid.uuid4().hex


def _identity_dict(identity: AgentIdentity) -> dict[str, str]:
    return {
        "name": str(getattr(identity, "name", "") or ""),
        "mission": str(getattr(identity, "mission", "") or ""),
    }


def _coerce_control(
    *,
    session_key: str = "",
    cancellation_event: threading.Event | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
    execution: RuntimeExecutionControl | None = None,
) -> RuntimeExecutionControl:
    """Build a RuntimeExecutionControl from legacy kwargs when the harness
    calls the provider without the modern ``execution`` keyword."""
    if execution is not None:
        return execution

    adapted: Callable[[RuntimeProgress], None] | None = None
    if progress_callback is not None:
        def adapted(progress: RuntimeProgress) -> None:
            progress_callback(progress.elapsed_seconds, progress.stage)

    return RuntimeExecutionControl(
        session_key=session_key,
        cancellation_event=cancellation_event,
        progress_callback=adapted,
    )


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MuseModelOption:
    """Single static model option; the registry UI only needs ``.slug``."""

    slug: str = "muse-mailbox"
    label: str = "Muse (mailbox)"


class MuseRuntime:
    """Enoch runtime provider that bridges to Muse via a file mailbox."""

    name = "muse"
    provider_kind = "runtime"
    config_section = "muse"

    capabilities = ProviderCapabilities(
        provider_kind="runtime",
        capabilities=frozenset({"runtime.respond", "runtime.execute"}),
    )

    def __init__(self, root: Path | None = None) -> None:
        self._root = root

    # -- AgentRuntime contract ----------------------------------------

    def respond(
        self,
        identity: AgentIdentity,
        message: str,
        cwd: Path | None = None,
        progress_callback: Callable[[int, str], None] | None = None,
        session_key: str = "",
        image_paths: Sequence[Path] = (),
        execution: RuntimeExecutionControl | None = None,
    ) -> RuntimeResultLike:
        control = _coerce_control(
            session_key=session_key,
            progress_callback=progress_callback,
            execution=execution,
        )
        # Conformance: a pre-cancelled / timed-out execution must raise
        # before any work (in particular, before touching the mailbox).
        control.raise_if_stopped()
        request_id = _request_id(control)
        self._drop_request(
            request_id=request_id,
            kind="respond",
            identity=identity,
            message=message,
            session_key=control.session_key or session_key,
            sandbox="read-only",
            cwd=cwd,
            state_root=self._root,
            image_paths=image_paths,
        )
        text = self._await_reply(request_id, control, sandbox="read-only")
        control.raise_if_stopped()
        return RuntimeResult(final_text=text, session_id=request_id)

    def act_in_session(
        self,
        identity: AgentIdentity,
        message: str,
        cwd: Path | None = None,
        progress_callback: Callable[[int, str], None] | None = None,
        sandbox: str = "",
        session_key: str = "",
        cancellation_event: threading.Event | None = None,
        state_root: Path | None = None,
        execution: RuntimeExecutionControl | None = None,
    ) -> RuntimeResultLike:
        control = _coerce_control(
            session_key=session_key,
            cancellation_event=cancellation_event,
            progress_callback=progress_callback,
            execution=execution,
        )
        control.raise_if_stopped()
        request_id = _request_id(control)
        effective_sandbox = sandbox or "workspace-write"
        self._drop_request(
            request_id=request_id,
            kind="act_in_session",
            identity=identity,
            message=message,
            session_key=control.session_key or session_key,
            sandbox=effective_sandbox,
            cwd=cwd,
            state_root=state_root if state_root is not None else self._root,
            image_paths=(),
        )
        text = self._await_reply(request_id, control, sandbox=effective_sandbox)
        control.raise_if_stopped()
        return RuntimeResult(final_text=text, session_id=request_id)

    def model_summary(self, root: Path | None = None) -> str:
        return "Muse (mailbox runtime provider)"

    def model_options(self) -> tuple[Any, ...]:
        return (MuseModelOption(),)

    def reset_usage(self) -> None:
        # The mailbox bridge keeps no usage accounting.
        return None

    def health(self, root: Path | None = None) -> ProviderHealth:
        base = mailbox_base()
        try:
            ok = mailbox_configured()
            detail = (
                f"mailbox {base} writable" if ok else f"mailbox {base} not writable"
            )
        except OSError as exc:  # pragma: no cover - defensive
            ok = False
            detail = f"mailbox check failed: {exc}"
        return ProviderHealth(
            name="muse mailbox",
            passed=ok,
            command="mailbox check",
            summary=detail,
        )

    # -- Mailbox internals --------------------------------------------

    def _mailbox(self) -> tuple[Path, Path]:
        base = _ensure_private_dir(mailbox_base())
        return _ensure_private_dir(base / "inbox"), _ensure_private_dir(base / "outbox")

    def _drop_request(
        self,
        *,
        request_id: str,
        kind: str,
        identity: AgentIdentity,
        message: str,
        session_key: str,
        sandbox: str,
        cwd: Path | None,
        state_root: Path | None,
        image_paths: Sequence[Path],
    ) -> None:
        inbox, _ = self._mailbox()
        payload = {
            "request_id": request_id,
            "kind": kind,
            "identity": _identity_dict(identity),
            "message": message,
            "session_key": session_key,
            "sandbox": sandbox,
            "cwd": str(cwd) if cwd else "",
            "state_root": str(state_root) if state_root else "",
            "image_paths": [str(p) for p in (image_paths or ())],
            "created_at": time.time(),
        }
        _atomic_write_json(inbox / f"{request_id}.json", payload)

    def _await_reply(
        self,
        request_id: str,
        control: RuntimeExecutionControl,
        *,
        sandbox: str,
    ) -> str:
        _, outbox = self._mailbox()
        reply_path = outbox / f"{request_id}.json"
        # Conversation turns carry no harness-side timeout, so the provider
        # self-imposes one (same pattern as the claude provider).
        timeout = control.timeout_seconds or int(
            os.environ.get("ENOCH_MUSE_TIMEOUT", "1800")
        )
        poll = float(os.environ.get("ENOCH_MUSE_POLL_SECONDS", "10"))
        deadline = time.monotonic() + timeout
        last_progress = control.started_at_monotonic
        while True:
            # Honors cancellation, timeout events, and the epoch monitor.
            control.raise_if_stopped()
            reply = self._read_reply(reply_path)
            if reply is not None:
                return reply
            now = time.monotonic()
            if now >= deadline:
                raise AgentRuntimeTimedOut(
                    f"Muse mailbox wait timed out after {timeout}s "
                    f"(request {request_id})."
                )
            if now - last_progress >= 60:
                control.emit_progress(
                    RuntimeProgress(
                        elapsed_seconds=int(now - control.started_at_monotonic),
                        stage="mailbox-wait",
                        sandbox=sandbox,
                        session_id=request_id,
                    )
                )
                last_progress = now
            time.sleep(min(poll, max(0.1, deadline - now)))

    @staticmethod
    def _read_reply(path: Path) -> str | None:
        try:
            raw = path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            return None
        try:
            payload = json.loads(raw)
        except ValueError:
            # Tolerate transient partial reads; the consumer must still
            # use atomic rename (see scripts/mailbox_consumer_stub.py).
            return None
        if not isinstance(payload, dict):
            return None
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            return None
        return text


def create_provider(root: Path | None = None) -> MuseRuntime:
    """Factory referenced by the ``our_ark.providers`` entry point and the
    ``OUR_ARK_PROVIDERS`` descriptor. Accepts an optional root (the registry
    calls ``factory(root)`` when the factory declares it)."""
    return MuseRuntime(root=root)
