# enoch-muse-runtime

A `muse` **runtime provider** for [Enoch](https://github.com/our-ark/enoch)
(`our-ark/enoch`) — the proof of concept for running Enoch natively with
**Muse as the reasoner (R)**.

## RIPA framing

Under RIPA, an agent is its persistent substrate `P = (I, M, B)` —
identity, memory, body revision — while the execution substrate
`E = (R, H, D)` (reasoner, harness, host) and the interaction surfaces `S`
are independently replaceable. Swapping the reasoner does **not** create a
new agent: Enoch stays Enoch, it just thinks with a different brain.

MuseEnoch is exactly that substitution: `R = Muse`, reached through an
async file **mailbox**, while Enoch's daemon loop, leases, audit
artifacts, and `[ENOCH_ACTION]` text-protocol parsing run natively.
(Muse has no synchronous machine-callable API — no public endpoint, CLI,
or SDK — so the mailbox *is* the machine form of Muse's interface:
files + a scheduled pickup. If Muse ever gains a real API, the provider
interior can become one HTTP call without touching the contract.)

## Repo layout

```
src/our_ark_muse/
  __init__.py   factories + OUR_ARK_PROVIDERS descriptor (route B)
  core.py       MuseRuntime: AgentRuntime contract over the mailbox (R axis)
  chat.py       MuseChatClient: ChatProvider contract over the mailbox (S axis)
scripts/
  mailbox_consumer_stub.py   documents the external-side protocol (stub only)
  mailbox_pending.py         lists inbox requests with no outbox reply yet
  e2e_live_respond.py        live end-to-end: loads runtime.muse via Enoch's
                             registry and runs one blocking respond() turn
  chat_turn.py               drives ONE genuine Enoch conversation turn for a
                             muse-chat message: real P (identity+memory),
                             run_conversation, runtime.muse, chat.muse
tests/
  test_roundtrip.py          round-trip / pre-cancel / timeout tests
  test_chat_roundtrip.py     chat provider receive/send/cursor tests
.gitignore                   excludes mailbox/ (live traffic, never committed)
```

## Registration

**Route A — entry point (active once installed):**
`pyproject.toml` declares
`[project.entry-points."our_ark.providers"] "runtime.muse" =
"our_ark_muse:create_provider"` and `"chat.muse" =
"our_ark_muse.chat:create_provider"`, discovered via `importlib.metadata`.

**Route B — no install needed:** `OUR_ARK_PROVIDERS` in
`src/our_ark_muse/__init__.py` is picked up when `our_ark_muse` is listed
as a `[[runtime_dependencies]]` entry (`import_name = "our_ark_muse"`) in
`genesis.toml`. The `supports` gate enables the provider only when the
mailbox directory is creatable/writable.

Select at runtime with `ENOCH_RUNTIME_PROVIDER=muse` (env wins) or
`/config provider runtime muse`. Do **not** mark it `default=True`.

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `ENOCH_MUSE_MAILBOX` | `<cwd>/.enoch/muse_mailbox` | mailbox base dir (`inbox/`, `outbox/`; 0700, files 0600) |
| `ENOCH_MUSE_POLL_SECONDS` | `10` | outbox poll interval |
| `ENOCH_MUSE_TIMEOUT` | `1800` | self-imposed deadline when the harness passes no `timeout_seconds` (conversation turns) |

Task turns should set Enoch's `[task] timeout_seconds` toward its 7200s
ceiling for mailbox operation.

## Running the tests

```bash
cd ~/workspace/muse-enoch
python3 tests/test_roundtrip.py
```

Tests use stdlib `unittest` only. They import Enoch's provider-kit
contracts from the local source tree
(`~/workspace/enoch-experiment/libraries/provider-kit/src`) — read-only;
nothing in the Enoch checkout is modified.

## Live consumer (bidirectional bridge)

The live loop is a scheduled job (cron id `muse-enoch-mailbox-consumer`,
every 2 minutes) that works both directions:

**R direction (reasoner):** scans `mailbox/inbox/` for requests with no
`outbox/<request_id>.json` reply, reasons over each prompt as Muse, and
atomic-writes the reply (`{"request_id", "text", "replied_at"}`, tmp +
rename, 0600). Empty inbox: the job does nothing and stays silent.

**S direction (surface):** `@enoch` messages from Muse chat are appended
by the chat operator to `mailbox/chat_inbox/<seq>.json` (never answered
by the operator itself — the anti-roleplay guarantee). The job drives one
genuine Enoch turn per new message via `scripts/chat_turn.py` (real P:
identity + memory + `run_conversation` + `runtime.muse`), tracks progress
in `mailbox/chat_cursor.txt`, and delivers `mailbox/chat_outbox/` replies
back into Muse chat verbatim (marked with `<id>.delivered`).

The consumer interval dominates round-trip latency: one chat message can
trigger up to 7 sequential provider calls, so a 2-minute consumer cadence
keeps a full turn comfortably inside the provider's 30-minute
self-imposed deadline.

## Deploying an Enoch instance inside Muse

One prompt is enough. Give Muse an **instance prompt** — the agent's name,
who it is, its mission, and any seed memories — and point it at
[`prompts/deploy-enoch.md`](prompts/deploy-enoch.md). Muse acts as the
deploy agent and hands back a working instance ready to talk.

What the deploy does, concretely:

1. Creates a dedicated agent root with real `enoch init` (never hand-made
   JSON), e.g. `~/workspace/muse-enoch-<slug>/`.
2. Installs the `our_ark_muse` package so entry points `runtime.muse` and
   `chat.muse` resolve through Enoch's real provider registry.
3. Gives the instance its **own mailbox directory** (`inbox/`, `outbox/`,
   `chat_inbox/`, `chat_outbox/`, `chat_cursor.txt`) — never shared
   between instances.
4. Seeds memories through Enoch's real memory API (`remember_memory`),
   not by editing JSON.
5. Runs one real end-to-end smoke turn: a `chat.muse` message in
   `chat_inbox` → `scripts/chat_turn.py` (real identity, real
   `memory_for_prompt`, real `run_conversation` with journal, real
   `runtime.muse`) → reply in `chat_outbox`.
6. Wires the bidirectional consumer (`muse-enoch-mailbox-consumer` cron
   or an equivalent loop) at the instance's mailbox so it keeps serving.

To talk to the instance afterwards: send `@<name> <text>` in Muse chat.
The operator appends your literal text to `chat_inbox` and delivers the
instance's `chat_outbox` reply verbatim — it never answers as the
instance itself (the anti-roleplay guarantee).

Constraints worth knowing: `mailbox/` is live traffic and gitignored;
one mailbox and one cursor per instance, never two consumers on the same
mailbox; `chat_turn.py` is a PoC stand-in for the daemon poll loop, not
the full `EnochApplication.handle_event()`.

## End-to-end verification (2026-09-18)

`scripts/e2e_live_respond.py` loads the provider through Enoch's **real**
registry (`load_provider("runtime", name="muse")`, entry point
`runtime.muse`) and runs one blocking `respond()` turn:

```
available runtime providers: ('codex', 'muse')
loaded: our_ark_muse.core.MuseRuntime
health: ProviderHealth(... passed=True ...)
respond() returned.
session_id: 53030fbb2f1a406e84cae50b0b30f7e0
final_text: Mailbox bridge live: consumer received request ... and answered. Round-trip OK.
```

Provider → `inbox/<id>.json` → consumer → `outbox/<id>.json` →
`respond()` returns the reply text. Full loop verified against the real
Enoch provider contract.

## PoC status and known limits

- [x] `MuseRuntime` satisfies the `AgentRuntime` Protocol (duck-typed;
      `respond` / `act_in_session` / `model_summary` / `model_options` /
      `reset_usage` / `health`, `provider_kind == "runtime"`).
- [x] Conformance-critical behavior: `execution.raise_if_stopped()` is
      called **first**, so pre-cancelled / timed-out executions raise
      `AgentRuntimeCancelled` / `AgentRuntimeTimedOut` without touching
      the mailbox.
- [x] Progress emission (`stage="mailbox-wait"`) every ~60s while polling;
      the epoch monitor is honored via `raise_if_stopped()` each iteration.
- [x] Atomic request writes (tmp + rename, 0600); unique request ids from
      `control.request_id` when the harness supplies one.
- [x] Live consumer: scheduled job `muse-enoch-mailbox-consumer` scans
      `inbox/` every 2 minutes and atomic-writes replies to `outbox/`;
      verified end to end with `scripts/e2e_live_respond.py` (2026-09-18).
- [x] `MuseChatClient` satisfies the `ChatProvider` Protocol
      (`receive` / `send_message` / `edit_message` / `send_read_ack`,
      `provider_kind == "chat"`); registered as entry point `chat.muse`
      and in `OUR_ARK_PROVIDERS`; verified via Enoch's real registry
      `load_provider("chat", name="muse")` (2026-09-18).
- [x] `@enoch` turn driver `scripts/chat_turn.py`: one genuine Enoch
      conversation turn per muse-chat message — real identity
      (`load_body_identity`), real memory (`memory_for_prompt` +
      `remember_memory` via the memory API), real `run_conversation`
      with journal, real `runtime.muse`; verified end to end against a
      real `enoch init` agent root (2026-09-18).
- [x] Consumer cron is now a bidirectional bridge: R direction answers
      runtime requests; S direction drives chat turns and delivers
      `chat_outbox/` replies back into Muse chat verbatim.
      Anti-roleplay rule: the chat operator never answers `@enoch`
      content itself; it only appends to `chat_inbox/` and delivers
      `chat_outbox/` replies.
- [ ] **Latency multiplication**: one chat message can trigger up to 7
      sequential provider calls (`MAX_ACTIONS = 6`); each is a full
      mailbox round-trip (mitigated by the 2-minute consumer cadence).
- [ ] Conversational turns run synchronously and **block the daemon's
      poll loop** while waiting; task turns are thread-isolated and safe.
- [x] ~~The mailbox replaces only the **runtime** provider. A separate
      **chat** provider is still needed if the surface `S` should also be
      Muse chat (the `@enoch` idea) — the two axes are replaced
      independently.~~ **Done 2026-09-18** — `chat.muse` provider +
      `chat_turn.py` + bidirectional consumer cron.
- [x] ~~No live consumer yet: `scripts/mailbox_consumer_stub.py` documents
      the protocol; the scheduled pickup loop that hands prompts to the
      Muse operator is the next step (not built here).~~ **Done
      2026-09-18** — cron `muse-enoch-mailbox-consumer` (2 min) +
      `scripts/mailbox_pending.py`; e2e verified.

## What's next

1. ~~Build the live consumer~~ — done (cron `muse-enoch-mailbox-consumer`).
2. ~~Point an Enoch checkout at the provider and run one real
   `respond()` turn end to end~~ — done 2026-09-18
   (`scripts/e2e_live_respond.py`, via the real registry).
3. ~~Implement the companion **chat** provider for the Muse-chat
   surface~~ — done 2026-09-18 (`chat.muse` + `chat_turn.py` +
   bidirectional cron; `@enoch` routes to real P).
4. Harden: per-`session_key` Muse-side continuity, daemon threading for
   conversational turns, cross-host mailbox.

## Pushing (vault-backed)

This repo is pushed with the `github` workspace skill
(`~/workspace/skills/github/bin/github-push`), which authenticates through
the vault-stored GitHub credential instead of a pasted token:

    ~/workspace/skills/github/bin/github-push --repo . --branch main

It mirrors local commits via the git-database REST API with identical
trees/messages/authors/dates, so local and remote SHAs stay in sync.
