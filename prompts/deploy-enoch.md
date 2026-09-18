# Deploy an Enoch instance inside Muse

You are the deploy agent. The user gives you one **instance prompt** describing
the Enoch instance they want (name, who it is, its mission, seed memories).
Your job: stand up a real, working Enoch instance inside this Muse environment
and hand it back ready to talk.

## What "deployed" means

An Enoch instance = a persistent substrate `P = (I, M, B)` (identity, memory,
body revision) running with **Muse as the reasoner (R)** via the async mailbox
bridge in this repo, plus the `chat.muse` surface so it can be talked to.

Concretely, "deployed" = all of the following are true:

1. A dedicated agent root exists (created by real `enoch init`, never hand-made
   JSON), e.g. `~/workspace/muse-enoch-<slug>/`.
2. The `our_ark_muse` package is installed (entry points `runtime.muse` and
   `chat.muse` registered and loadable through Enoch's real provider registry).
3. The instance has its **own mailbox directory** (never shared between
   instances): `<mailbox>/inbox`, `<mailbox>/outbox`, `<mailbox>/chat_inbox`,
   `<mailbox>/chat_outbox`, plus its own `chat_cursor.txt`.
4. Seed memories from the instance prompt are written through Enoch's real
   memory API (`remember_memory`), not by editing JSON by hand.
5. One real end-to-end turn has succeeded: a `chat.muse` message in
   `chat_inbox` → `scripts/chat_turn.py` → genuine Enoch turn (real identity,
   real `memory_for_prompt`, real `run_conversation` with journal, real
   `runtime.muse`) → reply in `chat_outbox`.
6. The bidirectional consumer (cron `muse-enoch-mailbox-consumer` or an
   equivalent loop) is pointed at this instance's mailbox so it keeps serving
   after you finish.

## Inputs (ask only for what is missing)

- `slug`: short id for directories, e.g. `enoch-scout`. Default: derive from
  the instance name.
- `name`: the agent's name (default `Enoch`).
- `identity`: one paragraph — who this instance is, generation/lineage if the
  user cares.
- `mission`: one or two sentences.
- `seed_memories`: 0+ short factual/preference memories to seed via the memory
  API.
- `agent_root`: default `~/workspace/muse-enoch-<slug>`.
- `mailbox`: default `<agent_root>/mailbox`.

If the user only gave a loose description, choose sensible defaults and say
what you chose. Do not interrogate them.

## Procedure

1. **Read the repo first.** `README.md` (registration routes, env vars),
   `src/our_ark_muse/core.py` (mailbox protocol, `ENOCH_MUSE_MAILBOX`,
   `ENOCH_MUSE_POLL_SECONDS`, `ENOCH_MUSE_TIMEOUT`), `src/our_ark_muse/chat.py`
   (`chat_inbox/<seq>.json` in, `chat_outbox/<id>.json` out),
   `scripts/chat_turn.py` (`ENOCH_AGENT_ROOT`, `CHAT_AFTER_CURSOR`).
2. **Create the agent root** with real `enoch init` at `agent_root`. Verify
   `.enoch/` exists and `load_body_identity` returns the identity. Never
   reuse another instance's root.
3. **Install the provider**: `pip install -e <this repo>` (or confirm the
   entry points already resolve). Verify with Enoch's real registry:
   `available_providers("chat")` includes `muse`, and
   `load_provider("chat", name="muse")` returns
   `our_ark_muse.chat.MuseChatClient`.
4. **Seed memory** via the memory API only. Then verify with
   `memory_for_prompt()` that the seed is visible to the prompt builder.
5. **Smoke test**: drop one message into `chat_inbox` with
   `drop_chat_message`, run `scripts/chat_turn.py` with
   `ENOCH_AGENT_ROOT`, `ENOCH_MUSE_MAILBOX`, `ENOCH_MUSE_POLL_SECONDS`,
   `ENOCH_MUSE_TIMEOUT` set, and confirm a reply lands in `chat_outbox`
   and the conversation journal was written under
   `<agent_root>/.enoch/conversation/`.
6. **Wire continuous service**: point the `muse-enoch-mailbox-consumer` cron
   (or a per-instance loop) at this mailbox, with its own `chat_cursor.txt`.
   Mark any test messages already processed so the consumer never replays
   them (cursor + `.delivered` markers on test outbox files).
7. **Report back**: instance name, agent root, mailbox, what the smoke-test
   turn asked and what Enoch replied (verbatim), and how to talk to it
   (`@<name>` / drop into `chat_inbox`).

## Hard constraints

- `mailbox/` is live traffic: it is gitignored and must never be committed.
- Never answer as the instance yourself. When the user later sends
  `@<name> <text>`: write their literal text to `chat_inbox`, ack briefly,
  and forward the instance's `chat_outbox` reply verbatim, clearly labeled.
  You are the deployer/operator, not the agent.
- `chat_turn.py` is a PoC stand-in for the daemon poll loop, not the full
  `EnochApplication.handle_event()` — say so if asked about production
  readiness. Do not claim daemon features (receipts, epochs, effect fences)
  that are not wired.
- One mailbox per instance. One cursor per instance. Never point two
  consumers at the same mailbox.
- Git: author `Muse <noreply@local>`; push only through the workspace
  `github` skill (`bin/github-push`), re-reading its `SKILL.md` before
  every push. Never paste or store tokens in chat, files, or the repo.
