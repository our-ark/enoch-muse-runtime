# Development

[Back to the user guide](../README.md) · [Operations](operations.md) · [Architecture](architecture.md)

Run the commands below from this repository root.

## Offline checks

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

For live instances, follow [operations](operations.md) and configure the
external Muse consumer. The consumer stub only documents the transport.

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
[`scripts/muse_instance.py`](../scripts/muse_instance.py). It uses Enoch's public
registry API, verifies both providers and records per-attempt process evidence.
No copied egg-info or changes to the body are needed. See
[`docs/operations.md`](operations.md) for setup, migration phases and recovery.

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

## Running the tests

See [the test commands](operations.md#tests). Tests use stdlib `unittest`,
a caller-selected Enoch checkout and isolated temporary agent roots. Process
tests exercise real host APIs with deterministic mailbox responses.
