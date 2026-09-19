#!/usr/bin/env bash
# Configure once with muse_instance.py configure before starting.
# Per-attempt stdout/stderr and observed exits: .enoch/artifacts/muse-runs.
#
# Starts the daemon detached (--detach): the supervisor runs in a new OS
# session, so it survives the launcher session going away (a plain background
# launch kept the daemon in the launcher's process group, and any teardown of
# that group SIGTERMed the daemon with it). The launcher prints the attempt
# JSON and exits once the supervisor reports running; duplicate starts are
# rejected by the instance lock inside muse_instance.py.
set -euo pipefail

AGENT_ROOT="${ENOCH_AGENT_ROOT:-$HOME/workspace/muse-enoch-agent}"
ENOCH_SRC_DIR="${ENOCH_SRC:-$HOME/workspace/enoch-experiment}"
REPO_ROOT="${ENOCH_MUSE_REPO:-$(cd -- "$(dirname -- "$0")/.." && pwd)}"
PYTHON="${ENOCH_PYTHON:-python3}"

args=(--root "$AGENT_ROOT" --enoch-src "$ENOCH_SRC_DIR" --detach)
if [[ -n "${ENOCH_MUSE_MAILBOX:-}" ]]; then
    args+=(--mailbox "$ENOCH_MUSE_MAILBOX")
fi
export ENOCH_MUSE_POLL_SECONDS="${ENOCH_MUSE_POLL_SECONDS:-5}"
export ENOCH_MUSE_TIMEOUT="${ENOCH_MUSE_TIMEOUT:-1800}"
exec "$PYTHON" "$REPO_ROOT/scripts/muse_instance.py" "${args[@]}" daemon
