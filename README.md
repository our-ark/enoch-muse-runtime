# enoch-muse-runtime

A `muse` **runtime provider** for [Enoch](https://github.com/our-ark/enoch)
(`our-ark/enoch`) — the proof of concept for running Enoch on Muse's
execution substrate: **Muse as the reasoner (R)**, **Muse chat as the
surface (S)**, the async mailbox bridge plus consumer loop as the
**harness (H)** glue, all **hosted (D)** in the Muse environment.

## RIPA framing ([paper](https://arxiv.org/abs/2609.00546))

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

## Deploying an Enoch instance inside Muse

One prompt is enough. Give Muse an **instance prompt** — the agent's name,
who it is, its mission, and any seed memories — and point it at
[`prompts/deploy-enoch.md`](prompts/deploy-enoch.md). Muse acts as the
deploy agent and hands back a working instance ready to talk.

Example instance prompt:

> Deploy an Enoch instance named **Scout** — a curious research
> assistant (Generation 4, descendant of Enoch). Mission: watch for new
> papers on persistent AI agents and summarize the interesting ones
> every morning. Seed memories: the user prefers replies in Chinese;
> the user's timezone is America/Los_Angeles.

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
   `chat_inbox` → Enoch's own daemon (`python -m enoch.agent`,
   full `handle_event()`: receipts, daemon epoch, effect-fence
   authorization, real `run_conversation` with journal, real
   `runtime.muse`) → reply in `chat_outbox`.
6. Wires the bidirectional consumer (`muse-enoch-mailbox-consumer` cron
   or an equivalent loop) at the instance's mailbox: it supervises the
   daemon process (restarts if dead), answers `runtime.muse` reasoning
   requests (R direction), and delivers `chat_outbox` replies.

Constraints worth knowing: `mailbox/` is live traffic and gitignored;
one mailbox per instance, never two daemons on the same mailbox
(daemon epoch is last-writer-wins, so a duplicate start retires the
older process). The daemon's chat cursor lives in
`.enoch/channels/muse/cursor.json` — the legacy `chat_cursor.txt`
is retired. Slash commands (`/help`, `/status`, `/do`, …) go through
Enoch's real registered-command table via the genuine
`_dispatch_chat_event` path. Note the behavior change vs the earlier
one-shot driver: model-issued `[ENOCH_ACTION]` blocks are now
**executed for real** under `DaemonEffectFence` (previously
report-only), and `[ENOCH_MEMORY_REQUEST]` is persisted to Enoch's
real memory.

## Using Enoch in Muse

**Chat:** send `@<name> <text>` in Muse chat. The operator appends your
literal text to the instance's `chat_inbox` and delivers its
`chat_outbox` reply verbatim — it never answers as the instance itself
(the anti-roleplay guarantee).

**Slash commands** (`/help`, `/status`, `/do`, …) are executed through
Enoch's real registered-command table, the same dispatch the daemon
uses. Unknown `/commands` fall through to normal conversation.

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
  chat_turn.py               legacy one-shot turn driver (retired from the
                             live loop; the daemon now owns S). Kept for
                             manual debugging.
  run_enoch_daemon.sh        starts Enoch's own daemon
                             (`python -m enoch.agent`) for an agent root:
                             env, PYTHONPATH, pidfile, log
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

The live loop has two parts. **Enoch's own daemon**
(`python -m enoch.agent`, started per agent root via
`scripts/run_enoch_daemon.sh`) owns the S direction end-to-end: its poll
loop calls `chat.muse.receive(cursor)` (~2s idle cadence, paced inside
the provider), dispatches each new `chat_inbox` message through the full
`handle_event()` path — receipts, daemon epoch checks, effect-fence
authorization, real `run_conversation` with journal — and issues
`runtime.muse` reasoning requests as `inbox/<request_id>.json`. The
daemon's chat cursor is managed by Enoch itself
(`.enoch/channels/muse/cursor.json`).

A scheduled job (cron id `muse-enoch-mailbox-consumer`, every 1 minute)
covers the rest:

**Supervision:** checks `mailbox/enoch-daemon.pid`; restarts the daemon
via `run_enoch_daemon.sh` if it died. (Daemon epoch is last-writer-wins,
so a duplicate start safely retires the older process.)

**R direction (reasoner):** scans `mailbox/inbox/` for requests with no
`outbox/<request_id>.json` reply, reasons over each prompt as Muse, and
atomic-writes the reply (`{"request_id", "text", "replied_at"}`, tmp +
rename, 0600). Note: the daemon namespaces request ids
(e.g. `conversation:<uuid>`) — the outbox filename must match the inbox
filename exactly, prefix included. Empty inbox: the job does nothing and
stays silent.

**Delivery:** `@enoch` messages from Muse chat are appended by the chat
operator to `mailbox/chat_inbox/<seq>.json` (never answered by the
operator itself — the anti-roleplay guarantee). The job delivers
`mailbox/chat_outbox/` replies back into Muse chat verbatim (marked
with `<id>.delivered`).

The consumer interval dominates round-trip latency: one chat message can
trigger up to 7 sequential provider calls, so a 1-minute consumer cadence
keeps a full turn comfortably inside the provider's 30-minute
self-imposed deadline.

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

## Known limits

- **Latency multiplication**: one chat message can trigger up to 7
  sequential provider calls (`MAX_ACTIONS = 6`); each is a full mailbox
  round-trip (mitigated by the 1-minute consumer cadence).
- **Poll-loop hold**: conversational turns run on the daemon's poll-loop
  thread and each `runtime.muse` call waits on the mailbox for minutes,
  so a long turn (up to 7 sequential calls) holds the poll loop for tens
  of minutes, starving other events, scheduled jobs, and lifecycle work
  meanwhile. (Blocking per se is normal — every LLM call blocks; the
  issue is the duration of the hold.) Task turns are thread-isolated and
  safe.
- **Real side effects**: model-issued `[ENOCH_ACTION]` blocks are now
  executed for real under `DaemonEffectFence`, and
  `[ENOCH_MEMORY_REQUEST]` persists to Enoch's real memory. The fence is
  Enoch's own authorization mechanism; review its capability grants
  before exposing the instance to untrusted input.
- The daemon is supervised by the cron pidfile check; a dead daemon is
  restarted within ~1 minute, but there is no systemd/launchd unit yet.

## What's next

- Per-`session_key` Muse-side continuity.
- Daemon threading for conversational turns (stop holding the poll loop
  for tens of minutes).
- Cross-host mailbox (beyond one VM).

## Pushing

Pushes go through the `github` workspace skill (vault-backed, no pasted
token), which mirrors local commits via the git-database API with
identical SHAs:

    ~/workspace/skills/github/bin/github-push --repo . --branch main
