#!/usr/bin/env bash
# Configure once with muse_instance.py configure before starting.
# Per-attempt stdout/stderr and observed exits: .enoch/artifacts/muse-runs.
set -euo pipefail

AGENT_ROOT="${ENOCH_AGENT_ROOT:-$HOME/workspace/muse-enoch-agent}"
ENOCH_SRC_DIR="${ENOCH_SRC:-$HOME/workspace/enoch-experiment}"
REPO_ROOT="${ENOCH_MUSE_REPO:-$(cd -- "$(dirname -- "$0")/.." && pwd)}"
PYTHON="${ENOCH_PYTHON:-python3}"

args=(--root "$AGENT_ROOT" --enoch-src "$ENOCH_SRC_DIR")
if [[ -n "${ENOCH_MUSE_MAILBOX:-}" ]]; then
    args+=(--mailbox "$ENOCH_MUSE_MAILBOX")
fi
export ENOCH_MUSE_POLL_SECONDS="${ENOCH_MUSE_POLL_SECONDS:-5}"
export ENOCH_MUSE_TIMEOUT="${ENOCH_MUSE_TIMEOUT:-1800}"
exec "$PYTHON" "$REPO_ROOT/scripts/muse_instance.py" "${args[@]}" daemon
