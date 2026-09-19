# Architecture and RIPA

[Back to the user guide](../README.md) · [Operations](operations.md) · [Mailbox protocol](mailbox-protocol.md)

## RIPA framing

Under RIPA, an agent is its persistent substrate `P = (I, M, B)` —
identity, memory, body revision — while the execution substrate
`E = (R, H, D)` (reasoner, harness, host) and the interaction surfaces `S`
are replaceable under the continuity and authority checks. An authorized
reasoner replacement can preserve the installed agent's lineage; it does not
imply identical behavior or capability.

This adapter realizes that substitution: `R = Muse`, reached through an
async file **mailbox**, while Enoch's daemon loop, leases, audit
artifacts, and `[ENOCH_ACTION]` text-protocol parsing run natively.
The evaluated deployment used no synchronous Muse API. Its consumer read and
answered actual mailbox requests through a live Muse operator conversation.

| RIPA component | In this deployment |
|---|---|
| Persistent substrate `P = (I, M, B)` | Enoch's installed identity, durable memory and versioned executable body |
| Reasoner `R` | Muse |
| Harness `H` | Enoch's daemon/runtime integration plus the mailbox bridge and consumer |
| Host `D` | Muse's cloud environment |
| Interaction surface `S` | Muse chat, routed through `@Enoch` |

See the [paper](https://arxiv.org/abs/2609.00546) for the lifecycle contract,
six continuity invariants and migration protocol, and the
[artifact guide](research-artifacts.md) for the tested bindings and
evidence boundaries.

## Deployment lifecycle

Give a suitably configured Muse operator an **instance prompt** — the agent's name,
who it is, its mission, and any seed memories — and point it at
[`prompts/deploy-enoch.md`](../prompts/deploy-enoch.md). Muse acts as the
deploy agent; verify the resulting bindings and smoke turn before use. Access
to the host and a running consumer are prerequisites, not supplied by a clone.

Example instance prompt:

> Deploy an Enoch instance named **Scout** — a curious research
> assistant (Generation 4, descendant of Enoch). Mission: watch for new
> papers on persistent AI agents and summarize the interesting ones
> every morning. Seed memories: the user prefers replies in Chinese;
> the user's timezone is America/Los_Angeles.

What the deploy does, concretely:

1. Creates a dedicated agent root with real `enoch init` (never hand-made
   JSON), e.g. `~/workspace/muse-enoch-<slug>/`.
2. Configures the instance through `scripts/muse_instance.py`, which
   registers the source factories through Enoch's real provider registry
   and persists the Muse bindings for later migration exports.
3. Gives the instance its **own mailbox directory** (`inbox/`, `outbox/`,
   `chat_inbox/`, `chat_outbox/`) — never shared
   between instances.
4. Seeds memories through Enoch's real memory API (`remember_memory`),
   not by editing JSON.
5. Runs one real end-to-end smoke turn: a `chat.muse` message in
   `chat_inbox` → Enoch's own daemon (`python -m enoch.agent`,
   full `handle_event()`: receipts, daemon epoch, effect-fence
   authorization, real `run_conversation` with journal, real
   `runtime.muse`) → reply in `chat_outbox`.
6. Wires the bidirectional consumer (`muse-enoch-mailbox-consumer` cron
   or an equivalent loop) at the instance's mailbox: it supervises the
   daemon process (restarts if dead), answers `runtime.muse` reasoning
   requests (R direction), and delivers `chat_outbox` replies.

Constraints worth knowing: `mailbox/` is live traffic and gitignored;
one mailbox per instance. The managed launcher rejects duplicate starts
before they acquire another daemon epoch. The daemon's chat cursor lives in
`.enoch/channels/muse/cursor.json` — the legacy `chat_cursor.txt`
is retired. Slash commands (`/help`, `/status`, `/do`, …) go through
Enoch's real registered-command table via the genuine
`_dispatch_chat_event` path. Note the behavior change vs the earlier
one-shot driver: model-issued `[ENOCH_ACTION]` blocks are now
**executed for real** under `DaemonEffectFence` (previously
report-only), and `[ENOCH_MEMORY_REQUEST]` is persisted to Enoch's
real memory.

## Known limits

- **Latency multiplication**: one chat message can trigger up to 7
  sequential provider calls (`MAX_ACTIONS = 6`); each is a full mailbox
  round-trip (mitigated by the 1-minute consumer cadence).
- **Poll-loop hold**: conversational turns run on the daemon's poll-loop
  thread and each `runtime.muse` call waits on the mailbox for minutes,
  so a long turn (up to 7 sequential calls) holds the poll loop for tens
  of minutes, starving other events, scheduled jobs, and lifecycle work
  meanwhile. Task turns run in separate threads; this does not eliminate
  service availability or external side-effect risks.
- **Real side effects**: model-issued `[ENOCH_ACTION]` blocks are now
  executed for real under `DaemonEffectFence`, and
  `[ENOCH_MEMORY_REQUEST]` persists to Enoch's real memory. The fence is
  Enoch's own authorization mechanism; review its capability grants
  before exposing the instance to untrusted input.
- The managed supervisor captures child exits and supports explicit recovery
  of a dead worker through Enoch's task API. Detaching cannot guarantee survival
  of a host/container shutdown; there is no systemd/launchd unit yet.

## What's next

- Per-`session_key` Muse-side continuity.
- Daemon threading for conversational turns (stop holding the poll loop
  for tens of minutes).
- Cross-host mailbox (beyond one VM).
