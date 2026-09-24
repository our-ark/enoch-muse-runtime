"""Muse chat provider for Enoch (MuseEnoch PoC).

Implements Enoch's ``ChatProvider`` contract
(``our_ark_provider_kit.contracts``) using a file mailbox as the transport
to the Muse operator::

    surface -> chat_inbox/<seq>.json     (user's @enoch message)
    daemon  -> chat_outbox/<id>.json     (Enoch's reply, via send_message)

This is the surface-axis (S) half of MuseEnoch, symmetric to the runtime
provider in ``core.py``. The daemon's poll loop calls ``receive(cursor)``
and dispatches each ``ChatEvent`` through the genuine conversation path
(``run_conversation`` with real identity/memory); replies come back through
``send_message`` into ``chat_outbox/``, where the delivery loop picks them
up and posts them into Muse chat.

Anti-roleplay guarantee: the assistant sitting in Muse chat never answers
``@enoch`` content itself. It only appends the literal user text to
``chat_inbox/`` (see ``drop_chat_message``) and later delivers the literal
``chat_outbox/`` replies. Both directions are auditable files.

Environment: same ``ENOCH_MUSE_MAILBOX`` base dir as the runtime provider.
"""

from __future__ import annotations

import os
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from our_ark_provider_kit.contracts import (
    Attachment,
    ChatEvent,
    ChatProvider,  # noqa: F401  (re-exported for isinstance checks)
    ChatProviderError,
    ConversationId,
    MessageId,
)

from our_ark_muse.core import _atomic_write_json, _ensure_private_dir, mailbox_base

__all__ = [
    "MuseChatClient",
    "MuseChatConfig",
    "CONVERSATION_ID",
    "create_provider",
    "drop_chat_message",
    "mailbox_chat_configured",
]

#: The single conversation this surface exposes. Muse chat is one shared
#: surface; per-user routing is the delivery layer's job, not the daemon's.
CONVERSATION_ID: ConversationId = "muse-chat"

# Inbound message the daemon is currently handling, as seen by
# ``send_read_ack`` (which Enoch's ``_dispatch_chat_event`` calls first,
# before any reply is generated). ``send_message`` attaches it as
# ``in_reply_to`` so every outbound reply points at the inbound message it
# answers, and a conversation can be threaded by message id.
# Semantics: the value persists until the *next* ack, so progress updates
# ("still working…") stay threaded under the same inbound event. Sends that
# happen with no prior ack (proactive notifications) carry no ``in_reply_to``.
_PENDING_IN_REPLY_TO: ContextVar[str | None] = ContextVar(
    "our_ark_muse_pending_in_reply_to", default=None
)


@dataclass(frozen=True)
class MuseChatConfig:
    conversation_id: ConversationId = CONVERSATION_ID


class MuseChatError(ChatProviderError):
    pass


def _chat_dirs() -> tuple[Path, Path]:
    base = _ensure_private_dir(mailbox_base())
    return (
        _ensure_private_dir(base / "chat_inbox"),
        _ensure_private_dir(base / "chat_outbox"),
    )


def mailbox_chat_configured() -> bool:
    """``supports`` gate for the ``OUR_ARK_PROVIDERS`` descriptor."""
    try:
        inbox, outbox = _chat_dirs()
        return os_access_writable(inbox) and os_access_writable(outbox)
    except OSError:
        return False


def os_access_writable(path: Path) -> bool:
    return os.access(path, os.W_OK)


def _read_json(path: Path) -> dict[str, Any] | None:
    import json

    try:
        raw = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None
    try:
        payload = json.loads(raw)
    except ValueError:
        return None
    return payload if isinstance(payload, dict) else None


def _next_seq(inbox: Path) -> int:
    """Next inbound sequence number. Single-writer assumption (the Muse
    chat router); skips past any existing file on collision."""
    seq = 0
    for child in inbox.iterdir():
        if child.suffix == ".json" and child.stem.isdigit():
            seq = max(seq, int(child.stem))
    return seq + 1


def drop_chat_message(text: str) -> int:
    """Append a user message to the chat inbox. This is the inbound half of
    the @enoch route: the Muse chat operator calls this with the literal
    user text (minus the @enoch prefix) instead of answering it."""
    text = text.strip()
    if not text:
        raise MuseChatError("Cannot drop an empty chat message.")
    inbox, _ = _chat_dirs()
    for _ in range(100):
        seq = _next_seq(inbox)
        path = inbox / f"{seq}.json"
        if path.exists():
            continue
        _atomic_write_json(
            path,
            {"seq": seq, "text": text, "created_at": time.time()},
        )
        return seq
    raise MuseChatError("Could not allocate an inbox sequence number.")


class MuseChatClient:
    """Enoch chat provider bridged to Muse chat via a file mailbox."""

    name = "muse"
    provider_kind = "chat"

    def __init__(
        self,
        config: MuseChatConfig | None = None,
        root: Path | None = None,
    ) -> None:
        self.config = config or MuseChatConfig()
        self._root = root

    # -- ChatProvider contract --------------------------------------

    @property
    def allowed_conversation_id(self) -> ConversationId | None:
        return self.config.conversation_id

    def receive(self, cursor: int | str | None = None) -> list[ChatEvent]:
        inbox, _ = _chat_dirs()
        try:
            after = int(cursor) if cursor is not None else 0
        except (TypeError, ValueError):
            after = 0
        events: list[ChatEvent] = []
        try:
            children = sorted(
                (
                    child
                    for child in inbox.iterdir()
                    if child.suffix == ".json" and child.stem.isdigit()
                ),
                key=lambda child: int(child.stem),
            )
        except OSError as error:
            raise MuseChatError(f"Cannot scan chat inbox: {error}") from error
        for child in children:
            seq = int(child.stem)
            if seq <= after:
                continue
            payload = _read_json(child)
            if payload is None:
                continue
            text = payload.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            events.append(
                ChatEvent(
                    cursor=seq,
                    conversation_id=self.config.conversation_id,
                    message_id=f"chat-{seq}",
                    text=text,
                    replied_text="",
                    raw={"seq": seq, "source": "muse-chat"},
                    attachments=(),
                )
            )
        if not events:
            # Idle pacing: Enoch's daemon calls receive() in a hot poll loop
            # with no sleep of its own. A short pause here sets the idle
            # cadence instead of spinning on directory scans.
            time.sleep(2)
        return events

    def send_message(
        self,
        conversation_id: ConversationId,
        text: str,
    ) -> MessageId | None:
        _, outbox = _chat_dirs()
        message_id = uuid.uuid4().hex
        payload: dict[str, Any] = {
            "message_id": message_id,
            "conversation_id": str(conversation_id),
            "text": text,
            "created_at": time.time(),
        }
        reply_to = _PENDING_IN_REPLY_TO.get()
        if reply_to:
            payload["in_reply_to"] = reply_to
        _atomic_write_json(outbox / f"{message_id}.json", payload)
        return message_id

    def edit_message(
        self,
        conversation_id: ConversationId,
        message_id: MessageId,
        text: str,
    ) -> None:
        # The mailbox is append-only; an edit is delivered as a new message
        # that references the original. The delivery layer renders it.
        _, outbox = _chat_dirs()
        edit_id = uuid.uuid4().hex
        _atomic_write_json(
            outbox / f"{edit_id}.json",
            {
                "message_id": edit_id,
                "edit_of": str(message_id),
                "conversation_id": str(conversation_id),
                "text": text,
                "created_at": time.time(),
            },
        )

    def send_read_ack(
        self,
        conversation_id: ConversationId,
        message_id: MessageId,
    ) -> None:
        # Record the ack where the delivery layer can surface it (e.g. a
        # reaction in Muse chat). Best-effort; never fails the turn.
        # Also tracks "which inbound message is being handled" so that
        # send_message can thread replies via in_reply_to.
        _PENDING_IN_REPLY_TO.set(str(message_id))
        inbox, _ = _chat_dirs()
        try:
            _atomic_write_json(
                inbox / f".ack-{message_id}.json",
                {
                    "ack": str(message_id),
                    "conversation_id": str(conversation_id),
                    "created_at": time.time(),
                },
            )
        except OSError:
            pass


def create_provider(root: Path | None = None) -> MuseChatClient:
    """Factory referenced by the ``our_ark.providers`` entry point and the
    ``OUR_ARK_PROVIDERS`` descriptor."""
    return MuseChatClient(root=root)
