# MuseEnoch

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
  __init__.py   factory + OUR_ARK_PROVIDERS descriptor (route B)
  core.py       MuseRuntime: AgentRuntime contract over the mailbox
scripts/
  mailbox_consumer_stub.py   documents the external-side protocol (stub only)
tests/
  test_roundtrip.py          round-trip / pre-cancel / timeout tests
```

## Registration

**Route A — entry point (active once installed):**
`pyproject.toml` declares
`[project.entry-points."our_ark.providers"] "runtime.muse" =
"our_ark_muse:create_provider"`, discovered via `importlib.metadata`.

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
- [ ] **Latency multiplication**: one chat message can trigger up to 7
      sequential provider calls (`MAX_ACTIONS = 6`); each is a full
      mailbox round-trip.
- [ ] Conversational turns run synchronously and **block the daemon's
      poll loop** while waiting; task turns are thread-isolated and safe.
- [ ] The mailbox replaces only the **runtime** provider. A separate
      **chat** provider is still needed if the surface `S` should also be
      Muse chat (the `@enoch` idea) — the two axes are replaced
      independently.
- [ ] No live consumer yet: `scripts/mailbox_consumer_stub.py` documents
      the protocol; the scheduled pickup loop that hands prompts to the
      Muse operator is the next step (not built here).

## What's next

1. Build the live consumer: a scheduled job that scans `inbox/`, keeps
   one Muse-side thread per `session_key`, and atomic-writes replies to
   `outbox/`.
2. Point an Enoch checkout at the provider
   (`ENOCH_RUNTIME_PROVIDER=muse`) and run one real `respond()` turn
   end to end.
3. Optionally, implement the companion **chat** provider for the
   Muse-chat surface.
