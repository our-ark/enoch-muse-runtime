#!/usr/bin/env python3
"""Drive ONE genuine Enoch conversation turn for a muse-chat message.

This is the PoC stand-in for the daemon's poll loop (``run_once`` ->
``handle_event`` -> ``_dispatch_chat_event``). It exercises the real
machinery against a real agent root (real P):

  chat.muse receive()          -- real ChatProvider contract, real inbox
  load_body_identity()         -- real identity (name/mission/generation)
  memory_for_prompt()          -- real long-term memory via the memory API
  conversation_turn_prompt()   -- the daemon's real prompt construction
  run_conversation()           -- the real journal-persisted action engine
  runtime.muse respond()       -- real R via the mailbox (Muse reasons)
  extract_memory_requests()    -- real memory-write path via remember_memory
  chat.muse send_message()     -- real reply into chat_outbox

What it does NOT do (daemon-only duties, out of scope): inbox
receipts (begin/complete_event), daemon epochs, effect-fence
authorization, lifecycle/task workers. Model-issued [ENOCH_ACTION]
blocks inside a conversational turn are reported, not executed;
user-issued slash commands (/help, /status, /do, ...) ARE dispatched
through Enoch's real registered-command table via
EnochApplication._dispatch_registered_command.

Usage:
    ENOCH_MUSE_MAILBOX=~/workspace/muse-enoch/mailbox \\
    ENOCH_AGENT_ROOT=~/workspace/muse-enoch-agent \\
    PYTHONPATH=<enoch>/src:<libs...> python3 scripts/chat_turn.py

The runtime request it emits must be answered by the Muse consumer
(cron or manual) while this script waits, exactly like e2e_live_respond.py.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from enoch.app.conversation import (
    ActionResult,
    ConversationAction,
    ConversationJournal,
    run_conversation,
)
from enoch.app.core import (
    EnochApplication,
    _chat_provider_name,
    _with_replied_text_context,
)
from enoch.app.parsing import parse_chat_command
from enoch.identity import identity_file_path, load_body_identity
from enoch.memory.prompt import memory_for_prompt
from enoch.memory.store import remember_memory
from enoch.prompt_append import (
    conversation_turn_prompt,
    extract_memory_requests,
    startup_context_note,
)
from enoch.providers.registry import load_provider
from enoch.providers.runtime import invoke_runtime_respond

AGENT_ROOT = Path(
    os.environ.get("ENOCH_AGENT_ROOT", str(Path.home() / "workspace/muse-enoch-agent"))
)
#: Only process chat events with seq greater than this (daemon offset
#: equivalent). The cron worker passes the last fully-processed seq.
CHAT_AFTER_CURSOR = int(os.environ.get("CHAT_AFTER_CURSOR", "0") or 0)


def main() -> int:
    root = AGENT_ROOT
    if not (root / ".agent" / "instance.yaml").exists():
        print(f"error: {root} is not an initialized Enoch agent root", flush=True)
        return 2

    chat = load_provider("chat", name="muse")
    events = [
        event
        for event in chat.receive()
        if int(event.cursor) > CHAT_AFTER_CURSOR
    ]
    if not events:
        print("no new chat events.", flush=True)
        return 0
    event = events[0]
    print(f"event cursor={event.cursor} conversation={event.conversation_id}", flush=True)
    print(f"user text: {event.text[:120]}", flush=True)

    identity = load_body_identity()
    identity_path = identity_file_path(root)
    request_id = uuid.uuid4().hex
    session_key = f"muse-chat:{event.conversation_id}"
    runtime = load_provider("runtime", name="muse")

    # Real slash-command dispatch (mirrors
    # EnochApplication._dispatch_chat_event): a registered command
    # (/help, /status, /do, ...) is executed by Enoch's real command
    # table instead of being treated as chat text. Unknown commands
    # fall through to the conversational turn, exactly like the daemon.
    command, argument = parse_chat_command(event.text)
    if command:
        app = EnochApplication(
            identity=identity, root=root, client=chat, runtime=runtime
        )
        work_text = _with_replied_text_context(
            event.text,
            event.replied_text,
            provider_name=_chat_provider_name(chat),
        )
        command_reply = app._dispatch_registered_command(
            event, command, argument, event.text, work_text
        )
        if command_reply is not None:
            message_id = chat.send_message(event.conversation_id, command_reply)
            print(
                f"registered command {command} executed by real Enoch dispatch "
                f"(message_id={message_id}).",
                flush=True,
            )
            print(f"processed_cursor={event.cursor}", flush=True)
            print("---- reply ----", flush=True)
            print(command_reply[:2000], flush=True)
            return 0
        print(
            f"unknown command {command}; falling through to conversational turn.",
            flush=True,
        )

    memory_context = memory_for_prompt(
        root, identity=identity, identity_path=identity_path
    )
    base_prompt = "\n\n".join(
        [
            startup_context_note(memory_context),
            "Current request:",
            conversation_turn_prompt(event.text, command_prefix="/"),
        ]
    )
    print(f"prompt built from real P ({len(base_prompt)} chars).", flush=True)

    journal = ConversationJournal(root, f"muse-chat:{request_id}")

    def respond(feedback: str) -> str:
        prompt = base_prompt
        if feedback:
            prompt = base_prompt + "\n\n" + feedback
        result = invoke_runtime_respond(
            runtime,
            identity,
            prompt,
            cwd=root,
        )
        return result.final_text

    def execute(action: ConversationAction, index: int) -> ActionResult:
        # PoC boundary: the driver does not execute model-issued actions.
        # Reported honestly instead of silently skipped.
        return ActionResult(
            f"Action '{action.command}' was not executed: the PoC turn driver "
            "does not run command effects (daemon-only).",
            stop=False,
        )

    def persist(fn, *args, **kwargs):  # noqa: ANN001,ANN202
        return fn(*args, **kwargs)

    def finalize(reply: str) -> str:
        # Same memory-write path as the daemon's _finish_conversation_reply.
        memory_result = extract_memory_requests(reply)
        reply = memory_result.visible_reply
        notes = []
        for request in memory_result.requests:
            try:
                remember_memory(request, root=root)
                notes.append(f"remembered: {request[:80]}")
            except ValueError as error:
                notes.append(f"memory rejected: {error}")
        memory_note = "\n".join(notes)
        return "\n\n".join(part for part in [reply, memory_note] if part)

    reply = run_conversation(
        journal=journal, respond=respond, execute=execute, persist=persist,
        finalize=finalize,
    )
    message_id = chat.send_message(event.conversation_id, reply)
    print(f"reply sent to chat_outbox (message_id={message_id}).", flush=True)
    print(f"processed_cursor={event.cursor}", flush=True)
    print("---- reply ----", flush=True)
    print(reply[:500], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
