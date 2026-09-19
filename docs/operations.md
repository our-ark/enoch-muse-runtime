# Running isolated Muse instances

Use Python 3.11+ and an Enoch checkout compatible with the provider-kit contract.
Keep one agent root and one mailbox per instance. These commands register the
factories from this adapter checkout through Enoch's public registry API; they
do not install packages, copy egg-info, or edit the body/genesis.toml.
For other Enoch entry points, install this package normally into their Python
environment and verify both `load_provider("runtime", name="muse")` and
`load_provider("chat", name="muse")`.

## Configure and check

```bash
python3 scripts/muse_instance.py --root /path/to/agent --enoch-src /path/to/enoch \
  --mailbox /path/to/mailbox configure
python3 scripts/muse_instance.py --root /path/to/agent --enoch-src /path/to/enoch check
```

Configuration uses Enoch's config API to persist `providers.runtime=muse`,
`providers.chat=muse`, and `muse.mailbox` in `.enoch/config.yaml`. A separate
export process can therefore report the real bindings even without the
launcher's environment. Conflicting environment overrides fail explicitly.
Config/credentials are excluded from migration bundles: configure the receiving
root separately before activation. Configuring a fenced or live root is refused.

The launcher checks actual registry resolution. A mailbox ownership marker
prevents accidental use by two configured roots; it is not a distributed lease.

## Start and inspect

```bash
python3 scripts/muse_instance.py --root /path/to/agent --enoch-src /path/to/enoch \
  --detach daemon
```

The command returns an `attempt` directory under
`.enoch/artifacts/muse-runs/`. Each invocation has unique stdout, stderr and
`status.json` files. The status records UTC timestamps, child/supervisor PIDs,
effective bindings, code revisions, source hashes, and the observed return code
or terminating signal. Python child output is unbuffered, and research driver
scripts also have their hash recorded. A completed status means the child exited zero;
application-level checks are still required. Logs are hashed after the child exits. Evidence can
contain prompts and responses; publish only isolated synthetic experiment data.

```bash
python3 scripts/muse_instance.py --root /path/to/agent --enoch-src /path/to/enoch \
  status /path/to/attempt
```

`run_enoch_daemon.sh` remains a foreground compatibility entry point; it now uses
the same supervisor. `enoch-daemon.pid` identifies the supervisor, and
`enoch-daemon-run.json` points to its evidence directory. SIGTERM to the
supervisor is forwarded to the child's process group and its exit is recorded.
The consumer must still answer requests and deliver chat messages.

A nonblocking instance lock rejects duplicate managed commands before another
Enoch epoch is created. The child inherits the lock, so losing the supervisor
does not allow a second worker to take over a still-running child. Detaching
uses a new OS session and closed input; it cannot guarantee survival of host or
container termination. If the supervisor disappears without an exit record,
status is unknown, never assumed successful. PID reuse may conservatively block
status/recovery; PIDs alone are not continuation authority. All cooperating
daemon/worker commands must use this launcher; native Enoch fences still apply.

## Run a research phase and recover a stopped worker

```bash
python3 scripts/muse_instance.py --root /path/to/agent --enoch-src /path/to/enoch \
  --detach run /path/to/phase.py --phase-specific-argument value
```

The child executes the Python script with source registration and the persistent
instance bindings. Only one command owns the instance lock, regardless of phase.
No automatic retries occur. If a worker exits with a task still running:

1. Retain its attempt directory. Inspect the captured exit, queue and checkpoint.
2. Use `recover <task-id>` through the launcher. It refuses a live daemon,
   live/unknown worker PID, changed task ownership or an exported source fence.
3. Recovery calls Enoch's `pause_task` API, keeps the checkpoint and records
   before/after task snapshots in `recovery.json`. It does not edit queue JSON,
   change epoch, or resume a task automatically.
4. Start the next phase with a new output directory. Completed attempts are never
   overwritten. A supervisor that was itself killed cannot attest the child exit.

## RIPA pilot v2

`scripts/ripa_pilot.py` is the revised tool-free research driver from the first
round-trip pilot. It uses the real migration/workflow/runtime APIs. Each phase
is a separate process with a new empty `--out` directory. The source chooses a
fresh synthetic identity ID (or accepts `--run-id`); later phases read it from
the installed/imported identity. The body is frozen at the SHA in the script.
Keep the first pilot's evidence unchanged; record v2 as a new development run.

On the source, run `source` then `outbound-export` with `--root` and distinct
`--out` directories. On Muse, run `configure`, then invoke `import` through the
launcher using `--archive`, and run the daemon conversation probe. Stop the
daemon before `muse-worker`. After that worker exits, run `return-export` through
the same launcher. For example:

```bash
python3 scripts/muse_instance.py --root /path/to/agent --enoch-src /path/to/enoch \
  --detach run "$PWD/scripts/ripa_pilot.py" muse-worker \
  --root /path/to/agent --out /path/to/evidence/worker-attempt-1
```

If the task is already running/completed, the driver refuses before advancing
the epoch. The supervisor captures that failure. The consumer must answer the
actual request with its captured attempt nonce. The return host imports and
verifies the bundle and runs `returned` with the real Codex runtime.

The separate daemon probe verifies conversations; explicit workflow driving
does not demonstrate automatic migration of arbitrary tasks/worktrees. Protocol
tests use deterministic mailbox replies and are not live-model results.

## Tests

```bash
ENOCH_SRC=/path/to/enoch \
PYTHONPATH=/path/to/enoch/libraries/provider-kit/src \
python3 -m unittest discover -s tests -v
```

Process tests cover fresh-source registration without site metadata, bindings in
a separate native export, duplicate starts, SIGKILL of a child, recovery with the
same task ID, lost supervisors, signal forwarding, retained failure logs, and a
real daemon conversation with a deterministic mailbox consumer. They do not
reproduce or establish the unknown cause of the first live worker disappearance.
