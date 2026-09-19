# enoch-muse-runtime

**Run a persistent [Enoch](https://github.com/our-ark/enoch) agent inside Muse,
and talk to it with `@Enoch`.** Enoch keeps its own installed identity, memory
and executable body; Muse supplies the reasoning and chat environment.

> **Based on the RIPA paper:**
> [*Runtime-Independent Persistent Agents: Preserving Identity, Memory, and Code Across Models, Harnesses, and Servers*](https://arxiv.org/abs/2609.00546).
>
> RIPA separates the persistent agent from its replaceable runtime and
> interaction bindings. This repository implements the Muse binding and
> includes evidence from supervised Codex–Muse–Codex migration studies.

**[Install in Muse](#how-to-install-in-muse)** ·
[Talk to Enoch](#using-enoch-in-muse) ·
[RIPA architecture](#ripa-framing-paper) ·
[Research artifacts](#research-artifacts) ·
[Developer checks](#quick-start-offline-checks)

Licensed under [Apache-2.0](LICENSE). This repository provides the adapter and
its synthetic research artifacts; Muse itself remains an external service.
The live studies use a supervised Muse mailbox consumer, not an unattended API.

## How to install in Muse

Deployment runs **inside Muse's cloud workspace**. Your computer is the chat
client; it does not need to host Enoch or run these commands locally.

**Prerequisites:** Muse must be able to access the GitHub repositories, run Git
and Python 3.11+ on a POSIX host, and maintain a scheduled mailbox consumer or
equivalent loop. This repository supplies the adapter and deployment procedure;
Muse access and the consumer's live reasoning service are external requirements.

### 1. Paste this into Muse

```text
Install https://github.com/our-ark/enoch-muse-runtime in your cloud workspace
and deploy a dedicated Enoch instance there.

Read and follow the deployment guide:
https://github.com/our-ark/enoch-muse-runtime/blob/main/prompts/deploy-enoch.md

Use the compatible Enoch body from https://github.com/our-ark/enoch at revision
66781e209962bcce6d5254e50d05f000ac914668.

Instance name: Enoch
Mission: Be my persistent assistant, retaining useful memories and unfinished
work across conversations.
Seed memory: I prefer replies in Chinese.

Create a dedicated agent root and mailbox. If an instance already exists,
inspect and report it before creating another; do not overwrite its state.
Configure both the Muse runtime and chat providers, start Enoch's native
daemon, and connect one mailbox consumer for this instance.

Route my @Enoch messages to that daemon and forward its replies verbatim.
Before reporting success, complete a real end-to-end chat turn. Show me the
instance name, agent root, mailbox, provider check, and Enoch's actual reply.
If this Muse environment lacks a required capability, report what is missing.
```

Change the name, mission and seed memory to suit your instance. The
[deployment guide](prompts/deploy-enoch.md) specifies the complete procedure;
the [operations guide](docs/operations.md) provides the underlying commands.

### 2. Verify the deployment

Muse should report a dedicated root and mailbox, successful resolution of both
`runtime.muse` and `chat.muse`, a running native Enoch daemon, and a real reply
in `chat_outbox` from its smoke-test message. A cloned repository or a response
written by the Muse operator is not a completed deployment. Keep the mailbox
consumer serving requests after setup; otherwise Enoch will wait for replies.

### 3. Talk to your agent

Send these messages in Muse chat after setup:

```text
@Enoch 你是谁？你现在运行在哪里？
@Enoch 请记住：我们把这个项目叫作「青舟」。
@Enoch 我们给这个项目起了什么名字？
@Enoch /status
```

The first message asks the installed agent to describe itself. The next two
are a simple memory interaction, and `/status` exercises native command
routing. Inspect Enoch's stored memory through its memory API when checking
persistence; an immediate recall answer alone can come from conversation
context. With another instance name, use its configured `@<name>` route.

## Using Enoch in Muse

**Chat:** send `@<name> <text>` in Muse chat. The operator appends your
literal text to the instance's `chat_inbox` and delivers its
`chat_outbox` reply verbatim. The operator must not answer as the instance;
this is an operating rule, not independently enforced host attestation.

**Slash commands** (`/help`, `/status`, `/do`, …) are executed through
Enoch's real registered-command table, the same dispatch the daemon
uses. Unknown `/commands` fall through to normal conversation.

## Quick start: offline checks

Requirements: Python 3.11+, Git, and a POSIX host for managed process tests.
Clone this repository and Enoch as sibling directories. The documented
compatibility revision is Enoch `66781e209962bcce6d5254e50d05f000ac914668`.

```bash
git clone https://github.com/our-ark/enoch.git ../enoch
git -C ../enoch checkout 66781e209962bcce6d5254e50d05f000ac914668
ENOCH_SRC="$PWD/../enoch" \
PYTHONPATH="$PWD/../enoch/libraries/provider-kit/src" \
python3 -m unittest discover -s tests -v
```

Use a fresh sibling checkout for these commands. The 23 tests use deterministic
mailbox replies and require no model credentials. A missing Enoch checkout
skips integration tests, so verify the full test count and absence of skips.
For an isolated package installation, install `../enoch/libraries/provider-kit`
and this project into the same virtual environment; provider-kit is consumed
from source, not assumed to be available from a package index.

For live instances, follow [operations](docs/operations.md) and configure the
external Muse consumer. The consumer stub only documents the transport.

## Research artifacts

[Artifact guide](docs/research-artifacts.md) links the pinned protocol, raw
synthetic records, migration bundles, recovery evidence and verifiers. The
measured study contains one qualification, five round trips, five controls and
one planned worker interruption. The recovered development pilot is separate.

```bash
git fetch origin exp/ripa-study-20260919
python3 scripts/verify_study_archive.py
```

This checks archived integrity and state consistency without model calls.
Live reproduction additionally requires Codex and Muse access and operator
coordination; the observations do not establish unattended reliability.

## RIPA framing ([paper](https://arxiv.org/abs/2609.00546))

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
[artifact guide](docs/research-artifacts.md) for the tested bindings and
evidence boundaries.

## Deploying an Enoch instance inside Muse

Give a suitably configured Muse operator an **instance prompt** — the agent's name,
who it is, its mission, and any seed memories — and point it at
[`prompts/deploy-enoch.md`](prompts/deploy-enoch.md). Muse acts as the
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

## Repo layout

```
src/our_ark_muse/
  __init__.py   factories + OUR_ARK_PROVIDERS descriptor (route B)
  core.py       MuseRuntime: AgentRuntime contract over the mailbox (R axis)
  chat.py       MuseChatClient: ChatProvider contract over the mailbox (S axis)
scripts/
  mailbox_consumer_stub.py   documents the external-side protocol (stub only)
  mailbox_pending.py         lists inbox requests with no outbox reply yet
  mailbox_reply.py           writes a protocol-correct reply for one request
                             (echoes the attempt nonce; atomic, 0600)
  e2e_live_respond.py        live end-to-end: loads runtime.muse via Enoch's
                             registry and runs one blocking respond() turn
  chat_turn.py               legacy one-shot turn driver (retired from the
                             live loop; the daemon now owns S). Kept for
                             manual debugging.
  run_enoch_daemon.sh        starts Enoch's own daemon
                             through the managed source launcher
  muse_instance.py           source registration, persistent bindings,
                             instance lock, detached execution, exit evidence
  ripa_pilot.py              revised synthetic migration/workflow driver
tests/
  test_roundtrip.py          round-trip / pre-cancel / timeout tests
  test_chat_roundtrip.py     chat provider receive/send/cursor tests
.gitignore                   excludes mailbox/ (live traffic, never committed)
```

## Registration

**Managed source launcher:** configure and run through
[`scripts/muse_instance.py`](scripts/muse_instance.py). It uses Enoch's public
registry API, verifies both providers and records per-attempt process evidence.
No copied egg-info or changes to the body are needed. See
[`docs/operations.md`](docs/operations.md) for setup, migration phases and recovery.

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

For installed entry points, select with `/config provider runtime muse` and
`/config provider chat muse`. Environment-only selections do not survive into
a later export process. The managed launcher persists and checks both bindings.
Do **not** mark the plugin `default=True`.

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `ENOCH_MUSE_MAILBOX` | `<cwd>/.enoch/muse_mailbox` | mailbox base dir (`inbox/`, `outbox/`; 0700, files 0600) |
| `ENOCH_MUSE_POLL_SECONDS` | `10` | outbox poll interval |
| `ENOCH_MUSE_TIMEOUT` | `1800` | self-imposed deadline when the harness passes no `timeout_seconds` (conversation turns) |

Task turns should set Enoch's `[task] timeout_seconds` toward its 7200s
ceiling for mailbox operation.

## Running the tests

See [the test commands](docs/operations.md#tests). Tests use stdlib `unittest`,
a caller-selected Enoch checkout and isolated temporary agent roots. Process
tests exercise real host APIs with deterministic mailbox responses.

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
via `run_enoch_daemon.sh` if it died. Configure persistent bindings first.
The instance lock rejects duplicate managed launches; each attempt retains its
own logs and observed exit status. An unobserved process exit remains unknown.

**R direction (reasoner):** runs `scripts/mailbox_pending.py` to find
requests with no valid `outbox/<request_id>.json` reply (a reply is valid
only if it echoes the inbox request's live `attempt` nonce), reasons over
each prompt as Muse, and atomic-writes the reply (`{"request_id",
"attempt", "text", "replied_at"}`, tmp + rename, 0600). The reply
**must echo the `attempt` nonce** captured **when the request was read** (easiest via
`scripts/mailbox_reply.py <request_id> --attempt <nonce> --text "..."`,
where `<nonce>` is the attempt you captured **when you read the request**,
not the inbox's current value); the provider
rejects any reply whose attempt doesn't match the live one, so a reused
request_id can never pick up a stale reply. Note: the daemon namespaces
request ids (e.g. `conversation:<uuid>`) — the outbox filename must match
the inbox filename exactly, prefix included. Empty inbox: the job does
nothing and stays silent.

**Timeout lifecycle:** if a provider call times out or is stopped, the
provider moves its inbox request to `mailbox/dead-letter/` stamped with
`cancelled_at` / `cancel_reason`. The consumer never answers dead-letter
entries; a late reply for a dead attempt is inert (attempt mismatch).

**Reply checklist** (two rules, learned the hard way):

1. Capture the `attempt` when you **read** the request and carry it to
   submit time (`--attempt`); never substitute the inbox's current value —
   the request may have been superseded while you were reasoning.
2. A `dead-letter/` entry blocks only its own attempt; a retry of the
   same request id with a fresh attempt is legitimate and must be
   answered.

**Delivery:** `@enoch` messages from Muse chat are appended by the chat
operator to `mailbox/chat_inbox/<seq>.json` for the native daemon to handle.
The operator must not invent an instance reply. The job delivers
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

## License and contributions

See [LICENSE](LICENSE), [CONTRIBUTING.md](CONTRIBUTING.md) and
[CITATION.cff](CITATION.cff). Use synthetic fixtures in reports; do not publish
production instance state or live mailbox traffic. Historical study files
remain immutable, including their recorded failures and limitations.
