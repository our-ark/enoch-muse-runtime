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
2. Both Muse factories resolve through Enoch's real registry, using the
   managed source launcher or a normal package installation. Importability
   alone is not enough; never copy egg-info from another instance.
3. The instance has its **own mailbox directory** (never shared between
   instances): `<mailbox>/inbox`, `<mailbox>/outbox`, `<mailbox>/chat_inbox`,
   `<mailbox>/chat_outbox`. The chat cursor is daemon-managed
   (`<agent_root>/.enoch/channels/muse/cursor.json`); there is no
   `chat_cursor.txt` anymore.
4. Seed memories from the instance prompt are written through Enoch's real
   memory API (`remember_memory`), not by editing JSON by hand.
5. One real end-to-end turn has succeeded: a `chat.muse` message in
   `chat_inbox` → the instance's own daemon (`python -m enoch.agent`,
   started via `scripts/run_enoch_daemon.sh` with `ENOCH_AGENT_ROOT` /
   `ENOCH_MUSE_MAILBOX` pointed at this instance) picks it up in its poll
   loop → genuine Enoch turn (real identity, real `memory_for_prompt`,
   real `run_conversation` with journal, real `runtime.muse`) → reply in
   `chat_outbox`.
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

Use Python 3.11+, Git and a POSIX host in Muse's workspace. The documented
compatible Enoch body revision is
`66781e209962bcce6d5254e50d05f000ac914668`; use a dedicated checkout at that
revision for a new deployment. If the requested instance already exists,
inspect and report it first; preserve its root and memory rather than creating
a replacement or resetting its state.

1. **Read the repo first.** [Development](../docs/development.md) (provider
   registration), [mailbox protocol](../docs/mailbox-protocol.md) (environment
   variables and consumer duties), [operations](../docs/operations.md),
   `src/our_ark_muse/core.py` (mailbox protocol, `ENOCH_MUSE_MAILBOX`,
   `ENOCH_MUSE_POLL_SECONDS`, `ENOCH_MUSE_TIMEOUT`), `src/our_ark_muse/chat.py`
   (`chat_inbox/<seq>.json` in, `chat_outbox/<id>.json` out),
   `scripts/run_enoch_daemon.sh` (daemon launcher; `ENOCH_AGENT_ROOT`,
   `ENOCH_MUSE_MAILBOX`, `ENOCH_MUSE_REPO`, `ENOCH_SRC` overrides).
2. **Create the agent root** with real `enoch init` at `agent_root`. Verify
   `.enoch/` exists and `load_body_identity` returns the identity. Never
   reuse another instance's root.
3. **Configure and verify the provider** using `scripts/muse_instance.py
   --root <agent_root> --enoch-src <enoch_checkout> --mailbox <mailbox>
   configure`, then the same command with `check` instead of `configure`.
   This registers source factories through Enoch's public registry API and
   persists both Muse bindings plus the mailbox in private config. It changes
   no body files. Other Enoch entry points need normal package installation;
   do not manufacture/copy registration metadata or edit genesis.toml to make
   a frozen body pass. See `docs/operations.md`.
4. **Seed memory** via the memory API only. Then verify with
   `memory_for_prompt()` that the seed is visible to the prompt builder.
   An immediate recall reply can use conversation context; verify the stored
   record through the memory API when checking persistence.
5. **Smoke test**: start the instance's daemon with
   `ENOCH_AGENT_ROOT=<agent_root> ENOCH_MUSE_MAILBOX=<mailbox> bash
   scripts/run_enoch_daemon.sh` (with `ENOCH_SRC` set to the body source),
   or use `muse_instance.py --detach daemon`. Keep the returned attempt
   directory: stdout/stderr and observed exit status must not be overwritten.
   Drop one message into `chat_inbox` with
   `drop_chat_message`, and confirm a reply lands in `chat_outbox` and the
   conversation journal was written under
   `<agent_root>/.enoch/conversation/`. The daemon owns the S direction
   end-to-end; `scripts/chat_turn.py` is retired from the live loop (kept
   for debugging only) and must not be used here.
6. **Wire continuous service**: point the `muse-enoch-mailbox-consumer` cron
   (or a per-instance loop) at this mailbox. The cron supervises the daemon
   via the mailbox pidfile and serves the R direction; the chat cursor is
   daemon-managed, so there is no `chat_cursor.txt` to wire up.
   Mark any test messages already processed so the consumer never replays
   them (cursor + `.delivered` markers on test outbox files).
   Use the managed launcher for research workers too. If a worker disappears,
   retain its logs and inspect ownership; do not simply rerun and advance the
   epoch. `recover <task-id>` refuses live/unknown owners and pauses the task
   through Enoch's native API; a subsequent run uses fresh output directories.
   Missing exit evidence is unknown, not proof of SIGKILL or success.
7. **Report back**: instance name, agent root, mailbox, what the smoke-test
   turn asked and what Enoch replied (verbatim), and how to talk to it
   (`@<name>` / drop into `chat_inbox`).

## Hard constraints

- `mailbox/` is live traffic: it is gitignored and must never be committed.
- Never answer as the instance yourself. When the user later sends
  `@<name> <text>`: write their literal text to `chat_inbox`, ack briefly,
  and forward the instance's `chat_outbox` reply verbatim, clearly labeled.
  You are the deployer/operator, not the agent.
- `scripts/chat_turn.py` is retired from the live loop (debug use only).
  The S direction is owned by the instance's own daemon
  (`python -m enoch.agent` via `scripts/run_enoch_daemon.sh`), which runs
  the full `handle_event()` path: receipts, daemon epochs,
  `DaemonEffectFence`, and real `[ENOCH_ACTION]` execution. Do not claim
  production readiness beyond what the daemon actually wires; say what is
  PoC if asked.
- One mailbox per instance. One cursor per instance. Never point two
  consumers at the same mailbox.
- Git: author `Muse <noreply@local>`; push only through the workspace
  `github` skill (`bin/github-push`), re-reading its `SKILL.md` before
  every push. Never paste or store tokens in chat, files, or the repo.
